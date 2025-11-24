"""
Purpose: Business logic for Retrieval Service.
Handles semantic search and document retrieval using Pinecone with LangChain.
"""

import os
import httpx
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pinecone import Pinecone


load_dotenv()


class RetrievalService:
    """Manages semantic search and retrieval operations using Pinecone with LangChain"""
    
    def __init__(
        self,
        embedding_url: Optional[str] = None,
        pinecone_api_key: Optional[str] = None,
        index_name: Optional[str] = None,
    ):
        """Initialize Retrieval Service"""
        self.embedding_url = embedding_url or os.getenv(
            "EMBEDDING_SERVICE_URL",
            "http://embedding_service:8002"
        )
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Initialize Pinecone
        self.pinecone_api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY must be provided")
        
        self.index_name = index_name or os.getenv("SUPABASE_BUCKET")
        if not self.index_name:
            raise ValueError("SUPABASE_BUCKET environment variable must be set")
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        
        # Initialize Pinecone index (will be used with LangChain)
        self.index = self.pc.Index(self.index_name)
    
    async def _get_query_embedding(
        self,
        query: str,
        model_name: Optional[str] = None,
    ) -> List[float]:
        """Get embedding for query text"""
        response = await self.http_client.post(
            f"{self.embedding_url}/api/v1/embeddings/generate",
            json={"texts": [query], "model_name": model_name},
        )
        response.raise_for_status()
        data = response.json()
        return data["embeddings"][0]
    
    async def similarity_search(
        self,
        query: str,
        table_name: str = None,
        query_function: str = None,
        k: int = 4,
        threshold: float = 0.5,
        embedding_model: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search using Pinecone with LangChain.
        
        Parameters:
        - query: Search query text
        - table_name: Ignored (kept for API compatibility)
        - query_function: Ignored (kept for API compatibility)
        - k: Number of results
        - threshold: Similarity threshold (score filter)
        - embedding_model: Model for query embedding
        
        Returns:
        - List of search results with content, similarity, and metadata
        """
        # Get query embedding from embedding service
        query_embedding = await self._get_query_embedding(query, embedding_model)
        
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
    
    async def mmr_search(
        self,
        query: str,
        table_name: str = None,
        query_function: str = None,
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
        - table_name: Ignored (kept for API compatibility)
        - query_function: Ignored (kept for API compatibility)
        - k: Final number of results
        - fetch_k: Number of candidates to fetch
        - lambda_mult: Diversity factor (0=max diversity, 1=max relevance)
        - threshold: Similarity threshold
        - embedding_model: Model for query embedding
        
        Returns:
        - List of diverse, relevant results
        """
        # Get query embedding
        query_embedding = await self._get_query_embedding(query, embedding_model)
        
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
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
