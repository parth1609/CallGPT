"""
Purpose: Business logic for Voice Service.
Handles Speech-to-Text (STT) and Text-to-Speech (TTS) using the Groq API.

TTS uses edge_tts as an async library (not subprocess) for minimal latency.
"""

import os
import asyncio
import logging
import time
import io
from typing import Optional
from dotenv import load_dotenv
from groq import Groq
from pydub import AudioSegment
import edge_tts

load_dotenv()

logger = logging.getLogger(__name__)

# Edge TTS voice — fast, natural, conversational
EDGE_TTS_VOICE = "en-US-EmmaNeural"


class VoiceService:
    """Manages voice operations: STT (Whisper) and TTS (edge_tts async library)"""

    def __init__(self):
        """Initialize Voice Service with Groq client."""
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY must be set for VoiceService")
        self.client = Groq(api_key=self.groq_api_key)

    def transcribe(self, audio_bytes: bytes) -> Optional[str]:
        """
        Transcribe audio bytes to text using Groq Whisper API.

        Parameters:
        - audio_bytes (bytes): Raw audio data (WAV, MP3, etc.)

        Returns:
        - str: Transcribed text, or None on failure.
        """
        try:
            # Groq SDK expects a file tuple: (filename, file_bytes)
            transcription = self.client.audio.transcriptions.create(
                file=("audio.wav", audio_bytes),
                model="whisper-large-v3-turbo",
            )
            return transcription.text
        except Exception as e:
            logger.error(f"STT transcription failed: {e}")
            return None

    async def speak_async(self, text: str) -> Optional[bytes]:
        """
        Convert text to speech using edge_tts async library (NO subprocess).
        Returns 8kHz, 16-bit, Mono raw PCM bytes for Exotel.

        Parameters:
        - text (str): Text to convert to speech.

        Returns:
        - bytes: RAW PCM bytes, or None on failure.
        """
        t_tts_start = time.time()

        try:
            # Use edge_tts library directly — no subprocess spawn overhead
            communicate = edge_tts.Communicate(text, EDGE_TTS_VOICE)
            mp3_chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    mp3_chunks.append(chunk["data"])

            if not mp3_chunks:
                logger.warning("⚠️ Edge TTS returned no audio data")
                return None

            audio_data = b"".join(mp3_chunks)
            t_tts = time.time() - t_tts_start
            logger.info(
                f"✅ Edge TTS (async) success | ⏱️ {t_tts:.2f}s | {len(audio_data)} bytes MP3"
            )
        except Exception as e:
            logger.error(f"❌ TTS engine failed: {e}")
            return None

        # Convert MP3 → 8kHz, 16-bit, Mono raw PCM for Exotel
        try:
            t_conv_start = time.time()
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
            audio = audio.set_frame_rate(8000).set_channels(1).set_sample_width(2)

            pcm_buffer = io.BytesIO()
            audio.export(pcm_buffer, format="raw")
            logger.debug(f"⏱️ PCM Conversion: {time.time() - t_conv_start:.2f}s")

            return pcm_buffer.getvalue()
        except Exception as e:
            logger.error(f"❌ PCM conversion failed: {e}")
            return None

    def speak(self, text: str) -> Optional[bytes]:
        """
        Sync wrapper around speak_async for backward compatibility.
        If an event loop is already running, runs in a new thread loop.

        Parameters:
        - text (str): Text to convert to speech.

        Returns:
        - bytes: RAW PCM bytes, or None on failure.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Called from within an async context (e.g. run_in_executor)
            # Create a new event loop in this thread
            new_loop = asyncio.new_event_loop()
            try:
                return new_loop.run_until_complete(self.speak_async(text))
            finally:
                new_loop.close()
        else:
            return asyncio.run(self.speak_async(text))
