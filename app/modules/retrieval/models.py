"""
Purpose: Pydantic models for Retrieval Service API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# ============================================================================
# Search Request/Response Models
# ============================================================================


class SimilaritySearchRequest(BaseModel):
    """
    Request model for similarity search.

    Parameters:
    - query (str): Search query text
    - index_name (str): Pinecone index name
    - k (int): Number of results to return
    - threshold (float): Similarity threshold (0.0-1.0)
    - embedding_model (Optional[str]): Embedding model to use
    - use_reranker (bool): Enable two-stage retrieval with reranking
    - fetch_k (int): Initial candidates for reranking (only if use_reranker=True)
    - reranker_model (str): Pinecone reranker model name
    """

    query: str = Field(..., description="Search query text", min_length=1)
    index_name: str = Field(..., description="Pinecone index name")
    k: int = Field(default=4, ge=1, le=20, description="Number of results")
    threshold: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Similarity threshold"
    )
    embedding_model: Optional[str] = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", description="Embedding model"
    )
    use_reranker: bool = Field(default=False, description="Enable reranking")
    fetch_k: int = Field(default=20, ge=5, le=100, description="Initial candidates")
    reranker_model: str = Field(
        default="bge-reranker-v2-m3", description="Reranker model name"
    )


class MMRSearchRequest(BaseModel):
    """
    Request model for MMR search (diversity-focused).

    Parameters:
    - query (str): Search query text
    - index_name (str): Pinecone index name
    - k (int): Final number of results
    - fetch_k (int): Initial candidates to fetch
    - lambda_mult (float): Diversity factor (0=diverse, 1=relevant)
    - threshold (float): Similarity threshold
    - embedding_model (Optional[str]): Embedding model to use
    """

    query: str = Field(..., description="Search query text", min_length=1)
    index_name: str = Field(..., description="Pinecone index name")
    k: int = Field(default=4, ge=1, le=20, description="Final results")
    fetch_k: int = Field(default=20, ge=5, le=100, description="Initial candidates")
    lambda_mult: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Diversity factor"
    )
    threshold: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Similarity threshold"
    )
    embedding_model: Optional[str] = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", description="Embedding model"
    )


class RerankSearchRequest(BaseModel):
    """
    Request model for dedicated reranking search.

    Parameters:
    - query (str): Search query text
    - index_name (str): Pinecone index name
    - fetch_k (int): Initial candidates to retrieve
    - top_n (int): Final number of reranked results
    - reranker_model (str): Pinecone reranker model
    - embedding_model (Optional[str]): Embedding model to use
    """

    query: str = Field(..., description="Search query text", min_length=1)
    index_name: str = Field(..., description="Pinecone index name")
    fetch_k: int = Field(default=20, ge=5, le=100, description="Initial candidates")
    top_n: int = Field(default=4, ge=1, le=20, description="Final reranked results")
    reranker_model: str = Field(
        default="bge-reranker-v2-m3", description="Reranker model name"
    )
    embedding_model: Optional[str] = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", description="Embedding model"
    )


# ============================================================================
# Search Result Models
# ============================================================================


class SearchResult(BaseModel):
    """Individual search result"""

    content: str = Field(..., description="Document content")
    similarity: float = Field(..., description="Cosine similarity score")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Document metadata"
    )
    id: str = Field(..., description="Document ID")
    relevance_score: Optional[float] = Field(
        None, description="Reranker relevance score"
    )


class SearchResponse(BaseModel):
    """
    Response model for search operations.

    Parameters:
    - results (List[SearchResult]): List of search results
    - query (str): Original query
    - total_results (int): Number of results returned
    - search_type (str): Type of search performed
    - used_reranker (bool): Whether reranking was used
    """

    results: List[SearchResult] = Field(..., description="Search results")
    query: str = Field(..., description="Original query")
    total_results: int = Field(..., description="Number of results")
    search_type: str = Field(..., description="Search type used")
    used_reranker: bool = Field(default=False, description="Reranking enabled")


# ============================================================================
# Health Check Model
# ============================================================================


class HealthCheckResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., description="Service status")
    service: str = Field(default="retrieval_service", description="Service name")
