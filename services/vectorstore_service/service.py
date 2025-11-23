"""
Purpose: Business logic for Vector Store Service using Pinecone.
"""

import os
import time
from typing import List, Optional, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from uuid import uuid4
from dotenv import load_dotenv


load_dotenv()


class VectorStoreService:
    """Manages vector database operations with Pinecone"""
    
    def __init__(self, pinecone_api_key: Optional[str] = None):
        """Initialize Vector Store Service with Pinecone connection"""
        self.pinecone_api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY must be provided")
        self.pc: Pinecone = Pinecone(api_key=self.pinecone_api_key)
        # SUPABASE BUCKET = INDEX NAME (Organisation name)
        self.default_index = os.getenv("SUPABASE_BUCKET")
        self.cloud = os.getenv("PINECONE_CLOUD", "aws")
        self.region = os.getenv("PINECONE_REGION", "us-east-1")
    
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
            vectors.append({
                "id": f"{prefix}-{i}",
                "values": embedding,
                "metadata": meta,
            })

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
            elif isinstance(value, list) and all(isinstance(item, str) for item in value):
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
                    tables.append({
                        "index_name": idx.name,
                        "row_count": int(stats.get("total_vector_count", 0) or 0),
                        "dimension": stats.get("dimension"),
                    })
                except Exception:
                    tables.append({
                        "index_name": idx.name,
                        "row_count": 0,
                        "dimension": None,
                    })
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
