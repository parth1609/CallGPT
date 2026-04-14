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

Performance optimizations:
  - HuggingFace embedding model is pre-loaded once at module import
  - Greeting TTS audio is pre-generated and cached as base64 PCM
  - Greeting is sent immediately on 'start' event to prevent Exotel timeout
"""

import time
import json
import base64
import asyncio
import logging
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.modules.voice.service import VoiceService
from app.modules.embedding.service import EmbeddingService
from app.modules.pipeline.pipeline import customer_pipeline as _customer_graph
from langgraph.checkpoint.memory import MemorySaver
from .service import ExotelCallManager

logger = logging.getLogger(__name__)

# Dedicated thread pool for blocking pipeline / TTS work
executor = ThreadPoolExecutor(max_workers=4)

# Compile the pipeline with MemorySaver for voicebot use.
# PostgreSQL checkpointer is NOT thread-safe when called from run_in_executor,
# so voicebot gets its own in-memory checkpointer.
# Streamlit / API routes continue using the PostgreSQL-backed `customer` graph.
_voicebot_checkpointer = MemorySaver()
_voicebot_pipeline = _customer_graph.compile(checkpointer=_voicebot_checkpointer)


async def safe_send(ws: WebSocket, data: str) -> bool:
    """Send text on the WebSocket only if it is still connected."""
    try:
        if ws.client_state == WebSocketState.CONNECTED:
            await ws.send_text(data)
            return True
    except (RuntimeError, WebSocketDisconnect) as e:
        logger.warning(f"WebSocket already closed: {e}")
    except Exception as e:
        logger.warning(f"WebSocket send failed: {e}")
    return False


# Track sequence numbers per WebSocket session
_sequence_counter = 0


async def send_audio_chunks(ws: WebSocket, pcm_bytes: bytes, stream_sid: str, send_mark: bool = False):
    """
    Split PCM audio into 100ms chunks (3200 bytes min) and send to Exotel.
    Optionally sends a 'mark' event after all audio to signal playback complete.
    """
    global _sequence_counter
    CHUNK_SIZE = 3200  # Exotel minimum: 3.2k (100ms at 8kHz 16-bit mono per spec)
    
    for i in range(0, len(pcm_bytes), CHUNK_SIZE):
        chunk = pcm_bytes[i:i+CHUNK_SIZE]
        # Pad to 320-byte multiple as required by Exotel
        remainder = len(chunk) % 320
        if remainder != 0:
            chunk += b'\x00' * (320 - remainder)
        
        b64_payload = base64.b64encode(chunk).decode("utf-8")
        media_event = {
            "event": "media",
            "stream_sid": stream_sid,
            "media": {
                "payload": b64_payload
            }
        }
        
        sent = await safe_send(ws, json.dumps(media_event))
        if not sent:
            break
            
        # Small delay between chunks for smooth buffering
        await asyncio.sleep(0.01)
    
    # Send mark event after audio to signal Exotel that bot finished speaking
    if send_mark:
        _sequence_counter += 1
        mark_event = {
            "event": "mark",
            "stream_sid": stream_sid,
            "mark": {
                "name": f"bot_response_{_sequence_counter}"
            }
        }
        await safe_send(ws, json.dumps(mark_event))
        logger.info(f"✅ Sent mark event: bot_response_{_sequence_counter}")

router = APIRouter()

# ---------------------------------------------------------------------------
# Startup singletons — loaded ONCE when this module is imported
# ---------------------------------------------------------------------------

# Pre-load the HuggingFace embedding model into memory at import time.
# This avoids the 5-8 second HuggingFace download/load on every call.
logger.info("⏳ Pre-loading HuggingFace embedding model (one-time)...")
_embedding_service = EmbeddingService()
logger.info("✅ Embedding model pre-loaded and cached")

# Greeting text — audio is generated lazily on first call via speak_async().
# We can't pre-generate at import time because edge_tts async conflicts with
# uvicorn's already-running event loop.
GREETING_TEXT = "Hello, welcome. Please ask your question after the beep."
_cached_greeting_pcm_b64: str | None = None
logger.info("ℹ️ Greeting will be generated on first call (lazy async TTS)")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default pipeline parameters for voice calls
VOICE_PIPELINE_DEFAULTS = {
    "embeddings_model": "sentence-transformers/all-MiniLM-L6-v2",
    "llm_model": "llama-3.3-70b-versatile",  # Updated from decommissioned llama3-70b-8192
    "temperature": 0.5,
    "k": 4,
    "search_type": "similarity_search",
    "fetch_k": 20,
    "lambda_mult": 0.5,
}

# Minimum audio buffer size (bytes) to process.
# Below this threshold, the audio is too short to transcribe meaningfully.
# 1000 bytes of 8kHz 16-bit mono PCM ≈ 62ms — not enough for speech.
MIN_BUFFER_SIZE = 1000

# ---------------------------------------------------------------------------
# Voice Activity Detection (VAD) — detects when user stops speaking
# by analyzing actual PCM audio amplitude, NOT by waiting for gaps in
# WebSocket messages (Exotel sends continuous audio even during silence).
# ---------------------------------------------------------------------------

# RMS amplitude threshold: below this = silence, above = speech.
# 8kHz 16-bit PCM: silence ~0-100, background noise ~100-300, speech ~500+
VAD_SPEECH_THRESHOLD = 300

# How long (seconds) of continuous silence after speech to trigger processing.
VAD_SILENCE_DURATION = 1.5

# Overall connection timeout (seconds) for waiting on Exotel messages.
WS_RECEIVE_TIMEOUT = 300


def compute_rms(pcm_bytes: bytes) -> float:
    """Compute RMS (root-mean-square) amplitude of 16-bit PCM audio."""
    import struct
    if len(pcm_bytes) < 2:
        return 0.0
    n_samples = len(pcm_bytes) // 2
    samples = struct.unpack(f'<{n_samples}h', pcm_bytes[:n_samples * 2])
    if not samples:
        return 0.0
    return (sum(s * s for s in samples) / len(samples)) ** 0.5


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@router.websocket("/voicebot")
async def exotel_voicebot(ws: WebSocket):
    """
    Exotel AgentStream WebSocket endpoint.

    Lifecycle:
    1. Accept WebSocket connection
    2. Receive 'connected' → acknowledge
    3. Receive 'start' → extract caller info, look up company, send greeting
    4. Receive 'media' → buffer PCM audio, run VAD
    5. VAD detects end-of-speech (silence after speaking) → process pipeline
    6. Send back media event with TTS audio
    7. Repeat 4-6 for multi-turn conversation
    8. Receive 'stop' OR WebSocket disconnect → cleanup (do NOT process)
    """
    await ws.accept()
    logger.info("🔌 Exotel WebSocket connected")

    # Initialize per-call state and services
    call = ExotelCallManager()
    voice_service = VoiceService()

    is_processing = False

    # VAD state tracking
    has_spoken = False          # True once we detect speech in this turn
    last_speech_time = 0.0      # Timestamp of last speech-detected chunk
    vad_triggered = False       # Prevent double-triggering

    async def process_speech():
        """
        Process speech in a streaming fashion:
        1. Transcribe the audio buffer.
        2. Stream the RAG pipeline.
        3. Break the AI response into sentences.
        4. Synthesize and send each sentence as it's generated (Low Latency).
        """
        nonlocal is_processing, has_spoken, vad_triggered
        if is_processing or len(call.audio_buffer) < MIN_BUFFER_SIZE:
            return

        is_processing = True
        full_answer = []
        transcribed_text = ""
        try:
            # 1. Clear any pending audio on Exotel's side
            clear_event = {"event": "clear", "stream_sid": call.stream_sid}
            await safe_send(ws, json.dumps(clear_event))
            logger.info("📡 Sent 'clear' event to Exotel")

            # 2. Transcribe (STT)
            t_start = time.time()
            wav_bytes = call.get_wav_bytes()
            logger.info(f"🎤 Transcribing {len(wav_bytes)} bytes...")
            transcribed_text = await asyncio.get_event_loop().run_in_executor(
                executor, voice_service.transcribe, wav_bytes
            )
            t_stt = time.time() - t_start
            logger.info(f"⏱️ STT duration: {t_stt:.2f}s | Text: '{transcribed_text[:100]}'")

            if not transcribed_text or not transcribed_text.strip():
                call.reset_buffer()
                return

            # 3. Setup Streaming Pipeline & Audio Worker
            t_rag_start = time.time()
            sentence_queue = asyncio.Queue()

            async def audio_worker():
                """Background worker to synthesize and send audio for each sentence in order."""
                while True:
                    try:
                        sentence = await sentence_queue.get()
                        if sentence is None: # Exit sentinel
                            break
                        
                        if not sentence.strip():
                            sentence_queue.task_done()
                            continue

                        logger.info(f"🔊 Synthesizing: '{sentence[:50]}...'")
                        # Use async TTS directly — no executor/thread overhead
                        pcm_data = await voice_service.speak_async(sentence)
                        
                        if pcm_data:
                            logger.info(f"📤 Streaming PCM response in chunks | Size: {len(pcm_data)} bytes")
                            await send_audio_chunks(ws, pcm_data, call.stream_sid)
                            logger.info(f"📤 Finished sending PCM chunks | Latency from start: {time.time() - t_start:.2f}s")
                        
                        sentence_queue.task_done()
                    except Exception as e:
                        logger.error(f"Error in audio_worker: {e}")
                        sentence_queue.task_done()

            # 4. Stream the pipeline
            worker_task = asyncio.create_task(audio_worker())
            
            try:
                state = {
                    "question": transcribed_text,
                    "bucket_name": call.bucket_name,
                    "thread_id": call.thread_id,
                    "messages": [],
                    **VOICE_PIPELINE_DEFAULTS,
                }
                config = {"configurable": {"thread_id": call.thread_id}}
                
                buffer = ""
                async for chunk in _voicebot_pipeline.astream(state, config, stream_mode="messages"):
                    # Only process AI response chunks — skip HumanMessage/SystemMessage
                    if isinstance(chunk, tuple) and len(chunk) > 1:
                        msg = chunk[0]
                        # Filter: only AIMessageChunk has the AI's streaming response
                        msg_type = type(msg).__name__
                        if "AIMessage" not in msg_type:
                            continue
                        if hasattr(msg, "content") and msg.content:
                            content = msg.content
                            buffer += content
                            full_answer.append(content)
                            
                            # Trigger sentence when punctuation or buffer length is reached
                            if any(p in content for p in [".", "?", "!", "\n"]) or len(buffer) > 40:
                                if buffer.strip():
                                    await sentence_queue.put(buffer.strip())
                                    buffer = ""

                # Push remaining buffer
                if buffer.strip():
                    await sentence_queue.put(buffer.strip())
            finally:
                # Signal worker to exit and wait for it
                await sentence_queue.put(None)
                await worker_task

            t_total = time.time() - t_start
            logger.info(f"⏱️ Total Interaction duration: {t_total:.2f}s")

            # Send mark event AFTER all audio to tell Exotel bot finished speaking
            await send_audio_chunks(ws, b"", call.stream_sid, send_mark=True)

        except Exception as e:
            logger.error(f"Streaming pipeline error: {e}", exc_info=True)
            # Fallback error message
            try:
                await sentence_queue.put("I am sorry, I encountered an error. Please try again.")
                await sentence_queue.put(None)
                await worker_task
            except:
                pass
        finally:
            # 5. Cleanup
            is_processing = False
            final_text = "".join(full_answer)
            call.save_turn(question=transcribed_text, answer=final_text)
            call.reset_buffer()
            has_spoken = False
            vad_triggered = False
            logger.info(f"🔄 Ready for next utterance (turn {call.turn_count})")

    try:
        while True:
            # Check if WebSocket is still alive
            if ws.client_state != WebSocketState.CONNECTED or ws.application_state == WebSocketState.DISCONNECTED:
                logger.warning("WebSocket no longer connected — exiting loop")
                break

            # Receive next message — use a generous timeout since Exotel
            # sends continuous audio (VAD handles silence detection instead).
            try:
                raw_message = await asyncio.wait_for(
                    ws.receive_text(), timeout=WS_RECEIVE_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.warning(f"⏰ No message for {WS_RECEIVE_TIMEOUT}s — closing")
                break
            except RuntimeError as e:
                logger.warning(f"WebSocket interface error: {e}. Session ending.")
                break

            data = json.loads(raw_message)
            event = data.get("event", "")

            # ----------------------------------------------------------
            # EVENT: connected
            # ----------------------------------------------------------
            if event == "connected":
                logger.info("✅ Exotel stream connected (handshake)")

            # ----------------------------------------------------------
            # EVENT: start — extract caller info, look up company,
            #                send cached greeting immediately
            # ----------------------------------------------------------
            elif event == "start":
                call.handle_start(data)
                # Debug: log the stream_sid so we can verify it's correct
                logger.info(
                    f"📞 Call setup complete | "
                    f"stream_sid: '{call.stream_sid}' | "
                    f"Caller: {call.caller_number} | "
                    f"Called: {call.called_number} | "
                    f"Bucket: {call.bucket_name} | "
                    f"Thread: {call.thread_id}"
                )

                # If stream_sid is missing, try extracting from top-level data
                if not call.stream_sid:
                    call.stream_sid = data.get("stream_sid", data.get("streamSid", ""))
                    logger.warning(f"⚠️ stream_sid was empty, retried from top-level: '{call.stream_sid}'")

                # Generate greeting on first call if not cached yet
                global _cached_greeting_pcm_b64
                if not _cached_greeting_pcm_b64:
                    logger.info("⏳ Generating greeting audio (first call — async TTS)...")
                    try:
                        greeting_pcm_raw = await voice_service.speak_async(GREETING_TEXT)
                        if greeting_pcm_raw:
                            _cached_greeting_pcm_b64 = base64.b64encode(greeting_pcm_raw).decode("utf-8")
                            logger.info(f"✅ Greeting audio cached ({len(greeting_pcm_raw)} bytes PCM)")
                        else:
                            logger.warning("⚠️ Greeting TTS returned no audio")
                    except Exception as e:
                        logger.error(f"⚠️ Greeting TTS failed: {e}")

                # Send greeting
                if _cached_greeting_pcm_b64 and call.stream_sid:
                    greeting_pcm = base64.b64decode(_cached_greeting_pcm_b64)
                    logger.info(f"👋 Sending greeting audio | {len(greeting_pcm)} bytes PCM")
                    await send_audio_chunks(ws, greeting_pcm, call.stream_sid, send_mark=True)
                    logger.info("👋 Finished sending greeting audio + mark")
                elif not call.stream_sid:
                    logger.warning("⚠️ No stream_sid — cannot send greeting")

            # ----------------------------------------------------------
            # EVENT: media — accumulate audio + VAD silence detection
            # ----------------------------------------------------------
            elif event == "media":
                call.handle_media(data)

                # VAD: Analyze the PCM audio to detect speech vs silence
                if not is_processing and not vad_triggered:
                    media_payload = data.get("media", {})
                    payload_b64 = media_payload.get("payload", "")
                    if payload_b64:
                        pcm_chunk = base64.b64decode(payload_b64)
                        rms = compute_rms(pcm_chunk)

                        if rms > VAD_SPEECH_THRESHOLD:
                            # User is speaking
                            has_spoken = True
                            last_speech_time = time.time()
                        elif has_spoken and last_speech_time > 0:
                            # User was speaking but this chunk is silent
                            silence_duration = time.time() - last_speech_time
                            if silence_duration >= VAD_SILENCE_DURATION:
                                # End of speech detected!
                                logger.info(
                                    f"🎤 VAD: Speech ended after {silence_duration:.1f}s silence "
                                    f"(buffer: {len(call.audio_buffer)} bytes, "
                                    f"RMS: {rms:.0f} < threshold {VAD_SPEECH_THRESHOLD})"
                                )
                                vad_triggered = True
                                asyncio.create_task(process_speech())

            # ----------------------------------------------------------
            # EVENT: stop — call/stream is ENDING (NOT "user stopped speaking")
            # Do NOT process speech here — the call is over.
            # ----------------------------------------------------------
            elif event == "stop":
                reason = data.get("stop", {}).get("reason", "unknown")
                logger.info(f"🛑 Stop received — call/stream ending (reason: {reason})")
                break  # Exit the loop — the call is over

            # ----------------------------------------------------------
            # EVENT: mark — playback confirmation from Exotel
            # ----------------------------------------------------------
            elif event == "mark":
                mark_name = data.get("mark", {}).get("name", "unknown")
                logger.info(f"📍 Mark confirmation received: {mark_name}")

            # ----------------------------------------------------------
            # EVENT: dtmf — handle digits
            # ----------------------------------------------------------
            elif event == "dtmf":
                digit = data.get("dtmf", {}).get("digit")
                logger.info(f"🔢 DTMF received: {digit}")

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


