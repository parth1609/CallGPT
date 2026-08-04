"""
Purpose: Pydantic models for Voice Service API.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class TranscribeResponse(BaseModel):
    """Response model for audio transcription"""

    success: bool = Field(..., description="Whether transcription was successful")
    text: Optional[str] = Field(default=None, description="Transcribed text if successful")
    language: Optional[str] = Field(default=None, description="Language used for transcription")
    provider: Optional[str] = Field(default=None, description="Provider used (groq or sarvam)")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class SpeakRequest(BaseModel):
    """Request model for Text-to-Speech synthesis"""

    text: str = Field(..., description="Text to convert to speech")
    language: Literal["en", "hi", "mr"] = Field(
        default="en",
        description="Language code: 'en' (English/Groq), 'hi' (Hindi/Sarvam), 'mr' (Marathi/Sarvam)"
    )
    voice: Optional[str] = Field(
        default=None,
        description=(
            "Voice name override. "
            "English: troy, tanya, kore (Groq Orpheus). "
            "Hindi/Marathi: shubh, mani, sneha, deba, etc. (Sarvam Bulbul v3)"
        )
    )


class SpeakResponse(BaseModel):
    """Response model for TTS metadata"""

    success: bool = Field(..., description="Whether speech synthesis was successful")
    text_length: int = Field(..., description="Length of the source text")
    audio_size_bytes: int = Field(..., description="Size of the generated audio in bytes")
    language: Optional[str] = Field(default=None, description="Language used for synthesis")
    provider: Optional[str] = Field(default=None, description="Provider used (groq or sarvam)")
    voice: Optional[str] = Field(default=None, description="Voice used for synthesis")


class HealthCheckResponse(BaseModel):
    """Health check response for Voice service"""

    status: str = Field(..., description="Status of the voice service")
    service: str = Field(default="voice_service", description="Name of the service")
    groq_configured: bool = Field(default=False, description="Whether Groq API key is set")
    sarvam_configured: bool = Field(default=False, description="Whether Sarvam API key is set")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current timestamp")
