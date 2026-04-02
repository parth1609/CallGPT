"""
Purpose: Business logic for Vector Store Service using Pinecone.
"""

import os
import time
from typing import List, Optional, Dict, Any
import numpy as np
from pinecone import Pinecone, ServerlessSpec
from uuid import uuid4
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from supabase import Client, create_client


load_dotenv()


class VectorStoreService:
    """Manages vector database operations with Pinecone"""

    def __init__(
        self,
        pinecone_api_key: Optional[str] = None,
        embeddings: Optional[Embeddings] = None,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
    ):
        """Initialize Vector Store Service with Pinecone and Supabase connection"""
        # Pinecone Init
        self.pinecone_api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        if self.pinecone_api_key:
            self.pc: Pinecone = Pinecone(api_key=self.pinecone_api_key)
            self.cloud = os.getenv("PINECONE_CLOUD", "aws")
            self.region = os.getenv("PINECONE_REGION", "us-east-1")

        # Supabase Init
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = (
            supabase_key
            or os.getenv("SUPABASE_API_KEY")
            or os.getenv("SUPABASE_SERVICE_KEY")
            or os.getenv("SUPABASE_KEY")
        )

        if self.supabase_url and self.supabase_key:
            self.supabase_client: Client = create_client(
                self.supabase_url, self.supabase_key
            )

        self.embeddings = embeddings
        # SUPABASE BUCKET = INDEX NAME (Organisation name)
        self.default_index = os.getenv("SUPABASE_BUCKET")
        self.table_name = "documents"  # Default table name for Supabase
        self.query_name = "match_documents"  # Default query function for Supabase

        print(f"DEBUG: VectorStoreService init. Index: {self.default_index}")

    def _ensure_index(
        self,
        index_name: str,
        dimension: int,
        metric: str = "cosine",
    ) -> None:
        """Create Pinecone serverless index if it does not exist, and validate dimension if it does."""
        try:
            names = {idx.name for idx in self.pc.list_indexes()}
        except Exception:
            names = set()
        if index_name not in names:
            self.pc.create_index(
                name=index_name,
                dimension=dimension,
                metric=metric,
                spec=ServerlessSpec(cloud=self.cloud, region=self.region),
            )
            for _ in range(60):
                try:
                    idx = self.pc.Index(index_name)
                    _ = idx.describe_index_stats()
                    break
                except Exception:
                    time.sleep(1)
        else:
            # Validate existing dimension
            try:
                idx = self.pc.Index(index_name)
                stats = idx.describe_index_stats()
                existing_dim = stats.get("dimension")
                if existing_dim is not None and existing_dim != dimension:
                    raise ValueError(
                        f"Index '{index_name}' has dimension {existing_dim}, cannot upsert dimension {dimension}"
                    )
            except Exception:
                # If stats are unavailable, proceed without strict validation
                pass

    def upsert_vectors(
        self,
        chunks: List[str],
        embeddings: List[List[float]],
        index_name: str = None,
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Upsert text chunks with embeddings to Pinecone.

        Parameters:
        - chunks: List of text chunks
        - embeddings: Corresponding embedding vectors
        - index_name: Target index name
        - metadata: Optional metadata for each chunk

        Returns:
        - Dict with success status and inserted count
        """
        if chunks is None or embeddings is None:
            raise ValueError("Chunks and embeddings must be provided and non-null")

        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have same length")

        if not embeddings or not embeddings[0]:
            raise ValueError("Embeddings must be non-empty")

        index_name = index_name or self.default_index
        dimension = len(embeddings[0])
        self._ensure_index(index_name, dimension)

        vectors = []
        prefix = str(uuid4())
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            meta = metadata[i] if metadata and i < len(metadata) else {}
            # Store content in metadata for retrieval
            if "content" not in meta:
                meta = {**meta, "content": chunk}
            meta = self._sanitize_metadata(meta)
            vectors.append(
                {
                    "id": f"{prefix}-{i}",
                    "values": embedding,
                    "metadata": meta,
                }
            )

        try:
            idx = self.pc.Index(index_name)
            idx.upsert(vectors=vectors)
            return {
                "success": True,
                "inserted_count": len(vectors),
                "index_name": index_name,
            }
        except Exception as e:
            raise Exception(f"Upsert failed: {str(e)}")

    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure Pinecone-compatible metadata values."""
        sanitized: Dict[str, Any] = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, list) and all(
                isinstance(item, str) for item in value
            ):
                sanitized[key] = value
            else:
                sanitized[key] = str(value)
        return sanitized

    def create_index(
        self,
        index_name: str,
        dimension: int,
    ) -> Dict[str, Any]:
        """
        Create a Pinecone index with the specified dimension.

        Parameters:
        - index_name: Index name
        - dimension: Embedding dimension
        - query_function_name: Ignored (for API compatibility)

        Returns:
        - Dict with success status and index name
        """
        # Ensure Pinecone index exists with the requested dimension
        self._ensure_index(index_name or self.default_index, dimension)
        return {
            "success": True,
            "index_name": index_name or self.default_index,
            "message": "Index ensured (created if missing)",
        }

    def list_indexes(self) -> List[Dict[str, Any]]:
        """
        List all Pinecone indexes.

        Returns:
        - List of dicts with index name, row count, and dimension
        """
        try:
            tables = []
            for idx in self.pc.list_indexes():
                try:
                    index = self.pc.Index(idx.name)
                    stats = index.describe_index_stats()
                    tables.append(
                        {
                            "index_name": idx.name,
                            "row_count": int(stats.get("total_vector_count", 0) or 0),
                            "dimension": stats.get("dimension"),
                        }
                    )
                except Exception:
                    tables.append(
                        {
                            "index_name": idx.name,
                            "row_count": 0,
                            "dimension": None,
                        }
                    )
            return tables
        except Exception:
            return []

    def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """Get statistics for a specific Pinecone index"""
        try:
            index = self.pc.Index(index_name)
            stats = index.describe_index_stats()
            return {
                "index_name": index_name,
                "row_count": int(stats.get("total_vector_count", 0) or 0),
                "dimension": stats.get("dimension", None),
                "created_at": None,
            }
        except Exception as e:
            raise Exception(f"Failed to get table stats: {str(e)}")

    def delete_index(self, index_name: str) -> bool:
        """
        Delete a Pinecone index.

        Parameters:
        - index_name: Index name to delete

        Returns:
        - True if successful
        """
        try:
            self.pc.delete_index(index_name)
            return True
        except Exception as e:
            raise Exception(f"Failed to delete index: {str(e)}")

    # ============================================================================
    # Supabase Methods (Ported from CustomSupabaseVectorStore)
    # ============================================================================

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
        if not self.supabase_client or not self.embeddings:
            raise ValueError(
                "Supabase client and embeddings must be initialized for similarity search"
            )

        # Generate embedding for the query
        query_embedding = self.embeddings.embed_query(query)

        # Call Supabase RPC function
        response = self.supabase_client.rpc(
            self.query_name,
            {
                "query_embedding": query_embedding,
                "match_count": k,
            },
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
        if not self.supabase_client or not self.embeddings:
            raise ValueError(
                "Supabase client and embeddings must be initialized for MMR search"
            )

        # Generate embedding for the query
        query_embedding = self.embeddings.embed_query(query)

        # Fetch more candidates than needed
        response = self.supabase_client.rpc(
            self.query_name,
            {
                "query_embedding": query_embedding,
                "match_count": fetch_k,
            },
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
                candidate_embeddings.append(
                    self.embeddings.embed_query(doc.page_content)
                )

        # Apply MMR locally
        from langchain_community.vectorstores.utils import maximal_marginal_relevance

        # Convert to numpy arrays (MMR expects numpy arrays with .ndim attribute)
        query_embedding_np = np.array(query_embedding)
        candidate_embeddings_np = np.array(candidate_embeddings)

        if len(candidates) == 0:
            return []

        selected_indices = maximal_marginal_relevance(
            query_embedding_np,
            candidate_embeddings_np,
            lambda_mult=lambda_mult,
            k=k,
        )

        return [candidates[i] for i in selected_indices]

    def as_retriever(
        self, *, search_type: str = "similarity", search_kwargs: Dict[str, Any] = None
    ):
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

        # Capture self to use in inner class
        service_instance = self

        class CustomRetriever(BaseRetriever):
            search_type_: str
            search_kwargs_: Dict[str, Any]

            def _get_relevant_documents(
                self,
                query: str,
                *,
                run_manager: CallbackManagerForRetrieverRun = None,
            ) -> List[Document]:
                if self.search_type_ == "mmr":
                    return service_instance.max_marginal_relevance_search(
                        query, **self.search_kwargs_
                    )
                else:
                    return service_instance.similarity_search(
                        query, **self.search_kwargs_
                    )

        return CustomRetriever(
            search_type_=search_type,
            search_kwargs_=search_kwargs,
        )

    def upsert_documents(
        self,
        docs: List[Document],
        chunk_size: int = 500,
    ) -> str:
        """
        Upsert documents to Supabase.
        """
        if not self.supabase_client or not self.embeddings:
            raise ValueError("Supabase client and embeddings must be initialized")

        from uuid import uuid4

        # Generate embeddings
        texts = [doc.page_content for doc in docs]
        vectors = self.embeddings.embed_documents(texts)

        records = []
        for doc, vector in zip(docs, vectors):
            records.append(
                {
                    "id": str(uuid4()),
                    "content": doc.page_content,
                    "metadata": doc.metadata or {},
                    "embedding": vector,
                }
            )

        for i in range(0, len(records), chunk_size):
            batch = records[i : i + chunk_size]
            self.supabase_client.table(self.table_name).insert(batch).execute()

        return self.table_name


def build_supabase_from_documents(
    docs: List[Document],
    embeddings: Any,
    table_name: str = "documents",
    query_name: str = "match_documents",
) -> str:
    """
    Utility function to build a Supabase vector store from documents.
    """
    service = VectorStoreService(embeddings=embeddings)
    service.table_name = table_name
    service.query_name = query_name
    return service.upsert_documents(docs)

