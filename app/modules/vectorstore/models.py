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
    index_name: str = Field(default="supabase-bucket", description="Index name")
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


# Utility function models for Supabase operations

class BuildSupabaseRequest(BaseModel):
    """Request model for building Supabase vector store"""
    chunks: List[str] = Field(..., description="Text chunks to store")
    table_name: str = Field(default="documents", description="Supabase table name")
    query_name: str = Field(default="match_documents", description="RPC function name")
    embedding_model: Optional[str] = Field(default=None, description="Embedding model name")


class BuildSupabaseResponse(BaseModel):
    """Response model for Supabase build operation"""
    success: bool
    table_name: str
    chunks_inserted: int

