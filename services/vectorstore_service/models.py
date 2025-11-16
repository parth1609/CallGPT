"""
Purpose: Pydantic models for Vector Store Service API.
"""


from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class UpsertRequest(BaseModel):
    """Request model for upserting vectors"""
    chunks: List[str] = Field(..., description="Text chunks")
    embeddings: List[List[float]] = Field(..., description="Embedding vectors")
    index_name: str = Field(default="documents", description="Index name")
    metadata: Optional[List[Dict[str, Any]]] = Field(default=None, description="Metadata for each chunk")


class UpsertResponse(BaseModel):
    """Response model for upsert operation"""
    success: bool
    inserted_count: int
    index_name: str


class CreateIndexRequest(BaseModel):
    """Request model for creating a vector table"""
    index_name: str = Field(..., description="Index name")
    dimension: int = Field(..., description="Vector dimension")
    
class CreateIndexResponse(BaseModel):
    """Response model for index creation"""
    success: bool
    index_name: str
    message: str


class IndexInfo(BaseModel):
    """Information about a vector table"""
    index_name: str
    row_count: int
    dimension: Optional[int] = None


class IndexListResponse(BaseModel):
    """Response model for Indexes list"""
    indexes: List[IndexInfo]


class IndexStatsResponse(BaseModel):
    """Response model for index statistics"""
    index_name: str
    row_count: int
    dimension: Optional[int] = None
    created_at: Optional[datetime] = None


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    service: str = "vectorstore_service"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
