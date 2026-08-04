"""
Purpose: Pydantic models for Voicebot Service API.
Handles request/response schemas for call logs, active calls, and company management.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class CallLogEntry(BaseModel):
    """Single call log record from Supabase"""

    id: Optional[str] = Field(default=None, description="Call log UUID")
    company_id: Optional[str] = Field(default=None, description="Company UUID")
    company_name: Optional[str] = Field(default=None, description="Company name")
    caller_number: str = Field(..., description="Farmer's phone number")
    question: Optional[str] = Field(
        default=None, description="Transcribed farmer utterance"
    )
    answer: Optional[str] = Field(default=None, description="AI-generated response")
    called_at: Optional[datetime] = Field(
        default=None, description="When the call was made"
    )


class CallLogsResponse(BaseModel):
    """Response model for call logs list"""

    success: bool
    logs: List[CallLogEntry]
    total_count: int = Field(..., description="Total number of logs returned")


class ActiveCallInfo(BaseModel):
    """Information about a currently active WebSocket call"""

    stream_sid: Optional[str] = Field(
        default=None, description="Exotel stream session ID"
    )
    caller_number: Optional[str] = Field(
        default=None, description="Farmer's phone number"
    )
    called_number: Optional[str] = Field(
        default=None, description="Exotel number dialed"
    )
    company_name: Optional[str] = Field(
        default=None, description="Matched company name"
    )
    bucket_name: Optional[str] = Field(default=None, description="Vector store bucket")
    thread_id: Optional[str] = Field(default=None, description="Conversation thread ID")
    turn_count: int = Field(
        default=0, description="Number of conversation turns so far"
    )
    connected_at: Optional[datetime] = Field(
        default=None, description="When the call connected"
    )


class ActiveCallsResponse(BaseModel):
    """Response model for active calls list"""

    success: bool
    active_calls: List[ActiveCallInfo]
    total_active: int = Field(..., description="Number of active calls")


class CompanyInfo(BaseModel):
    """Company information from Supabase"""

    id: Optional[str] = Field(default=None, description="Company UUID")
    company_name: str = Field(..., description="Company name")
    bucket_name: str = Field(..., description="Vector store bucket name")
    exotel_number: str = Field(..., description="Exotel phone number")
    created_at: Optional[datetime] = Field(
        default=None, description="When the company was created"
    )


class CompanyListResponse(BaseModel):
    """Response model for companies list"""

    success: bool
    companies: List[CompanyInfo]
    total_count: int


class VoicebotConfigResponse(BaseModel):
    """Current voicebot pipeline configuration"""

    success: bool
    stt_model: str = "whisper-large-v3-turbo"
    tts_engine: str = "edge-tts"
    tts_voice: str = "en-US-JennyNeural"
    pipeline_defaults: Dict[str, Any] = Field(
        ..., description="Default pipeline parameters for voice calls"
    )
    audio_format: Dict[str, Any] = Field(
        default={
            "sample_rate": 8000,
            "channels": 1,
            "sample_width": 2,
            "encoding": "linear-pcm",
        },
        description="Exotel audio format specifications",
    )


class HealthCheckResponse(BaseModel):
    """Health check response for Voicebot service"""

    status: str
    service: str = "voicebot_service"
    active_calls: int = Field(default=0, description="Number of active WebSocket calls")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
