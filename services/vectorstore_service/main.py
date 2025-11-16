"""
Purpose: FastAPI application for Vector Store Service.

Usage:
    uvicorn main:app --host 0.0.0.0 --port 8003 --reload
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

from models import (
    UpsertRequest,
    UpsertResponse,
    CreateIndexRequest,
    CreateIndexResponse,
    IndexListResponse,
    IndexStatsResponse,
    HealthCheckResponse,
    IndexInfo,
)
from service import VectorStoreService


app = FastAPI(
    title="Vector Store Service",
    description="Microservice for vector database operations with Pinecone",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vectorstore_service = VectorStoreService()


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(status="healthy", timestamp=datetime.utcnow())


@app.post("/api/v1/vectorstore/upsert", response_model=UpsertResponse)
async def upsert_vectors(request: UpsertRequest):
    """Upsert vectors to Supabase pgvector"""
    try:
        result = vectorstore_service.upsert_vectors(
            chunks=request.chunks,
            embeddings=request.embeddings,
            index_name=request.index_name,
            metadata=request.metadata,
        )
        return UpsertResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upsert failed: {str(e)}",
        )


@app.post("/api/v1/vectorstore/create-index", response_model=CreateIndexResponse)
async def create_index(request: CreateIndexRequest):
    """to create a vector index"""
    try:
        result = vectorstore_service.create_index(
            index_name=request.index_name,
            dimension=request.dimension,

        )
        return CreateIndexResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Index creation failed: {str(e)}",
        )


@app.get("/api/v1/vectorstore/indexes", response_model=IndexListResponse)
async def list_indexes():
    """List all vector indexs"""
    indexes = vectorstore_service.list_indexes()
    return IndexListResponse(indexes=[IndexInfo(**t) for t in indexes])


@app.get("/api/v1/vectorstore/stats/{index_name}", response_model=IndexStatsResponse)
async def get_index_stats(index_name: str):
    """Get statistics for a specific table"""
    try:
        stats = vectorstore_service.get_index_stats(index_name)
        return IndexStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Index not found: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)
