"""
Purpose: Pydantic models for Retrieval Service API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class SearchRequest(BaseModel):
    """Request model for similarity search"""
    query: str = Field(..., description="Search query")
    table_name: str = Field(default="documents", description="Table to search")
    query_function: str = Field(default="match_documents", description="RPC function name")
    k: int = Field(default=4, description="Number of results")
    threshold: float = Field(default=0.5, description="Similarity threshold")
    embedding_model: Optional[str] = Field(default=None, description="Embedding model for query")


class MMRSearchRequest(SearchRequest):
    """Request model for MMR search"""
    fetch_k: int = Field(default=20, description="Number of candidates to fetch")
    lambda_mult: float = Field(default=0.5, description="Diversity factor (0-1)")


class SearchResult(BaseModel):
    """Single search result"""
    content: str
    similarity: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Response model for search"""
    results: List[SearchResult]
    query: str
    total_results: int


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    service: str = "retrieval_service"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
