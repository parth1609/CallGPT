"""
Purpose: Business logic for Voice Service.
Handles Speech-to-Text (STT) and Text-to-Speech (TTS) with multi-language support.

English  → Groq API  (Whisper STT) + Edge TTS
Hindi/Marathi → Sarvam AI (Saaras v3 STT + Bulbul v3 TTS)
"""

import os
import asyncio
import base64
import logging
import time
import io
from typing import Optional
from dotenv import load_dotenv
from groq import Groq
from pydub import AudioSegment
import requests
import edge_tts

load_dotenv()

logger = logging.getLogger(__name__)

# ── Edge TTS Configuration (English) ──────────────────────────────────
EDGE_TTS_VOICE = "en-US-AndrewMultilingualNeural"  # Natural male voice

# ── Sarvam Configuration (Hindi / Marathi) ────────────────────────────
SARVAM_API_BASE = "https://api.sarvam.ai"
SARVAM_TTS_MODEL = "bulbul:v3"
SARVAM_STT_MODEL = "saaras:v3"
SARVAM_DEFAULT_SPEAKER = "shubh"

# Language code mapping for Sarvam API
SARVAM_LANGUAGE_CODES = {
    "hi": "hi-IN",
    "mr": "mr-IN",
}

# Languages handled by Sarvam (everything else falls through to Edge TTS)
SARVAM_LANGUAGES = {"hi", "mr"}


class VoiceService:
    """Manages voice operations with language-aware routing.

    - English (en): Groq Whisper (STT) + Edge TTS
    - Hindi  (hi): Sarvam Saaras (STT) + Sarvam Bulbul (TTS)
    - Marathi(mr): Sarvam Saaras (STT) + Sarvam Bulbul (TTS)
    """

    def __init__(self):
        """Initialize Voice Service with Groq and Sarvam clients."""
        # Groq (required for STT)
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY must be set for VoiceService")
        self.groq_client = Groq(api_key=self.groq_api_key)

        # Sarvam (required for Hindi/Marathi)
        self.sarvam_api_key = os.getenv("SARVAM_API_KEY")
        if not self.sarvam_api_key:
            logger.warning(
                "⚠️ SARVAM_API_KEY not set — Hindi/Marathi STT/TTS will be unavailable"
            )

    # ──────────────────────────────────────────────────────────────────
    #  STT — Speech to Text
    # ──────────────────────────────────────────────────────────────────

    def transcribe(
        self, audio_bytes: bytes, language: str = "en"
    ) -> Optional[str]:
        """
        Transcribe audio bytes to text.

        Routes to Groq Whisper (English) or Sarvam Saaras (Hindi/Marathi).

        Parameters:
        - audio_bytes (bytes): Raw audio data (WAV, MP3, etc.)
        - language (str): Language code — "en", "hi", or "mr"

        Returns:
        - str: Transcribed text, or None on failure.
        """
        if language in SARVAM_LANGUAGES:
            return self._transcribe_sarvam(audio_bytes, language)
        return self._transcribe_groq(audio_bytes)

    def _transcribe_groq(self, audio_bytes: bytes) -> Optional[str]:
        """Transcribe using Groq Whisper (English)."""
        try:
            transcription = self.groq_client.audio.transcriptions.create(
                file=("audio.wav", audio_bytes),
                model="whisper-large-v3-turbo",
                language="en",
            )
            return transcription.text
        except Exception as e:
            logger.error(f"Groq STT failed: {e}")
            return None

    def _transcribe_sarvam(
        self, audio_bytes: bytes, language: str
    ) -> Optional[str]:
        """Transcribe using Sarvam Saaras v3 (Hindi/Marathi)."""
        if not self.sarvam_api_key:
            logger.error("SARVAM_API_KEY not set — cannot transcribe")
            return None

        try:
            t_start = time.time()
            lang_code = SARVAM_LANGUAGE_CODES.get(language, "hi-IN")

            response = requests.post(
                f"{SARVAM_API_BASE}/speech-to-text",
                headers={"api-subscription-key": self.sarvam_api_key},
                files={"file": ("audio.wav", audio_bytes, "audio/wav")},
                data={
                    "model": SARVAM_STT_MODEL,
                    "language_code": lang_code,
                },
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            transcript = result.get("transcript", "")
            t_elapsed = time.time() - t_start
            logger.info(
                f"✅ Sarvam STT success | lang={language} | ⏱️ {t_elapsed:.2f}s"
            )
            return transcript if transcript else None

        except Exception as e:
            logger.error(f"Sarvam STT failed: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────
    #  TTS — Text to Speech
    # ──────────────────────────────────────────────────────────────────

    def speak(
        self,
        text: str,
        language: str = "en",
        voice: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        Convert text to speech (synchronous).

        Routes to Edge TTS (English) or Sarvam Bulbul (Hindi/Marathi).
        Returns 8kHz, 16-bit, Mono raw PCM bytes for Exotel.

        Parameters:
        - text (str): Text to convert to speech.
        - language (str): Language code — "en", "hi", or "mr"
        - voice (str, optional): Voice name override.

        Returns:
        - bytes: RAW PCM bytes, or None on failure.
        """
        if language in SARVAM_LANGUAGES:
            return self._speak_sarvam(text, language, voice)
        # Edge TTS is async-native; run it in a new event loop for sync callers
        try:
            return asyncio.get_event_loop().run_until_complete(
                self._speak_edge_tts(text, voice)
            )
        except RuntimeError:
            # If there's already a running loop, create a new one in a thread
            return asyncio.run(self._speak_edge_tts(text, voice))

    async def speak_async(
        self,
        text: str,
        language: str = "en",
        voice: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        Async TTS for use in async contexts (e.g. audio_worker).

        Routes to Edge TTS (English, natively async) or Sarvam Bulbul
        (Hindi/Marathi, run in thread pool).

        Parameters:
        - text (str): Text to convert to speech.
        - language (str): Language code — "en", "hi", or "mr"
        - voice (str, optional): Voice name override.

        Returns:
        - bytes: RAW PCM bytes, or None on failure.
        """
        if language in SARVAM_LANGUAGES:
            return await asyncio.to_thread(self._speak_sarvam, text, language, voice)
        return await self._speak_edge_tts(text, voice)

    async def _speak_edge_tts(
        self, text: str, voice: Optional[str] = None
    ) -> Optional[bytes]:
        """TTS using Microsoft Edge TTS (free, no API key, async-native)."""
        t_tts_start = time.time()
        selected_voice = voice or EDGE_TTS_VOICE

        try:
            communicate = edge_tts.Communicate(text, selected_voice)

            # Collect all audio chunks into a buffer
            mp3_buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    mp3_buffer.write(chunk["data"])

            mp3_data = mp3_buffer.getvalue()

            if not mp3_data:
                logger.warning("⚠️ Edge TTS returned no audio data")
                return None

            t_tts = time.time() - t_tts_start
            logger.info(
                f"✅ Edge TTS success | voice={selected_voice} | "
                f"⏱️ {t_tts:.2f}s | {len(mp3_data)} bytes MP3"
            )

            return self._convert_to_pcm(mp3_data, fmt="mp3")

        except Exception as e:
            logger.error(f"❌ Edge TTS failed: {e}")
            return None

    def _speak_sarvam(
        self, text: str, language: str, voice: Optional[str] = None
    ) -> Optional[bytes]:
        """TTS using Sarvam Bulbul v3 (Hindi/Marathi)."""
        if not self.sarvam_api_key:
            logger.error("SARVAM_API_KEY not set — cannot synthesize speech")
            return None

        t_tts_start = time.time()
        selected_voice = voice or SARVAM_DEFAULT_SPEAKER
        lang_code = SARVAM_LANGUAGE_CODES.get(language, "hi-IN")

        try:
            payload = {
                "text": text,
                "target_language_code": lang_code,
                "speaker": selected_voice,
                "model": SARVAM_TTS_MODEL,
            }

            response = requests.post(
                f"{SARVAM_API_BASE}/text-to-speech",
                headers={
                    "api-subscription-key": self.sarvam_api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            # Sarvam returns base64-encoded audio in result["audios"]
            audios = result.get("audios", [])
            if not audios:
                logger.warning("⚠️ Sarvam TTS returned no audio data")
                return None

            # Decode the first audio chunk (base64 → raw bytes)
            audio_b64 = audios[0]
            wav_data = base64.b64decode(audio_b64)

            t_tts = time.time() - t_tts_start
            logger.info(
                f"✅ Sarvam TTS success | lang={language} | voice={selected_voice} | ⏱️ {t_tts:.2f}s | {len(wav_data)} bytes"
            )

        except Exception as e:
            logger.error(f"❌ Sarvam TTS failed: {e}")
            return None

        return self._convert_to_pcm(wav_data, fmt="wav")

    # ──────────────────────────────────────────────────────────────────
    #  Shared Utility
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _convert_to_pcm(audio_data: bytes, fmt: str = "wav") -> Optional[bytes]:
        """Convert audio bytes → 8kHz, 16-bit, Mono raw PCM for Exotel."""
        try:
            t_conv_start = time.time()
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format=fmt)
            audio = audio.set_frame_rate(8000).set_channels(1).set_sample_width(2)

            pcm_buffer = io.BytesIO()
            audio.export(pcm_buffer, format="raw")
            logger.debug(f"⏱️ PCM Conversion: {time.time() - t_conv_start:.2f}s")

            return pcm_buffer.getvalue()
        except Exception as e:
            logger.error(f"❌ PCM conversion failed: {e}")
            return None
