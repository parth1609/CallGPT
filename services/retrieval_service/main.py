"""
Purpose: FastAPI application for Retrieval Service.

Usage:
    uvicorn main:app --host 0.0.0.0 --port 8004 --reload
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

from models import (
    SearchRequest,
    MMRSearchRequest,
    SearchResult,
    SearchResponse,
    HealthCheckResponse,
)
from service import RetrievalService


app = FastAPI(
    title="Retrieval Service",
    description="Microservice for semantic search and document retrieval using Pinecone with LangChain",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

retrieval_service = RetrievalService()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await retrieval_service.close()


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(status="healthy", timestamp=datetime.utcnow())


@app.post("/api/v1/retrieval/search", response_model=SearchResponse)
async def similarity_search(request: SearchRequest):
    """Perform similarity search"""
    try:
        results = await retrieval_service.similarity_search(
            query=request.query,
            table_name=request.table_name,
            query_function=request.query_function,
            k=request.k,
            threshold=request.threshold,
            embedding_model=request.embedding_model,
        )
        
        return SearchResponse(
            results=[
                SearchResult(
                    content=r.get("content", ""),
                    similarity=r.get("similarity", 0.0),
                    metadata=r.get("metadata", {}),
                )
                for r in results
            ],
            query=request.query,
            total_results=len(results),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@app.post("/api/v1/retrieval/mmr-search", response_model=SearchResponse)
async def mmr_search(request: MMRSearchRequest):
    """Perform MMR search for diverse results"""
    try:
        results = await retrieval_service.mmr_search(
            query=request.query,
            table_name=request.table_name,
            query_function=request.query_function,
            k=request.k,
            fetch_k=request.fetch_k,
            lambda_mult=request.lambda_mult,
            threshold=request.threshold,
            embedding_model=request.embedding_model,
        )
        
        return SearchResponse(
            results=[
                SearchResult(
                    content=r.get("content", ""),
                    similarity=r.get("similarity", 0.0),
                    metadata=r.get("metadata", {}),
                )
                for r in results
            ],
            query=request.query,
            total_results=len(results),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MMR search failed: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
