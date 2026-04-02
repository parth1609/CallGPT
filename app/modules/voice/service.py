"""
Purpose: Business logic for Voice Service.
Handles Speech-to-Text (STT) and Text-to-Speech (TTS) using the Groq API.
"""

import os
import sys
import tempfile
import subprocess
import logging
from typing import Optional
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

logger = logging.getLogger(__name__)


class VoiceService:
    """Manages voice operations: STT (Whisper) and TTS (PlayAI) via Groq API"""

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

    def speak(self, text: str) -> Optional[bytes]:
        """
        Convert text to speech using Edge TTS for fast, high-quality, free neural voices.

        Parameters:
        - text (str): Text to convert to speech.

        Returns:
        - bytes: MP3 audio bytes, or None on failure.
        """
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_path = f.name
            
            # Using the edge-tts CLI directly avoiding asyncio conflict in Streamlit
            # en-US-JennyNeural is a high quality female voice natively available in edge-tts
            subprocess.run(
                [sys.executable, "-m", "edge_tts", "--voice", "en-US-JennyNeural", "--text", text, "--write-media", temp_path],
                check=True,
                capture_output=True
            )
            
            with open(temp_path, "rb") as f:
                audio_bytes = f.read()
                
            os.remove(temp_path)
            return audio_bytes
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            return None
