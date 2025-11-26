"""
Purpose: FastAPI router for Vector Store Module.
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime
import os

from .models import (
    UpsertRequest,
    UpsertResponse,
    CreateIndexRequest,
    CreateIndexResponse,
    IndexListResponse,
    IndexStatsResponse,
    HealthCheckResponse,
    IndexInfo,
    BuildSupabaseRequest,
    BuildSupabaseResponse,
)
from .service import VectorStoreService


router = APIRouter(tags=["VectorStore"])

vectorstore_service = VectorStoreService()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(status="healthy", timestamp=datetime.utcnow())


@router.post("/api/v1/vectorstore/upsert", response_model=UpsertResponse)
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


@router.post("/api/v1/vectorstore/create-index", response_model=CreateIndexResponse)
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


@router.get("/api/v1/vectorstore/indexes", response_model=IndexListResponse)
async def list_indexes():
    """List all vector indexs"""
    indexes = vectorstore_service.list_indexes()
    return IndexListResponse(indexes=[IndexInfo(**t) for t in indexes])


@router.get("/api/v1/vectorstore/stats/{index_name}", response_model=IndexStatsResponse)
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


# ============================================================================
# Utility Endpoints - Supabase Vector Store (Backend-compatible functions)
# ============================================================================

@router.post("/api/v1/vectorstore/utils/supabase/build", response_model=BuildSupabaseResponse)
async def build_supabase_vectorstore(request: BuildSupabaseRequest):
    """
    Build Supabase vector store from text chunks using pipeline utility.
    
    This endpoint exposes build_supabase_from_documents() for testing and
    frontend access before using in the pipeline.
    
    Parameters:
    - request (BuildSupabaseRequest): Chunks and configuration
    
    Return Value:
    - BuildSupabaseResponse: Build result
    """
    from .service import build_supabase_from_documents
    from app.modules.embedding.service import get_embedding_model
    from langchain_core.documents import Document
    
    try:
        # Get embedding model
        emb = get_embedding_model(request.embedding_model)
        
        # Create document objects from chunks
        docs = [Document(page_content=chunk, metadata={}) for chunk in request.chunks]
        
        # Build Supabase vector store
        table_name = build_supabase_from_documents(
            docs=docs,
            embeddings=emb,
            table_name=request.table_name,
            query_name=request.query_name,
        )
        
        return BuildSupabaseResponse(
            success=True,
            table_name=table_name,
            chunks_inserted=len(request.chunks),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase build failed: {str(e)}",
        )

