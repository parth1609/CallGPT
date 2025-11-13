"""
Purpose: FastAPI application for Embedding Service.
Handles text chunking and embedding generation.

Usage:
    uvicorn main:app --host 0.0.0.0 --port 8002 --reload
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

from models import (
    ChunkRequest,
    ChunkResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    ChunkAndEmbedRequest,
    ChunkAndEmbedResponse,
    ModelsListResponse,
    ModelInfo,
    HealthCheckResponse,
)
from service import EmbeddingService


app = FastAPI(
    title="Embedding Service",
    description="Microservice for text chunking and embedding generation",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service
embedding_service = EmbeddingService()


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint to verify service availability.
    
    Return Value:
    - HealthCheckResponse: Service status and timestamp
    """
    return HealthCheckResponse(
        status="healthy",
        service="embedding_service",
        timestamp=datetime.utcnow(),
    )


@app.post("/api/v1/embeddings/chunk", response_model=ChunkResponse)
async def chunk_text(request: ChunkRequest):
    """
    Chunk text into smaller segments.
    
    Parameters:
    - request (ChunkRequest): Text and chunking parameters
    
    Return Value:
    - ChunkResponse: List of text chunks
    """
    try:
        chunks = embedding_service.chunk_text(
            text=request.text,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
        )
        
        return ChunkResponse(
            chunks=chunks,
            total_chunks=len(chunks),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chunking failed: {str(e)}",
        )


@app.post("/api/v1/embeddings/generate", response_model=EmbeddingResponse)
async def generate_embeddings(request: EmbeddingRequest):
    """
    Generate embeddings for a list of texts.
    
    Parameters:
    - request (EmbeddingRequest): Texts and model name
    
    Return Value:
    - EmbeddingResponse: Embedding vectors and metadata
    """
    try:
        embeddings, model_name, dimension = embedding_service.generate_embeddings(
            texts=request.texts,
            model_name=request.model_name,
        )
        
        return EmbeddingResponse(
            embeddings=embeddings,
            model_name=model_name,
            dimension=dimension,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding generation failed: {str(e)}",
        )


@app.post("/api/v1/embeddings/chunk-and-embed", response_model=ChunkAndEmbedResponse)
async def chunk_and_embed(request: ChunkAndEmbedRequest):
    """
    Chunk text and generate embeddings in one operation.
    
    Parameters:
    - request (ChunkAndEmbedRequest): Text, chunking, and embedding parameters
    
    Return Value:
    - ChunkAndEmbedResponse: Chunks and their embeddings
    
    Side Effects:
    - Loads embedding model (cached)
    """
    try:
        chunks, embeddings, model_name, total_chunks = embedding_service.chunk_and_embed(
            text=request.text,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            model_name=request.model_name,
        )
        
        return ChunkAndEmbedResponse(
            chunks=chunks,
            embeddings=embeddings,
            model_name=model_name,
            total_chunks=total_chunks,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chunk and embed failed: {str(e)}",
        )


@app.get("/api/v1/embeddings/models", response_model=ModelsListResponse)
async def list_models():
    """
    Get list of available embedding models.
    
    Return Value:
    - ModelsListResponse: List of available models with metadata
    """
    models = embedding_service.get_available_models()
    
    return ModelsListResponse(
        models=[ModelInfo(**model) for model in models]
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
