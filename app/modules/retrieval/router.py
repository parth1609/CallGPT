"""
Purpose: FastAPI router for Retrieval Service.
Exposes semantic search and reranking endpoints via REST API.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List

from .models import (
    SimilaritySearchRequest,
    MMRSearchRequest,
    RerankSearchRequest,
    SearchResponse,
    SearchResult,
    HealthCheckResponse,
)
from .service import RetrievalService


router = APIRouter(tags=["Retrieval"])


# ============================================================================
# Health Check Endpoint
# ============================================================================


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint for retrieval service.

    Return Value:
    - HealthCheckResponse: Service status
    """
    return HealthCheckResponse(status="healthy", service="retrieval_service")


# ============================================================================
# Similarity Search Endpoints
# ============================================================================


@router.post(
    "/search/similarity", response_model=SearchResponse, status_code=status.HTTP_200_OK
)
async def similarity_search(request: SimilaritySearchRequest):
    """
    Perform similarity search with optional reranking.

    **Standard Search** (use_reranker=False):
    - Retrieves top K documents by cosine similarity

    **Two-Stage Retrieval** (use_reranker=True):
    - Stage 1: Retrieve fetch_k candidates
    - Stage 2: Rerank to top K results using reranker model

    Parameters:
    - request: SimilaritySearchRequest with search parameters

    Return Value:
    - SearchResponse: Search results with metadata

    Example:
    ```json
    {
        "query": "What is machine learning?",
        "index_name": "my-docs",
        "k": 3,
        "use_reranker": true,
        "fetch_k": 20
    }
    ```
    """
    try:
        # Initialize retrieval service
        retrieval_service = RetrievalService(index_name=request.index_name)

        # Perform search
        results = retrieval_service.similarity_search(
            query=request.query,
            k=request.k,
            threshold=request.threshold,
            embedding_model=request.embedding_model,
            use_reranker=request.use_reranker,
            fetch_k=request.fetch_k,
            reranker_model=request.reranker_model,
        )

        # Format response
        search_results = [
            SearchResult(
                content=r.get("content", ""),
                similarity=r.get("similarity", 0.0),
                metadata=r.get("metadata", {}),
                id=r.get("id", ""),
                relevance_score=r.get("relevance_score"),
            )
            for r in results
        ]

        return SearchResponse(
            results=search_results,
            query=request.query,
            total_results=len(search_results),
            search_type="similarity_search",
            used_reranker=request.use_reranker,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.post(
    "/search/mmr", response_model=SearchResponse, status_code=status.HTTP_200_OK
)
async def mmr_search(request: MMRSearchRequest):
    """
    Perform MMR search for diverse results.

    MMR (Maximal Marginal Relevance) balances relevance and diversity.

    Parameters:
    - request: MMRSearchRequest with search parameters

    Return Value:
    - SearchResponse: Diverse search results

    Example:
    ```json
    {
        "query": "Python programming",
        "index_name": "my-docs",
        "k": 5,
        "fetch_k": 30,
        "lambda_mult": 0.7
    }
    ```

    lambda_mult:
    - 0.0 = Maximum diversity
    - 1.0 = Maximum relevance
    - 0.5 = Balanced (default)
    """
    try:
        # Initialize retrieval service
        retrieval_service = RetrievalService(index_name=request.index_name)

        # Perform MMR search
        results = retrieval_service.mmr_search(
            text_query=request.query,
            k=request.k,
            fetch_k=request.fetch_k,
            lambda_mult=request.lambda_mult,
            threshold=request.threshold,
            embedding_model=request.embedding_model,
        )

        # Format response
        search_results = [
            SearchResult(
                content=r.get("content", ""),
                similarity=r.get("similarity", 0.0),
                metadata=r.get("metadata", {}),
                id=r.get("id", ""),
            )
            for r in results
        ]

        return SearchResponse(
            results=search_results,
            query=request.query,
            total_results=len(search_results),
            search_type="mmr_search",
            used_reranker=False,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MMR search failed: {str(e)}",
        )


# ============================================================================
# Dedicated Reranking Endpoint
# ============================================================================


@router.post(
    "/search/rerank", response_model=SearchResponse, status_code=status.HTTP_200_OK
)
async def rerank_search(request: RerankSearchRequest):
    """
    Dedicated two-stage retrieval with reranking.

    **Process:**
    1. Stage 1: Retrieve fetch_k candidates via similarity search
    2. Stage 2: Rerank candidates using Pinecone reranker
    3. Return top_n most relevant results

    Parameters:
    - request: RerankSearchRequest with reranking parameters

    Return Value:
    - SearchResponse: Reranked results with relevance scores

    Example:
    ```json
    {
        "query": "Apple corporation products",
        "index_name": "my-docs",
        "fetch_k": 30,
        "top_n": 5,
        "reranker_model": "bge-reranker-v2-m3"
    }
    ```

    Available reranker models:
    - bge-reranker-v2-m3 (default, multilingual)
    - bge-reranker-base (faster, English)
    - bge-reranker-large (most accurate)
    """
    try:
        # Initialize retrieval service
        retrieval_service = RetrievalService(index_name=request.index_name)

        # Perform reranking search
        results = retrieval_service.rerank_search(
            query=request.query,
            fetch_k=request.fetch_k,
            top_n=request.top_n,
            reranker_model=request.reranker_model,
            embedding_model=request.embedding_model,
        )

        # Format response
        search_results = [
            SearchResult(
                content=r.get("content", ""),
                similarity=r.get("similarity", 0.0),
                metadata=r.get("metadata", {}),
                id=r.get("id", ""),
                relevance_score=r.get("relevance_score"),
            )
            for r in results
        ]

        return SearchResponse(
            results=search_results,
            query=request.query,
            total_results=len(search_results),
            search_type="rerank_search",
            used_reranker=True,
        )

    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Reranking requires langchain-pinecone. Install with: pip install langchain-pinecone",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reranking failed: {str(e)}",
        )
