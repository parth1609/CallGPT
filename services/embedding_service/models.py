"""
Purpose: Pydantic models for Embedding Service API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ChunkRequest(BaseModel):
    """
    Request model for text chunking.
    
    Parameters:
    - text (str): Text content to chunk
    - chunk_size (int): Size of each chunk (default: 1000)
    - chunk_overlap (int): Overlap between chunks (default: 200)
    """
    text: str = Field(..., description="Text content to chunk")
    chunk_size: int = Field(default=1000, description="Size of each chunk")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")


class ChunkResponse(BaseModel):
    """
    Response model for chunked text.
    
    Parameters:
    - chunks (List[str]): List of text chunks
    - total_chunks (int): Total number of chunks created
    """
    chunks: List[str] = Field(..., description="List of text chunks")
    total_chunks: int = Field(..., description="Total number of chunks")


class EmbeddingRequest(BaseModel):
    """
    Request model for embedding generation.
    
    Parameters:
    - texts (List[str]): List of texts to embed
    - model_name (Optional[str]): Embedding model name
    """
    texts: List[str] = Field(..., description="List of texts to embed")
    model_name: Optional[str] = Field(default=None, description="Embedding model name")


class EmbeddingResponse(BaseModel):
    """
    Response model for generated embeddings.
    
    Parameters:
    - embeddings (List[List[float]]): List of embedding vectors
    - model_name (str): Model used for embedding
    - dimension (int): Dimension of each embedding vector
    """
    embeddings: List[List[float]] = Field(..., description="Embedding vectors")
    model_name: str = Field(..., description="Model used")
    dimension: int = Field(..., description="Embedding dimension")


class ChunkAndEmbedRequest(BaseModel):
    """
    Request model for combined chunking and embedding.
    
    Parameters:
    - text (str): Text content to process
    - chunk_size (int): Size of each chunk
    - chunk_overlap (int): Overlap between chunks
    - model_name (Optional[str]): Embedding model name
    """
    text: str = Field(..., description="Text content")
    chunk_size: int = Field(default=1000, description="Chunk size")
    chunk_overlap: int = Field(default=200, description="Chunk overlap")
    model_name: Optional[str] = Field(default=None, description="Embedding model")


class ChunkAndEmbedResponse(BaseModel):
    """
    Response model for chunked and embedded text.
    
    Parameters:
    - chunks (List[str]): Text chunks
    - embeddings (List[List[float]]): Embedding vectors for each chunk
    - model_name (str): Model used
    - total_chunks (int): Total number of chunks
    """
    chunks: List[str]
    embeddings: List[List[float]]
    model_name: str
    total_chunks: int


class ModelInfo(BaseModel):
    """
    Information about an available embedding model.
    
    Parameters:
    - name (str): Model name
    - dimension (int): Embedding dimension
    - description (str): Model description
    """
    name: str
    dimension: int
    description: str


class ModelsListResponse(BaseModel):
    """
    Response model for available models list.
    
    Parameters:
    - models (List[ModelInfo]): List of available models
    """
    models: List[ModelInfo]


class HealthCheckResponse(BaseModel):
    """
    Response model for health check endpoint.
    
    Parameters:
    - status (str): Service status
    - service (str): Service name
    - timestamp (datetime): Current timestamp
    """
    status: str
    service: str = "embedding_service"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
