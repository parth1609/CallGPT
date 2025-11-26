"""
Purpose: Pydantic models for Conversation Service API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class CreateThreadRequest(BaseModel):
    """Request to create a new conversation thread"""
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Thread metadata")


class ThreadResponse(BaseModel):
    """Response model for thread"""
    id: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AddMessageRequest(BaseModel):
    """Request to add a message to a thread"""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Message metadata")


class MessageResponse(BaseModel):
    """Response model for message"""
    id: str
    thread_id: str
    role: str
    content: str
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ThreadListResponse(BaseModel):
    """Response model for listing threads"""
    threads: List[ThreadResponse]
    total: int


class MessagesListResponse(BaseModel):
    """Response model for listing messages"""
    messages: List[MessageResponse]
    thread_id: str
    total: int


class ThreadPreviewResponse(BaseModel):
    """Response model for thread preview"""
    thread_id: str
    preview: str
    message_count: int
    last_updated: datetime


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    service: str = "conversation_service"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
