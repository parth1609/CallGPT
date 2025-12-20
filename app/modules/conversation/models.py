"""
Purpose: Pydantic models for Conversation Service API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

# add messages in the thread (OK)
class AddMessage(BaseModel):
    """Request to add a message to a thread"""
    type: str = Field(..., description="Message type: 'HumanMessage' or 'AIMessage'")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Message metadata")

class MessageResponse(BaseModel):
    """Response model for message"""
    messages_id: UUID
    thread_id: UUID
    index: int
    type: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
 
# create the thread (ok)
class CreateThreadRequest(BaseModel):
    """Request to create a new conversation thread with optional initial messages"""
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Thread metadata")
    conversation: Optional[List[AddMessage]] = Field(
        default=None, 
        description="Optional initial messages to add to the thread"
    )

class ThreadResponse(BaseModel):
    """Response model for newly created thread"""
    thread_id: UUID
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


 
# Retrive the thread data (ok)
class MessageModel(BaseModel):
    """Model for a single message in a thread"""
    messages_id: UUID
    thread_id: UUID
    index: int
    type: str  # "HumanMessage" or "AIMessage"
    content: str
    created_at: datetime
    class Config:
        from_attributes = True  # Allows creating from dict/ORM objects

class ThreadMessagesResponse(BaseModel):
    """Response model for a thread with all its messages"""
    thread_id: UUID
    messages: List[MessageModel]
    class Config:
        from_attributes = True

  
class AllThreadsMessagesResponse(BaseModel):
    """Response model for all threads with their messages"""
    threads: List[ThreadMessagesResponse]
    total: int = Field(description="Total number of threads")
    class Config:
        from_attributes = True

# Health check (ok)
class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    service: str = "conversation_service"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# messages list of specific thread
class MessagesListResponse(BaseModel):
    """Response model for a list of messages"""
    messages: List[MessageModel]
    thread_id: UUID
    total: int = Field(description="Total number of messages")
    class Config:
        from_attributes = True