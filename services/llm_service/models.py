"""
Purpose: Pydantic models for LLM Service API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class Message(BaseModel):
    """Chat message"""
    role: str = Field(..., description="Message role: 'user' or 'assistant' or 'system'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request model for chat completion"""
    messages: List[Message] = Field(..., description="Conversation messages")
    model: Optional[str] = Field(default=None, description="LLM model name")
    temperature: float = Field(default=0.5, description="Sampling temperature")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")
    stream: bool = Field(default=False, description="Stream response")


class ChatResponse(BaseModel):
    """Response model for chat completion"""
    message: Message
    model: str
    usage: Optional[Dict[str, int]] = None


class StreamChunk(BaseModel):
    """Streaming response chunk"""
    content: str
    finish_reason: Optional[str] = None


class ModelInfo(BaseModel):
    """LLM model information"""
    name: str
    provider: str
    description: str


class ModelsListResponse(BaseModel):
    """Response model for available models"""
    models: List[ModelInfo]


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    service: str = "llm_service"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
