"""
Purpose: Pydantic models for Document Service API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class DocumentUploadRequest(BaseModel):
    """
    Request model for document upload.
    
    Parameters:
    - filename (str): Name of the file being uploaded
    - content (str): Text content of the document
    - metadata (Optional[Dict]): Additional metadata for the document
    """
    filename: str = Field(..., description="Name of the file")
    content: str = Field(..., description="Text content of the document")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class DocumentUploadResponse(BaseModel):
    """
    Response model for successful document upload.
    
    Parameters:
    - document_id (str): Unique identifier for the uploaded document
    - filename (str): Name of the uploaded file
    - size (int): Size of the document in bytes
    - public_url (Optional[str]): Public URL if the file is publicly accessible
    - created_at (datetime): Timestamp of upload
    """
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="File name")
    size: int = Field(..., description="File size in bytes")
    public_url: Optional[str] = Field(None, description="Public URL")
    created_at: datetime = Field(..., description="Upload timestamp")


class DocumentMetadataResponse(BaseModel):
    """
    Response model for document metadata retrieval.
    
    Parameters:
    - document_id (str): Unique identifier for the document
    - filename (str): Name of the file
    - size (int): Size in bytes
    - content_type (str): MIME type of the document
    - created_at (datetime): Creation timestamp
    - updated_at (datetime): Last update timestamp
    - metadata (Dict): Additional metadata
    """
    document_id: str
    filename: str
    size: int
    content_type: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]


class DocumentListResponse(BaseModel):
    """
    Response model for listing documents.
    
    Parameters:
    - documents (list): List of document metadata
    - total (int): Total count of documents
    """
    documents: list[DocumentMetadataResponse]
    total: int


class DocumentContentResponse(BaseModel):
    """
    Response model for document content retrieval.
    
    Parameters:
    - document_id (str): Document identifier
    - filename (str): File name
    - content (str): Text content of the document
    """
    document_id: str
    filename: str
    content: str


class HealthCheckResponse(BaseModel):
    """
    Response model for health check endpoint.
    
    Parameters:
    - status (str): Service status ('healthy' or 'unhealthy')
    - service (str): Service name
    - timestamp (datetime): Current timestamp
    """
    status: str = Field(..., description="Service status")
    service: str = Field(default="document_service", description="Service name")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current timestamp")


# Utility function models

class ChunkDocumentsRequest(BaseModel):
    """
    Request model for chunking documents utility.
    
    Parameters:
    - content (str): Text content to chunk
    - chunk_size (int): Maximum size of each chunk
    - chunk_overlap (int): Overlap between chunks
    """
    content: str = Field(..., description="Text content to chunk")
    chunk_size: int = Field(default=1000, description="Maximum chunk size in characters")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")


class ChunkDocumentsResponse(BaseModel):
    """
    Response model for chunking operation.
    
    Parameters:
    - chunks (list[str]): List of text chunks
    - total_chunks (int): Number of chunks created
    """
    chunks: list[str] = Field(..., description="List of text chunks")
    total_chunks: int = Field(..., description="Total number of chunks")

