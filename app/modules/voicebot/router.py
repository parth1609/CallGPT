"""
Purpose: FastAPI WebSocket endpoint for Exotel AgentStream integration.

When a farmer calls the Exotel number, Exotel opens a WebSocket to
wss://<server>/voicebot and exchanges JSON events:
  - connected: handshake acknowledged
  - start:     call metadata (from/to numbers)
  - media:     base64-encoded PCM audio chunks (8kHz, 16-bit, mono)
  - stop:      farmer finished speaking → trigger STT → RAG → TTS pipeline

The endpoint keeps the connection open for multi-turn conversation
until the farmer hangs up.
"""

import json
import base64
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.modules.voice.service import VoiceService
from app.modules.pipeline.service import PipelineService
from .service import ExotelCallManager, mp3_to_pcm

logger = logging.getLogger(__name__)

router = APIRouter()

# Default pipeline parameters for voice calls
# (tuned for concise, spoken-style responses)
VOICE_PIPELINE_DEFAULTS = {
    "embeddings_model": "sentence-transformers/all-MiniLM-L6-v2",
    "llm_model": "openai/gpt-oss-120b",
    "temperature": 0.5,
    "k": 4,
    "search_type": "similarity_search",
    "fetch_k": 20,
    "lambda_mult": 0.5,
}


@router.websocket("/voicebot")
async def exotel_voicebot(ws: WebSocket):
    """
    Exotel AgentStream WebSocket endpoint.

    Lifecycle:
    1. Accept WebSocket connection
    2. Receive 'connected' → acknowledge
    3. Receive 'start' → extract caller info, look up company
    4. Receive 'media' → buffer PCM audio
    5. Receive 'stop' → process full pipeline (STT → RAG → TTS)
    6. Send back media event with TTS audio
    7. Repeat 4-6 for multi-turn conversation
    8. WebSocket disconnect → cleanup
    """
    await ws.accept()
    logger.info("🔌 Exotel WebSocket connected")

    # Initialize per-call state and services
    call = ExotelCallManager()
    voice_service = VoiceService()
    pipeline_service = PipelineService()

    try:
        while True:
            # Receive JSON message from Exotel
            raw_message = await ws.receive_text()
            data = json.loads(raw_message)
            event = data.get("event", "")

            # ----------------------------------------------------------
            # EVENT: connected
            # ----------------------------------------------------------
            if event == "connected":
                logger.info("✅ Exotel stream connected (handshake)")

            # ----------------------------------------------------------
            # EVENT: start — extract caller info, look up company
            # ----------------------------------------------------------
            elif event == "start":
                call.handle_start(data)
                logger.info(
                    f"📞 Call setup complete | "
                    f"Caller: {call.caller_number} | "
                    f"Called: {call.called_number} | "
                    f"Bucket: {call.bucket_name} | "
                    f"Thread: {call.thread_id}"
                )

            # ----------------------------------------------------------
            # EVENT: media — accumulate audio chunks
            # ----------------------------------------------------------
            elif event == "media":
                call.handle_media(data)

            # ----------------------------------------------------------
            # EVENT: stop — farmer finished speaking, run full pipeline
            # ----------------------------------------------------------
            elif event == "stop":
                buffer_size = len(call.audio_buffer)
                logger.info(f"🛑 Stop received | Buffer size: {buffer_size} bytes | Turn: {call.turn_count + 1}")

                if buffer_size == 0:
                    logger.warning("Empty audio buffer on stop event — skipping")
                    continue

                # ---- Step 1: PCM → WAV → Transcribe ----
                wav_bytes = call.get_wav_bytes()
                logger.info(f"🎤 Transcribing {len(wav_bytes)} bytes of WAV audio...")

                transcribed_text = voice_service.transcribe(wav_bytes)
                if not transcribed_text or not transcribed_text.strip():
                    logger.warning("Transcription returned empty — skipping pipeline")
                    call.reset_buffer()
                    continue

                logger.info(f"📝 Transcribed: '{transcribed_text[:100]}...'")

                # ---- Step 2: Run RAG pipeline ----
                logger.info(f"🤖 Running pipeline | Bucket: {call.bucket_name} | Question: {transcribed_text[:80]}...")

                try:
                    result = pipeline_service.query_documents(
                        bucket_name=call.bucket_name,
                        question=transcribed_text,
                        thread_id=call.thread_id,
                        **VOICE_PIPELINE_DEFAULTS,
                    )
                    answer_text = result.get("answer", "")
                except Exception as e:
                    logger.error(f"Pipeline error: {e}")
                    answer_text = "I'm sorry, I'm having trouble processing your request right now. Please try again."

                if not answer_text:
                    answer_text = "I'm sorry, I could not find an answer to your question."

                logger.info(f"💬 Answer: '{answer_text[:100]}...'")

                # ---- Step 3: TTS → MP3 → PCM → Base64 ----
                logger.info("🔊 Generating TTS response...")

                mp3_bytes = voice_service.speak(answer_text)
                if mp3_bytes:
                    pcm_response = mp3_to_pcm(mp3_bytes)
                    pcm_b64 = base64.b64encode(pcm_response).decode("utf-8")

                    # Send audio back to Exotel
                    response_event = {
                        "event": "media",
                        "media": {
                            "payload": pcm_b64,
                        },
                    }
                    await ws.send_text(json.dumps(response_event))
                    logger.info(f"📤 Sent {len(pcm_response)} bytes of PCM audio back to Exotel")
                else:
                    logger.error("TTS failed — no audio generated")

                # ---- Step 4: Save call log ----
                call.save_turn(question=transcribed_text, answer=answer_text)

                # ---- Step 5: Reset buffer for next utterance ----
                call.reset_buffer()
                logger.info(f"🔄 Ready for next utterance (turn {call.turn_count})")

            else:
                logger.debug(f"Unknown event type: {event}")

    except WebSocketDisconnect:
        logger.info(
            f"📴 Call ended | Caller: {call.caller_number} | "
            f"Turns: {call.turn_count} | Thread: {call.thread_id}"
        )
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from Exotel: {e}")
    except Exception as e:
        logger.error(f"Voicebot WebSocket error: {e}", exc_info=True)
    finally:
        try:
            await ws.close()
        except Exception:
            pass
        logger.info("🔌 Exotel WebSocket closed")
