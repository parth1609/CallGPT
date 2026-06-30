"""
Purpose: FastAPI router for Voice Module.
Exposes STT (transcribe) and TTS (speak) as REST endpoints.

Supports multi-language routing:
  - English (en) → Groq Whisper / Orpheus
  - Hindi  (hi) → Sarvam Saaras / Bulbul
  - Marathi(mr) → Sarvam Saaras / Bulbul
"""

import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from fastapi.responses import Response
from datetime import datetime
from typing import Optional

from .models import (
    TranscribeResponse,
    SpeakRequest,
    SpeakResponse,
    HealthCheckResponse,
)
from .service import VoiceService, SARVAM_LANGUAGES


router = APIRouter(tags=["Voice"])

voice_service = VoiceService()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check for Voice service — reports Groq and Sarvam API status."""
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        groq_configured=bool(os.getenv("GROQ_API_KEY")),
        sarvam_configured=bool(os.getenv("SARVAM_API_KEY")),
    )


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file (WAV, MP3, etc.)"),
    language: str = Form(
        default="en",
        description="Language code: 'en' (English/Groq), 'hi' (Hindi/Sarvam), 'mr' (Marathi/Sarvam)",
    ),
):
    """
    Transcribe an audio file to text.

    Routes to Groq Whisper (English) or Sarvam Saaras v3 (Hindi/Marathi)
    based on the language parameter.

    Parameters:
    - file (UploadFile): Audio file to transcribe
    - language (str): Language code — "en", "hi", or "mr"

    Returns:
    - TranscribeResponse: Transcribed text and metadata
    """
    try:
        audio_bytes = await file.read()

        if not audio_bytes or len(audio_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty audio file",
            )

        provider = "sarvam" if language in SARVAM_LANGUAGES else "groq"
        text = voice_service.transcribe(audio_bytes, language=language)

        if text is None:
            return TranscribeResponse(
                success=False,
                text=None,
                language=language,
                provider=provider,
                error=f"Transcription failed — check audio format or {provider.upper()} API key",
            )

        return TranscribeResponse(
            success=True,
            text=text,
            language=language,
            provider=provider,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}",
        )


@router.post("/speak")
async def text_to_speech(request: SpeakRequest):
    """
    Convert text to speech.

    Routes to Groq Orpheus (English) or Sarvam Bulbul v3 (Hindi/Marathi)
    based on the language parameter.

    Parameters:
    - request (SpeakRequest): Text, language, and optional voice selection

    Returns:
    - Binary audio response with Content-Type: audio/wav
    """
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text cannot be empty",
            )

        provider = "sarvam" if request.language in SARVAM_LANGUAGES else "groq"
        audio_bytes = voice_service.speak(
            request.text,
            language=request.language,
            voice=request.voice,
        )

        if audio_bytes is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="TTS synthesis failed — no audio generated",
            )

        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=speech.wav",
                "X-Audio-Size": str(len(audio_bytes)),
                "X-Voice-Used": request.voice or "default",
                "X-Language": request.language,
                "X-Provider": provider,
                "X-Text-Length": str(len(request.text)),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS failed: {str(e)}",
        )


@router.post("/speak/metadata", response_model=SpeakResponse)
async def text_to_speech_metadata(request: SpeakRequest):
    """
    Generate TTS and return metadata only (without audio binary).

    Useful for checking if TTS will succeed and getting audio size info.

    Parameters:
    - request (SpeakRequest): Text, language, and optional voice selection

    Returns:
    - SpeakResponse: Metadata about the generated audio
    """
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text cannot be empty",
            )

        provider = "sarvam" if request.language in SARVAM_LANGUAGES else "groq"
        audio_bytes = voice_service.speak(
            request.text,
            language=request.language,
            voice=request.voice,
        )

        if audio_bytes is None:
            return SpeakResponse(
                success=False,
                text_length=len(request.text),
                audio_size_bytes=0,
                language=request.language,
                provider=provider,
                voice=request.voice,
            )

        return SpeakResponse(
            success=True,
            text_length=len(request.text),
            audio_size_bytes=len(audio_bytes),
            language=request.language,
            provider=provider,
            voice=request.voice,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS metadata failed: {str(e)}",
        )
