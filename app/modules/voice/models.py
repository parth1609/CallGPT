"""
Purpose: Pydantic models for Voice Service API.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TranscribeResponse(BaseModel):
    """Response model for audio transcription"""

    success: bool = Field(..., description="Whether transcription was successful")
    text: Optional[str] = Field(default=None, description="Transcribed text if successful")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class SpeakRequest(BaseModel):
    """Request model for Text-to-Speech synthesis"""

    text: str = Field(..., description="Text to convert to speech")
    voice: Optional[str] = Field(
        default="en-US-EmmaNeural",
        description="Voice name to use for speech synthesis"
    )


class SpeakResponse(BaseModel):
    """Response model for TTS metadata"""

    success: bool = Field(..., description="Whether speech synthesis was successful")
    text_length: int = Field(..., description="Length of the source text")
    audio_size_bytes: int = Field(..., description="Size of the generated audio in bytes")
    voice: Optional[str] = Field(default=None, description="Voice used for synthesis")


class HealthCheckResponse(BaseModel):
    """Health check response for Voice service"""

    status: str = Field(..., description="Status of the voice service")
    service: str = Field(default="voice_service", description="Name of the service")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current timestamp")
