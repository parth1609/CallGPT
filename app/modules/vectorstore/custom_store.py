"""
Custom Supabase vector store wrapper that bypasses broken SupabaseVectorStore methods.

Purpose: Directly call Supabase RPC functions for vector similarity search,
avoiding the langchain-community bug with SyncRPCFilterRequestBuilder.params.
"""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from supabase import Client


class CustomSupabaseVectorStore:
    """
    Purpose: Minimal wrapper for Supabase vector search using direct RPC calls.
    
    Side Effects:
    - Calls Supabase RPC functions via client.rpc()
    """
    
    def __init__(
        self,
        client: Client,
        embeddings: Embeddings,
        table_name: str = "documents",
        query_name: str = "match_documents",
    ):
        self.client = client
        self.embeddings = embeddings
        self.table_name = table_name
        self.query_name = query_name
    
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        **kwargs: Any,
    ) -> List[Document]:
        """
        Purpose: Perform similarity search using Supabase RPC.
        
        Parameters:
        - query (str): Search query text.
        - k (int): Number of results to return.
        
        Return Value:
        - List[Document]: Matching documents.
        """
        # Generate embedding for the query
        query_embedding = self.embeddings.embed_query(query)
        
        # Call Supabase RPC function
        response = self.client.rpc(
            self.query_name,
            {
                "query_embedding": query_embedding,
                "match_count": k,
            }
        ).execute()
        
        # Convert results to LangChain Documents
        documents = []
        for row in response.data:
            doc = Document(
                page_content=row.get("content", ""),
                metadata=row.get("metadata", {}),
            )
            documents.append(doc)
        
        return documents
    
    def max_marginal_relevance_search(
        self,
        query: str,
        k: int = 4,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
        **kwargs: Any,
    ) -> List[Document]:
        """
        Purpose: Perform MMR search (fetch more, then diversify).
        
        Parameters:
        - query (str): Search query text.
        - k (int): Final number of results.
        - fetch_k (int): Initial candidates to fetch.
        - lambda_mult (float): Diversity factor [0,1].
        
        Return Value:
        - List[Document]: Diversified documents.
        
        Side Effects:
        - Fetches fetch_k candidates, applies MMR locally.
        """
        # Generate embedding for the query
        query_embedding = self.embeddings.embed_query(query)
        
        # Fetch more candidates than needed
        response = self.client.rpc(
            self.query_name,
            {
                "query_embedding": query_embedding,
                "match_count": fetch_k,
            }
        ).execute()
        
        # Convert to Documents
        candidates = []
        candidate_embeddings = []
        
        for row in response.data:
            doc = Document(
                page_content=row.get("content", ""),
                metadata=row.get("metadata", {}),
            )
            candidates.append(doc)
            # If embeddings are returned, use them; otherwise re-embed
            if "embedding" in row:
                candidate_embeddings.append(row["embedding"])
            else:
                candidate_embeddings.append(self.embeddings.embed_query(doc.page_content))
        
        # Apply MMR locally
        from langchain_community.vectorstores.utils import maximal_marginal_relevance
        
        # Convert to numpy arrays (MMR expects numpy arrays with .ndim attribute)
        query_embedding_np = np.array(query_embedding)
        candidate_embeddings_np = np.array(candidate_embeddings)
        
        selected_indices = maximal_marginal_relevance(
            query_embedding_np,
            candidate_embeddings_np,
            lambda_mult=lambda_mult,
            k=k,
        )
        
        return [candidates[i] for i in selected_indices]
    
    def as_retriever(self, *, search_type: str = "similarity", search_kwargs: Dict[str, Any] = None):
        """
        Purpose: Create a LangChain retriever interface.
        
        Parameters:
        - search_type (str): 'similarity' or 'mmr'.
        - search_kwargs (Dict): Additional search parameters (k, fetch_k, lambda_mult).
        
        Return Value:
        - CustomRetriever: Object with invoke() method.
        """
        from langchain_core.retrievers import BaseRetriever
        from langchain_core.callbacks import CallbackManagerForRetrieverRun
        
        search_kwargs = search_kwargs or {}
        
        class CustomRetriever(BaseRetriever):
            vectorstore: CustomSupabaseVectorStore
            search_type_: str
            search_kwargs_: Dict[str, Any]
            
            def _get_relevant_documents(
                self,
                query: str,
                *,
                run_manager: CallbackManagerForRetrieverRun = None,
            ) -> List[Document]:
                if self.search_type_ == "mmr":
                    return self.vectorstore.max_marginal_relevance_search(query, **self.search_kwargs_)
                else:
                    return self.vectorstore.similarity_search(query, **self.search_kwargs_)
        
        return CustomRetriever(
            vectorstore=self,
            search_type_=search_type,
            search_kwargs_=search_kwargs,
        )
