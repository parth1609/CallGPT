"""
Purpose: Service layer for Exotel Voicebot integration.
Handles per-call state management, company lookup, call logging,
and audio format conversions (PCM <-> WAV, MP3 -> PCM).
"""

import os
import io
import wave
import base64
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Audio conversion utilities
# ---------------------------------------------------------------------------


def pcm_to_wav(
    pcm_bytes: bytes, sample_rate: int = 8000, channels: int = 1, sample_width: int = 2
) -> bytes:
    """
    Wrap raw Linear PCM bytes in a WAV header.

    Parameters:
    - pcm_bytes: Raw PCM audio data (16-bit signed, little-endian)
    - sample_rate: Sample rate in Hz (Exotel uses 8000)
    - channels: Number of audio channels (1 = mono)
    - sample_width: Bytes per sample (2 = 16-bit)

    Returns:
    - Complete WAV file as bytes
    """
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


def mp3_to_pcm(
    mp3_bytes: bytes,
    target_rate: int = 8000,
    target_channels: int = 1,
    target_width: int = 2,
) -> bytes:
    """
    Convert MP3 audio bytes to raw Linear PCM (8kHz, 16-bit, mono).

    Uses pydub (requires ffmpeg on the system).

    Parameters:
    - mp3_bytes: MP3 audio data
    - target_rate: Output sample rate (8000 for Exotel)
    - target_channels: Output channels (1 = mono)
    - target_width: Output bytes per sample (2 = 16-bit)

    Returns:
    - Raw PCM audio bytes
    """
    audio = AudioSegment.from_mp3(io.BytesIO(mp3_bytes))
    audio = (
        audio.set_frame_rate(target_rate)
        .set_channels(target_channels)
        .set_sample_width(target_width)
    )
    raw_pcm = audio.raw_data

    # Ensure raw PCM length is a multiple of 320 bytes for Exotel compatibility
    remainder = len(raw_pcm) % 320
    if remainder != 0:
        padding = b"\x00" * (320 - remainder)
        raw_pcm += padding

    return raw_pcm


# ---------------------------------------------------------------------------
# Supabase helpers
# ---------------------------------------------------------------------------


def _get_supabase_client() -> Client:
    """Create and return a Supabase client from environment variables."""
    url = os.getenv("SUPABASE_URL")
    key = (
        os.getenv("SUPABASE_API_KEY")
        or os.getenv("SUPABASE_SERVICE_KEY")
        or os.getenv("SUPABASE_KEY")
    )
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set for voicebot")
    return create_client(url, key)


def lookup_company_by_exotel_number(exotel_number: str) -> Optional[Dict[str, Any]]:
    """
    Look up a company by its Exotel phone number.

    Queries the Supabase `companies` table where exotel_number matches.

    Parameters:
    - exotel_number: The Exotel number that was called (the `to` field)

    Returns:
    - Dict with company_id, company_name, bucket_name — or None if not found
    """
    try:
        client = _get_supabase_client()
        response = (
            client.table("companies")
            .select("id, company_name, bucket_name, exotel_number")
            .eq("exotel_number", exotel_number)
            .limit(1)
            .execute()
        )
        if response.data and len(response.data) > 0:
            row = response.data[0]
            return {
                "company_id": row["id"],
                "company_name": row.get("company_name", "Unknown"),
                "bucket_name": row["bucket_name"],
            }
        return None
    except Exception as e:
        logger.error(f"Company lookup failed for {exotel_number}: {e}")
        return None


def save_call_log(
    company_id: str,
    caller_number: str,
    question: str,
    answer: str,
) -> bool:
    """
    Save a call conversation turn to the Supabase `call_logs` table.

    Parameters:
    - company_id: UUID of the company from the companies table
    - caller_number: Farmer's phone number
    - question: Transcribed farmer utterance
    - answer: AI-generated response

    Returns:
    - True if saved successfully, False otherwise
    """
    try:
        client = _get_supabase_client()
        client.table("call_logs").insert(
            {
                "company_id": company_id,
                "caller_number": caller_number,
                "question": question,
                "answer": answer,
                "called_at": datetime.now(timezone.utc).isoformat(),
            }
        ).execute()
        logger.info(f"📞 Call log saved: {caller_number} → company {company_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to save call log: {e}")
        return False


# ---------------------------------------------------------------------------
# Per-call state manager
# ---------------------------------------------------------------------------


class ExotelCallManager:
    """
    Manages state for a single Exotel AgentStream WebSocket session.

    Each incoming call creates one instance that tracks:
    - Caller and called numbers
    - Company info (looked up from Supabase)
    - Audio buffer for accumulating PCM chunks
    - Thread ID for LangGraph conversation persistence
    """

    def __init__(self):
        self.stream_sid: Optional[str] = None
        self.caller_number: Optional[str] = None
        self.called_number: Optional[str] = None
        self.company_id: Optional[str] = None
        self.company_name: Optional[str] = None
        self.bucket_name: Optional[str] = None
        self.thread_id: Optional[str] = None
        self.audio_buffer: bytearray = bytearray()
        self.turn_count: int = 0

    def handle_start(self, data: Dict[str, Any]) -> None:
        """
        Process the 'start' event from Exotel.

        Extracts caller info and looks up the company from Supabase.

        Parameters:
        - data: The full start event payload from Exotel
        """
        start_payload = data.get("start", data)

        self.stream_sid = start_payload.get(
            "streamSid", start_payload.get("stream_sid", "")
        )
        self.caller_number = start_payload.get(
            "from", start_payload.get("caller_number", "unknown")
        )
        self.called_number = start_payload.get(
            "to", start_payload.get("called_number", "unknown")
        )

        # Build thread_id from caller number for conversation persistence
        self.thread_id = f"call_{self.caller_number}"

        logger.info(f"📞 Call started: {self.caller_number} → {self.called_number}")

        # Look up company by Exotel number
        company = lookup_company_by_exotel_number(self.called_number)
        if company:
            self.company_id = company["company_id"]
            self.company_name = company["company_name"]
            self.bucket_name = company["bucket_name"]
            logger.info(
                f"🏢 Company matched: {self.company_name} (bucket: {self.bucket_name})"
            )
        else:
            # Fallback to default bucket from environment
            self.bucket_name = os.getenv("SUPABASE_BUCKET", "openai-bucket")
            logger.warning(
                f"⚠️ No company found for {self.called_number}, using default bucket: {self.bucket_name}"
            )

    def handle_media(self, data: Dict[str, Any]) -> None:
        """
        Process a 'media' event — append base64 PCM audio to the buffer.

        Parameters:
        - data: The media event payload containing base64-encoded audio
        """
        media_payload = data.get("media", {})
        payload_b64 = media_payload.get("payload", "")
        if payload_b64:
            pcm_chunk = base64.b64decode(payload_b64)
            self.audio_buffer.extend(pcm_chunk)

    def get_wav_bytes(self) -> bytes:
        """
        Convert the accumulated PCM buffer to WAV format.

        Returns:
        - WAV audio bytes ready for transcription
        """
        return pcm_to_wav(bytes(self.audio_buffer))

    def reset_buffer(self) -> None:
        """Clear the audio buffer for the next utterance."""
        self.audio_buffer = bytearray()
        self.turn_count += 1

    def save_turn(self, question: str, answer: str) -> None:
        """
        Save this conversation turn to the call_logs table.

        Parameters:
        - question: The transcribed farmer utterance
        - answer: The AI-generated response
        """
        if self.company_id:
            save_call_log(
                company_id=self.company_id,
                caller_number=self.caller_number or "unknown",
                question=question,
                answer=answer,
            )
        else:
            logger.warning("Skipping call log save — no company_id available")
