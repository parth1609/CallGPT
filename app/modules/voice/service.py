"""
Purpose: Business logic for Voice Service.
Handles Speech-to-Text (STT) and Text-to-Speech (TTS) with multi-language support.

English      → Groq Whisper (STT) + Edge TTS
Hindi/Marathi → Groq Whisper auto-detect (STT) + Edge TTS (regional voice)
               Falls back to Sarvam AI if SARVAM_API_KEY is set.
"""

import os
import asyncio
import base64
import logging
import time
import io
from typing import Optional, Tuple
from dotenv import load_dotenv
from groq import Groq
from pydub import AudioSegment
import requests
import edge_tts

load_dotenv()

logger = logging.getLogger(__name__)

# ── Edge TTS Voice Configuration ──────────────────────────────────────
EDGE_TTS_VOICES = {
    "en": "en-US-AndrewMultilingualNeural",   # English male
    "hi": "hi-IN-MadhurNeural",               # Hindi male
    "mr": "mr-IN-ManoharNeural",              # Marathi male
}
EDGE_TTS_DEFAULT_VOICE = "en-US-AndrewMultilingualNeural"

# ── Sarvam Configuration (Hindi / Marathi — optional) ─────────────────
SARVAM_API_BASE = "https://api.sarvam.ai"
SARVAM_TTS_MODEL = "bulbul:v3"
SARVAM_STT_MODEL = "saaras:v3"
SARVAM_DEFAULT_SPEAKER = "shubh"

# Language code mapping for Sarvam API
SARVAM_LANGUAGE_CODES = {
    "en": "en-IN",
    "hi": "hi-IN",
    "mr": "mr-IN",
}

# Languages handled by Sarvam (when API key is available)
SARVAM_LANGUAGES = {"en", "hi", "mr"}


class VoiceService:
    """Manages voice operations with language-aware routing.

    STT (Speech-to-Text):
    - All languages: Sarvam Saaras v3 STT (auto-detects English, Hindi, and Marathi).
      If SARVAM_API_KEY is missing, falls back to Groq Whisper.

    TTS (Text-to-Speech):
    - English (en): Edge TTS (en-US-AndrewMultilingualNeural)
    - Hindi  (hi): Edge TTS (hi-IN-MadhurNeural) — or Sarvam Bulbul if key set
    - Marathi(mr): Edge TTS (mr-IN-ManoharNeural) — or Sarvam Bulbul if key set
    """

    def __init__(self):
        """Initialize Voice Service with Groq and Sarvam clients."""
        # Groq (fallback for STT)
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY must be set for VoiceService")
        self.groq_client = Groq(api_key=self.groq_api_key)

        # Sarvam (primary STT & optional TTS)
        self.sarvam_api_key = os.getenv("SARVAM_API_KEY")
        if not self.sarvam_api_key:
            logger.warning(
                "⚠️ SARVAM_API_KEY not set — using Groq Whisper as fallback for STT, and Edge TTS for TTS"
            )

    # ──────────────────────────────────────────────────────────────────
    #  STT — Speech to Text
    # ──────────────────────────────────────────────────────────────────

    # Whisper verbose_json returns full names ("English", "Hindi") not
    # ISO codes. Map the common ones we care about.
    _WHISPER_NAME_TO_CODE = {
        "english": "en",
        "hindi": "hi",
        "marathi": "mr",
    }

    # Normalize specific codes to 2-letter ISO codes
    _CODE_TO_ISO = {
        "mr-in": "mr",
        "hi-in": "hi",
        "mr-en": "en",
        "en-in": "en",
        "en-us": "en",
        "en": "en",
        "hi": "hi",
        "mr": "mr",
    }

    @classmethod
    def _normalize_language(cls, raw_lang: str) -> str:
        """Convert a language name or code to a 2-letter ISO code."""
        if not raw_lang:
            return "en"
        lowered = raw_lang.strip().lower()
        if lowered in cls._CODE_TO_ISO:
            return cls._CODE_TO_ISO[lowered]
        if "hi" in lowered:
            return "hi"
        if "mr" in lowered:
            return "mr"
        if len(lowered) <= 3:
            return lowered
        return cls._WHISPER_NAME_TO_CODE.get(lowered, "en")

    def transcribe(
        self, audio_bytes: bytes, language: Optional[str] = None
    ) -> Tuple[Optional[str], str]:
        """
        Transcribe audio bytes to text with language auto-detection.

        Flow:
        - If SARVAM_API_KEY is set: Uses Sarvam STT. If language is None,
          auto-detects English, Hindi, and Marathi.
        - Fallback: Uses Groq Whisper.

        Parameters:
        - audio_bytes (bytes): Raw audio data (WAV, MP3, etc.)
        - language (str, optional): 2-letter ISO language code.
          If None, triggers auto-detect.

        Returns:
        - Tuple of (transcribed_text, detected_language).
          detected_language is a 2-letter ISO 639-1 code ("en", "hi", "mr").
          Returns (None, "en") on failure.
        """
        if self.sarvam_api_key:
            return self._transcribe_sarvam(audio_bytes, language)
        return self._transcribe_groq(audio_bytes, language=language)

    def _transcribe_groq(
        self, audio_bytes: bytes, language: Optional[str] = None
    ) -> Tuple[Optional[str], str]:
        """
        Transcribe using Groq Whisper with optional language auto-detection.

        When language is None, Whisper auto-detects and we extract the
        detected language from the verbose JSON response.
        """
        try:
            if language:
                # Language is known — use standard transcription with ISO code
                transcription = self.groq_client.audio.transcriptions.create(
                    file=("audio.wav", audio_bytes),
                    model="whisper-large-v3-turbo",
                    language=language,
                )
                return (transcription.text, language)
            else:
                # Language unknown — auto-detect via verbose JSON
                transcription = self.groq_client.audio.transcriptions.create(
                    file=("audio.wav", audio_bytes),
                    model="whisper-large-v3-turbo",
                    response_format="verbose_json",
                )
                text = transcription.text
                raw_lang = getattr(transcription, "language", "en") or "en"
                detected_lang = self._normalize_language(raw_lang)
                logger.info(
                    f"🌐 Whisper auto-detected language: '{raw_lang}' → '{detected_lang}'"
                )
                return (text, detected_lang)

        except Exception as e:
            logger.error(f"Groq STT failed: {e}")
            return (None, language or "en")

    def _transcribe_sarvam(
        self, audio_bytes: bytes, language: Optional[str] = None
    ) -> Tuple[Optional[str], str]:
        """Transcribe using Sarvam Saaras v3 with language auto-detection."""
        if not self.sarvam_api_key:
            logger.error("SARVAM_API_KEY not set — cannot transcribe")
            return (None, "en")

        try:
            t_start = time.time()
            # If language is None, use "unknown" to trigger auto-detect
            lang_code = SARVAM_LANGUAGE_CODES.get(language, "unknown") if language else "unknown"

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

            # Extract detected language code if we used "unknown"
            if lang_code == "unknown":
                raw_detected = result.get("language_code", "en-IN") or "en-IN"
                detected_lang = self._normalize_language(raw_detected)
                logger.info(
                    f"🌐 Sarvam auto-detected language: '{raw_detected}' → '{detected_lang}'"
                )
            else:
                detected_lang = language or "en"

            t_elapsed = time.time() - t_start
            logger.info(
                f"✅ Sarvam STT success | lang={detected_lang} | ⏱️ {t_elapsed:.2f}s | Text: '{transcript[:100] if transcript else ''}'"
            )
            return (transcript if transcript else None, detected_lang)

        except Exception as e:
            logger.error(f"❌ Sarvam STT failed: {e}")
            return (None, language or "en")

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

        Routes to Sarvam Bulbul (Hindi/Marathi, if API key set) or Edge TTS.
        Returns 8kHz, 16-bit, Mono raw PCM bytes for Exotel.

        Parameters:
        - text (str): Text to convert to speech.
        - language (str): Language code — "en", "hi", or "mr"
        - voice (str, optional): Voice name override.

        Returns:
        - bytes: RAW PCM bytes, or None on failure.
        """
        if language in SARVAM_LANGUAGES and self.sarvam_api_key:
            return self._speak_sarvam(text, language, voice)
        # Edge TTS is async-native; run it in a new event loop for sync callers
        try:
            return asyncio.get_event_loop().run_until_complete(
                self._speak_edge_tts(text, language, voice)
            )
        except RuntimeError:
            return asyncio.run(self._speak_edge_tts(text, language, voice))

    async def speak_async(
        self,
        text: str,
        language: str = "en",
        voice: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        Async TTS for use in async contexts (e.g. audio_worker).

        Routes to Sarvam Bulbul (Hindi/Marathi, if API key set) or
        Edge TTS (all languages, natively async).

        Parameters:
        - text (str): Text to convert to speech.
        - language (str): Language code — "en", "hi", or "mr"
        - voice (str, optional): Voice name override.

        Returns:
        - bytes: RAW PCM bytes, or None on failure.
        """
        if language in SARVAM_LANGUAGES and self.sarvam_api_key:
            return await asyncio.to_thread(self._speak_sarvam, text, language, voice)
        return await self._speak_edge_tts(text, language, voice)

    async def _speak_edge_tts(
        self, text: str, language: str = "en", voice: Optional[str] = None
    ) -> Optional[bytes]:
        """TTS using Microsoft Edge TTS (free, no API key, async-native).

        Automatically selects the correct voice for the detected language.
        """
        t_tts_start = time.time()
        # Pick voice: explicit override > language-mapped > default
        selected_voice = voice or EDGE_TTS_VOICES.get(language, EDGE_TTS_DEFAULT_VOICE)

        try:
            communicate = edge_tts.Communicate(text, selected_voice)

            # Collect all audio chunks into a buffer
            mp3_buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    mp3_buffer.write(chunk["data"])

            mp3_data = mp3_buffer.getvalue()

            if not mp3_data:
                logger.warning(f"⚠️ Edge TTS returned no audio data (voice={selected_voice})")
                return None

            t_tts = time.time() - t_tts_start
            logger.info(
                f"✅ Edge TTS success | lang={language} | voice={selected_voice} | "
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
