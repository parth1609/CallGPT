"""
Retrieval module for semantic search and document retrieval.
Supports similarity search, MMR search, and Pinecone reranking.
"""

from .router import router
from .service import RetrievalService
from .models import (
    SimilaritySearchRequest,
    MMRSearchRequest,
    RerankSearchRequest,
    SearchResponse,
    SearchResult,
    HealthCheckResponse,
)

__all__ = [
    "router",
    "RetrievalService",
    "SimilaritySearchRequest",
    "MMRSearchRequest",
    "RerankSearchRequest",
    "SearchResponse",
    "SearchResult",
    "HealthCheckResponse",
]
