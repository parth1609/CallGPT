"""
Purpose: Business logic for Retrieval Module.
Handles semantic search and document retrieval using Pinecone with LangChain.
Supports two-stage retrieval with Pinecone reranking.
"""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pinecone import Pinecone

from app.modules.embedding.service import EmbeddingService

# LangChain and Pinecone integrations for reranking
try:
    from langchain_pinecone import PineconeVectorStore
    from langchain_community.retrievers import PineconeRerank
    from langchain_core.documents import Document as LangChainDocument
    RERANKING_AVAILABLE = True
except ImportError:
    RERANKING_AVAILABLE = False
    print("Warning: PineconeRerank not available. Install with: pip install langchain-pinecone")

load_dotenv()


class RetrievalService:
    """Manages semantic search and retrieval operations using Pinecone with LangChain"""
    
    def __init__(
        self,
        pinecone_api_key: Optional[str] = None,
        index_name: Optional[str] = None,
    ):
        """Initialize Retrieval Service"""
        # Initialize Embedding Service directly
        self.embedding_service = EmbeddingService()
        
        # Initialize Pinecone
        self.pinecone_api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY must be provided")
        
        self.index_name = index_name or os.getenv("SUPABASE_BUCKET")
        if not self.index_name:
            raise ValueError("SUPABASE_BUCKET environment variable must be set")
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        
        # Initialize Pinecone index (will be used with LangChain)
        print(f"DEBUG: RetrievalService init. Index: {self.index_name}, API Key: {self.pinecone_api_key[:4]}...")
        self.index = self.pc.Index(self.index_name)
    
    def _get_query_embedding(
        self,
        query: str,
        model_name: Optional[str] = None,
    ) -> List[float]:
        """Get embedding for query text"""
        # Direct call to embedding service
        embeddings, _, _ = self.embedding_service.generate_embeddings(
            texts=[query],
            model_name=model_name
        )
        return embeddings[0]
    
    def rerank_search(
        self,
        query: str,
        fetch_k: int = 20,
        top_n: int = 4,
        reranker_model: str = "bge-reranker-v2-m3",
        embedding_model: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Two-stage retrieval with Pinecone reranking.
        
        Stage 1: Retrieve fetch_k candidates using similarity search
        Stage 2: Rerank candidates and return top_n results
        
        Parameters:
        - query: Search query text
        - fetch_k: Initial number of candidates to retrieve (default: 20)
        - top_n: Final number of reranked results (default: 4)
        - reranker_model: Pinecone reranker model (default: bge-reranker-v2-m3)
        - embedding_model: Model for query embedding
        
        Returns:
        - List of top_n reranked results with relevance scores
        
        Raises:
        - ImportError: If langchain-pinecone is not installed
        """
        if not RERANKING_AVAILABLE:
            raise ImportError(
                "Pinecone reranking requires langchain-pinecone. "
                "Install with: pip install langchain-pinecone"
            )
        
        # Stage 1: Initial retrieval with fetch_k candidates
        print(f"🔍 Stage 1: Retrieving {fetch_k} candidates...")
        initial_results = self.similarity_search(
            query=query,
            k=fetch_k,
            threshold=0.0,  # Get all candidates
            embedding_model=embedding_model,
        )
        
        if not initial_results:
            return []
        
        # Convert to LangChain Document format for reranker
        from langchain_core.documents import Document as LangChainDocument
        
        langchain_docs = [
            LangChainDocument(
                page_content=result.get('content', ''),
                metadata={
                    **result.get('metadata', {}),
                    'similarity': result.get('similarity', 0.0),
                    'id': result.get('id', '')
                }
            )
            for result in initial_results
        ]
        
        # Stage 2: Rerank using Pinecone Rerank
        print(f"🎯 Stage 2: Reranking to top {top_n} results with {reranker_model}...")
        try:
            reranker = PineconeRerank(
                model=reranker_model,
                top_n=top_n,
                pinecone_api_key=self.pinecone_api_key
            )
            
            reranked_docs = reranker.compress_documents(langchain_docs, query)
            
            # Convert back to our standard format
            reranked_results = []
            for doc in reranked_docs:
                reranked_results.append({
                    'content': doc.page_content,
                    'metadata': {k: v for k, v in doc.metadata.items() if k not in ['relevance_score', 'similarity', 'id']},
                    'relevance_score': doc.metadata.get('relevance_score', 0.0),
                    'similarity': doc.metadata.get('similarity', 0.0),
                    'id': doc.metadata.get('id', ''),
                })
            
            print(f"✅ Reranking complete: {len(reranked_results)} results")
            return reranked_results
            
        except Exception as e:
            print(f"⚠️ Reranking failed: {str(e)}. Falling back to top {top_n} from initial results.")
            return initial_results[:top_n]
    
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        threshold: float = 0.5,
        embedding_model: Optional[str] = None,
        use_reranker: bool = False,
        fetch_k: int = 20,
        reranker_model: str = "bge-reranker-v2-m3",
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search using Pinecone with LangChain.
        
        Parameters:
        - query: Search query text
        - k: Number of results (or top_n if using reranker)
        - threshold: Similarity threshold (score filter)
        - embedding_model: Model for query embedding
        - use_reranker: Enable two-stage retrieval with reranking
        - fetch_k: Initial candidates to retrieve (only if use_reranker=True)
        - reranker_model: Pinecone reranker model name
        
        Returns:
        - List of search results with content, similarity, and metadata
        
        Example:
        >>> # Standard similarity search
        >>> results = retrieval_service.similarity_search(query="Apple", k=4)
        >>> 
        >>> # With reranking (two-stage retrieval)
        >>> results = retrieval_service.similarity_search(
        ...     query="Apple",
        ...     k=3,
        ...     use_reranker=True,
        ...     fetch_k=20
        ... )
        """
        # Use reranking if requested
        if use_reranker:
            return self.rerank_search(
                query=query,
                fetch_k=fetch_k,
                top_n=k,
                reranker_model=reranker_model,
                embedding_model=embedding_model,
            )
        
        # Standard similarity search (existing implementation)
        # Get query embedding from embedding service
        query_embedding = self._get_query_embedding(query, embedding_model)
        
        # Perform similarity search using Pinecone
        # Use query_by_vector for direct embedding search
        try:
            results = self.index.query(
                vector=query_embedding,
                top_k=k,
                include_metadata=True,
                include_values=False,
            )
            
            # Format results to match expected structure
            formatted_results = []
            for match in results.matches:
                # Filter by threshold if provided
                if match.score and match.score >= threshold:
                    metadata = match.metadata or {}
                    # Extract content from metadata or use page_content if available
                    content = metadata.get("content", "")
                    
                    formatted_results.append({
                        "content": content,
                        "similarity": float(match.score) if match.score else 0.0,
                        "metadata": metadata,
                        "id": match.id,
                    })
            
            return formatted_results
        except Exception as e:
            raise Exception(f"Pinecone similarity search failed: {str(e)}")
    
    def mmr_search(
        self,
        text_query: str,
        k: int = 4,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
        threshold: float = 0.5,
        embedding_model: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform Maximum Marginal Relevance (MMR) search using Pinecone.
        
        MMR balances relevance and diversity in search results.
        
        Parameters:
        - query: Search query
        - k: Final number of results
        - fetch_k: Number of candidates to fetch
        - lambda_mult: Diversity factor (0=max diversity, 1=max relevance)
        - threshold: Similarity threshold
        - embedding_model: Model for query embedding
        
        Returns:
        - List of diverse, relevant results
        """
        # Get query embedding
        query_embedding = self._get_query_embedding(query, embedding_model)
        
        # Fetch more candidates than needed for MMR
        try:
            results = self.index.query(
                vector=query_embedding,
                top_k=fetch_k,
                include_metadata=True,
                include_values=True,  # Need values for MMR calculation
            )
            
            candidates = []
            for match in results.matches:
                if match.score and match.score >= threshold:
                    metadata = match.metadata or {}
                    content = metadata.get("content", "")
                    candidates.append({
                        "content": content,
                        "similarity": float(match.score) if match.score else 0.0,
                        "metadata": metadata,
                        "id": match.id,
                        "embedding": match.values,  # Store embedding for MMR
                    })
            
            if not candidates or len(candidates) <= k:
                # Remove embedding before returning
                for c in candidates:
                    c.pop("embedding", None)
                return candidates[:k]
            
            # MMR implementation
            selected = [candidates[0]]  # Start with most relevant
            remaining = candidates[1:]
            
            while len(selected) < k and remaining:
                best_score = -1
                best_idx = 0
                
                for i, candidate in enumerate(remaining):
                    # Calculate MMR score: lambda * relevance - (1-lambda) * max_similarity_to_selected
                    relevance = candidate["similarity"]
                    
                    # Find max similarity to already selected documents
                    max_sim_to_selected = 0.0
                    if candidate.get("embedding") and selected:
                        for selected_doc in selected:
                            if selected_doc.get("embedding"):
                                # Calculate cosine similarity
                                sim = self._cosine_similarity(
                                    candidate["embedding"],
                                    selected_doc["embedding"]
                                )
                                max_sim_to_selected = max(max_sim_to_selected, sim)
                    
                    mmr_score = lambda_mult * relevance - (1 - lambda_mult) * max_sim_to_selected
                    
                    if mmr_score > best_score:
                        best_score = mmr_score
                        best_idx = i
                
                # Add best candidate to selected
                selected.append(remaining.pop(best_idx))
            
            # Remove embeddings before returning
            for doc in selected:
                doc.pop("embedding", None)
            
            return selected
        except Exception as e:
            raise Exception(f"Pinecone MMR search failed: {str(e)}")
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

