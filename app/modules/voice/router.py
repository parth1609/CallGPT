"""
Purpose: FastAPI router for Voice Module.
Exposes STT (transcribe) and TTS (speak) as REST endpoints.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from fastapi.responses import Response
from datetime import datetime

from .models import (
    TranscribeResponse,
    SpeakRequest,
    SpeakResponse,
    HealthCheckResponse,
)
from .service import VoiceService


router = APIRouter(tags=["Voice"])

voice_service = VoiceService()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check for Voice service"""
    return HealthCheckResponse(status="healthy", timestamp=datetime.utcnow())


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file (WAV, MP3, etc.)"),
):
    """
    Transcribe an audio file to text using Groq Whisper API.

    Upload any audio file (WAV, MP3, WebM, OGG, etc.) and receive
    the transcribed text.

    Parameters:
    - file (UploadFile): Audio file to transcribe

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

        text = voice_service.transcribe(audio_bytes)

        if text is None:
            return TranscribeResponse(
                success=False,
                text=None,
                error="Transcription failed — check audio format or Groq API key",
            )

        return TranscribeResponse(success=True, text=text)

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
    Convert text to speech using Edge TTS.

    Returns MP3 audio bytes as a binary response.

    Parameters:
    - request (SpeakRequest): Text and optional voice selection

    Returns:
    - Binary MP3 audio response with Content-Type: audio/mpeg
    """
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text cannot be empty",
            )

        audio_bytes = voice_service.speak(request.text)

        if audio_bytes is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="TTS synthesis failed — no audio generated",
            )

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3",
                "X-Audio-Size": str(len(audio_bytes)),
                "X-Voice-Used": request.voice,
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
    - request (SpeakRequest): Text and optional voice selection

    Returns:
    - SpeakResponse: Metadata about the generated audio
    """
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text cannot be empty",
            )

        audio_bytes = voice_service.speak(request.text)

        if audio_bytes is None:
            return SpeakResponse(
                success=False,
                text_length=len(request.text),
                audio_size_bytes=0,
                voice=request.voice,
            )

        return SpeakResponse(
            success=True,
            text_length=len(request.text),
            audio_size_bytes=len(audio_bytes),
            voice=request.voice,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS metadata failed: {str(e)}",
        )
