"""
Purpose: Pydantic models for Pipeline Service API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


# ============================================================================
# Organisation Pipeline Models
# ============================================================================


class OrganisationUploadRequest(BaseModel):
    """
    Request model for organisation document upload via JSON.

    Parameters:
    - bucket_name (str): Name of the bucket/index for storage
    - filename (str): Original filename
    - content (str): Text content of the document
    - embeddings_model (str): Model to use for generating embeddings
    - chunk_size (int): Size of text chunks
    - chunk_overlap (int): Overlap between chunks
    - metadata (Optional[Dict]): Additional metadata for the document
    """

    bucket_name: str = Field(..., description="Bucket/Index name for storage")
    filename: str = Field(..., description="Original filename")
    content: str = Field(..., description="Text content of the document")
    embeddings_model: str = Field(
        default="text-embedding-3-small", description="Embedding model to use"
    )
    chunk_size: Optional[int] = Field(
        default=500, description="Size of text chunks in characters"
    )
    chunk_overlap: Optional[int] = Field(
        default=50, description="Overlap between chunks in characters"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )


class OrganisationUploadResponse(BaseModel):
    """
    Response model for successful document processing through pipeline.

    Parameters:
    - status (str): Processing status
    - message (str): Human-readable message
    - filename (str): Processed filename
    - bucket_name (str): Bucket/Index where data is stored
    - chunks_created (int): Number of chunks created
    - metadata (Optional[Dict]): Document metadata
    """

    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")
    filename: str = Field(..., description="Filename")
    bucket_name: str = Field(..., description="Bucket/Index name")
    chunks_created: int = Field(..., description="Number of chunks created")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Document metadata"
    )


# ============================================================================
# Customer Query Pipeline Models
# ============================================================================


class CustomerQueryRequest(BaseModel):
    """
    Request model for customer query pipeline.

    Parameters:
    - bucket_name (str): Name of the bucket/index to query
    - question (str): User's question
    - embeddings_model (str): Model for query embedding
    - llm_model (str): LLM model for answer generation
    - temperature (float): Temperature for LLM
    - search_type (str): Type of search (similarity_search or mmr_search)
    - k (int): Number of documents to retrieve
    - fetch_k (Optional[int]): For MMR search
    - lambda_mult (Optional[float]): For MMR search
    - thread_id (Optional[str]): Thread ID for conversation tracking
    """

    bucket_name: str = Field(..., description="Bucket/Index name to query")
    question: str = Field(..., description="User's question")
    embeddings_model: str = Field(
        default="text-embedding-3-small", description="Embedding model"
    )
    llm_model: str = Field(
        default="openai/gpt-oss-120b", description="LLM model for generation"
    )
    temperature: float = Field(
        default=0.5, ge=0.0, le=1.0, description="LLM temperature"
    )
    search_type: str = Field(
        default="similarity_search",
        description="Search type: similarity_search or mmr_search",
    )
    k: int = Field(
        default=4, ge=1, le=20, description="Number of documents to retrieve"
    )
    fetch_k: Optional[int] = Field(
        default=20,
        ge=1,
        description="MMR: Number of documents to fetch before filtering",
    )
    lambda_mult: Optional[float] = Field(
        default=0.5, ge=0.0, le=1.0, description="MMR: Lambda multiplier for diversity"
    )
    thread_id: Optional[str] = Field(
        default=None, description="Thread ID for conversation tracking"
    )


class CustomerQueryResponse(BaseModel):
    """
    Response model for customer query.

    Parameters:
    - answer (str): Generated answer
    - question (str): Original question
    - thread_id (Optional[str]): Thread ID used
    """

    answer: str = Field(..., description="Generated answer")
    question: str = Field(..., description="Original question")
    thread_id: Optional[str] = Field(
        default=None, description="Thread ID for conversation tracking"
    )


# ============================================================================
# Health Check Model
# ============================================================================


class HealthCheckResponse(BaseModel):
    """
    Response model for health check endpoint.

    Parameters:
    - status (str): Service status ('healthy' or 'unhealthy')
    - service (str): Service name
    - timestamp (datetime): Current timestamp
    """

    status: str = Field(..., description="Service status")
    service: str = Field(default="pipeline_service", description="Service name")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Current timestamp"
    )
