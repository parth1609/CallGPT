import os
import io
import uuid
import tempfile
import streamlit as st
import streamlit.components.v1 as components
import requests
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage, FunctionMessage
import logging as logger

from app.modules.voice.service import VoiceService

# Optional: pip install audio-recorder-streamlit
try:
    from audio_recorder_streamlit import audio_recorder
    AUDIO_RECORDER_AVAILABLE = True
except ImportError:
    AUDIO_RECORDER_AVAILABLE = False

load_dotenv(override=False)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.modules.pipeline.pipeline import customer, checkpointer, _THREAD_RETRIEVERS, _THREAD_METADATA

st.set_page_config(page_title="CallGPT", page_icon="💬", layout="wide")

# Custom CSS
st.markdown(
    """
<style>
    .big-font {
        font-size:50px !important;
        font-weight: bold;
    }
    .medium-font {
        font-size:20px !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<p class="big-font">💬 CallGPT</p>', unsafe_allow_html=True)
st.markdown('<p class="medium-font">Enterprise RAG System</p>', unsafe_allow_html=True)

st.divider()


def custom_audio_player(audio_bytes: bytes, autoplay: bool = True):
    """Render a compact audio player with tiny play/pause buttons"""
    import base64
    b64 = base64.b64encode(audio_bytes).decode('utf-8')
    autoplay_attr = "autoplay" if autoplay else ""
    html = f"""
        <div style="display: flex; align-items: center; gap: 8px; font-family: sans-serif; margin-top: 5px;">
            <audio id="tts-player" src="data:audio/mp3;base64,{b64}" {autoplay_attr}></audio>
            <button onclick="document.getElementById('tts-player').play()" 
                    style="background: transparent; color: #4CAF50; border: 1px solid #4CAF50; border-radius: 4px; padding: 4px 8px; cursor: pointer; font-size: 14px; transition: 0.2s;">
                ▶ Play
            </button>
            <button onclick="document.getElementById('tts-player').pause()" 
                    style="background: transparent; color: #f44336; border: 1px solid #f44336; border-radius: 4px; padding: 4px 8px; cursor: pointer; font-size: 14px; transition: 0.2s;">
                ⏸ Pause
            </button>
        </div>
    """
    components.html(html, height=40)

 

# Utilities


def load_conversation(graph, thread_id: str) -> list[BaseMessage]:
    """
    Load conversation history from a graph's checkpointer.

    Parameters:
    - graph: The compiled LangGraph application with checkpointer
    - thread_id: The thread ID to load messages from

    Returns:
    - List of BaseMessage objects from the conversation history
    """
    try:
        config = {"configurable": {"thread_id": thread_id}}
        graph_state = graph.get_state(config)
        if graph_state and graph_state.values:
            return list(graph_state.values.get("messages", []))
    except Exception:
        pass
    return []


def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return list(all_threads)


def thread_has_document(thread_id) -> bool:
    return str(thread_id) in _THREAD_RETRIEVERS


def thread_document_metadata(thread_id) -> dict:
    return _THREAD_METADATA.get(str(thread_id), {})



def render_org():
    st.subheader("📄 Organization")
    st.caption("Upload and index your organization's documents")

    # Check API connection
    try:
        health_response = requests.get(
            f"{API_BASE_URL}/api/v1/pipeline/health", timeout=2
        )
        if health_response.status_code == 200:
            st.sidebar.success("✅ API Connected")
        else:
            st.sidebar.warning("⚠️ API Not Responding")
    except:
        st.sidebar.error("❌ API Offline")
        st.sidebar.caption(f"URL: {API_BASE_URL}")

    st.sidebar.subheader("⚙️ Org Configuration")
    bucket_name = st.sidebar.text_input("Bucket/Index Name", value="openai-bucket")
    chunk_size = st.sidebar.slider("Chunk Size", 500, 2000, 1000, 100)
    chunk_overlap = st.sidebar.slider("Chunk Overlap", 0, 500, 200, 50)
    embeddings_model = st.sidebar.text_input(
        "Embeddings Model", value="sentence-transformers/all-MiniLM-L6-v2"
    )
    rebuild = st.sidebar.checkbox("Rebuild Index", value=False)

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a text file to upload",
        type=["txt"],
        help="Upload text documents to be indexed",
    )

    # Display current configuration
    col1, col2 = st.columns([2, 1])
    with col2:
        st.metric("Bucket/Index", bucket_name)
        st.metric("Chunk Size", f"{chunk_size} chars")
        st.metric("Chunk Overlap", f"{chunk_overlap} chars")

    with col1:
        if uploaded_file is not None:
            st.info(f"📄 File: **{uploaded_file.name}** ({uploaded_file.size} bytes)")
            print(uploaded_file.name)
            print(uploaded_file.size)

            if st.button(
                "🚀 Process and Index Document",
                type="primary",
                use_container_width=True,
            ):
                try:
                    # Prepare multipart form data
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "text/plain",
                        )
                    }

                    # Prepare query parameters
                    params = {
                        "bucket_name": bucket_name,
                        "embeddings_model": embeddings_model,
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap,
                    }

                    # Call the pipeline API endpoint
                    with st.spinner("Processing document... This may take a moment."):
                        response = requests.post(
                            f"{API_BASE_URL}/api/v1/pipeline/organisations/upload-file",
                            files=files,
                            params=params,
                            timeout=300,  # 5 minutes timeout for large files
                        )

                    # Check response
                    if response.status_code == 201:
                        result = response.json()

                        # Display results
                        st.success("✅ Document processed and indexed successfully!")

                        with st.expander("📊 Processing Details", expanded=True):
                            st.write(f"**Status:** {result.get('status', 'N/A')}")
                            st.write(f"**Message:** {result.get('message', 'N/A')}")
                            st.write(f"**Filename:** {result.get('filename', 'N/A')}")
                            st.write(
                                f"**Bucket/Index:** {result.get('bucket_name', 'N/A')}"
                            )
                            st.write(
                                f"**Chunks created:** {result.get('chunks_created', 0)}"
                            )

                            if result.get("metadata"):
                                st.write(f"**Metadata:**")
                                st.json(result["metadata"])
                    else:
                        # Handle error response
                        error_detail = response.json().get("detail", "Unknown error")
                        st.error(f"❌ Error processing document: {error_detail}")
                        st.error(f"Status code: {response.status_code}")

                except requests.exceptions.ConnectionError:
                    st.error(
                        "❌ Error: Could not connect to API server. Please ensure the FastAPI server is running."
                    )
                    st.info("💡 Start the server with: `uvicorn app.main:app --reload`")
                except requests.exceptions.Timeout:
                    st.error(
                        "❌ Error: Request timed out. The file might be too large or processing is taking too long."
                    )
                except Exception as e:
                    st.error(f"❌ Error processing document: {str(e)}")
                    st.exception(e)
        else:
            st.warning("👆 Please upload a text file to begin processing")


def render_customer():
    """Customer chat interface using the customer pipeline from pipeline.py"""
    st.subheader("💬 Customer Chat")
    st.caption("Ask questions about your indexed documents")

    # Import customer pipeline and get_thread_history from pipeline.py
    from app.modules.pipeline.pipeline import customer, get_thread_history

    # Initialize customer graph in session state
    if "customer" not in st.session_state:
        st.session_state.customer = customer

    # Initialize thread_id if not present
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())

    # Initialize chat_history if not present
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Flag to track if we've loaded history for this thread
    if "history_loaded_for_thread" not in st.session_state:
        st.session_state.history_loaded_for_thread = None
    
    # Load conversation history from database if not already loaded for this thread
    if st.session_state.history_loaded_for_thread != st.session_state.thread_id:
        try:
            # Try to load previous messages from database
            messages = get_thread_history(st.session_state.thread_id, )
            if messages:
                # Convert to chat_history format
                st.session_state.chat_history = [
                    {"role": "user" if msg["type"] == "User" else "assistant", 
                     "content": msg["content"]}
                    for msg in messages
                ]
                st.info(f"📜 Loaded {len(messages)} previous messages from conversation history")
            # Mark that we've loaded history for this thread
            st.session_state.history_loaded_for_thread = st.session_state.thread_id
        except Exception as e:
            # If loading fails (e.g., new thread with no history), just continue
            logger.debug(f"Could not load history for thread {st.session_state.thread_id}: {e}")
            st.session_state.history_loaded_for_thread = st.session_state.thread_id

    # Sidebar settings
    st.sidebar.subheader("⚙️ Chat Settings")
    bucket_name = st.sidebar.text_input("Bucket/Index Name", value="openai-bucket")

    with st.sidebar.expander("🔧 Advanced Settings", expanded=False):
        embeddings_model = st.text_input(
            "Embeddings Model", value="sentence-transformers/all-MiniLM-L6-v2"
        )
        llm_model = st.text_input("LLM Model", value="openai/gpt-oss-120b")
        temperature = st.slider("Temperature", 0.0, 1.0, 0.5, 0.1)
        k = st.slider("Top-K Results", 1, 10, 4)
        search_type = st.selectbox(
            "Search Type", ["similarity_search", "mmr_search"], index=0
        )

        # Reranking settings
        st.markdown("---")
        st.markdown("**🎯 Reranking (Two-Stage Retrieval)**")
        use_reranker = st.checkbox(
            "Enable Reranking",
            value=False,
            help="Improves accuracy by reranking initial results",
        )
        if use_reranker:
            fetch_k = st.slider(
                "Initial Candidates",
                10,
                50,
                20,
                help="Number of candidates to retrieve before reranking",
            )
            reranker_model = st.selectbox(
                "Reranker Model",
                ["bge-reranker-v2-m3", "bge-reranker-base", "bge-reranker-large"],
                index=0,
            )
        else:
            fetch_k = 20
            reranker_model = "bge-reranker-v2-m3"

    # Voice settings
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎙️ Voice Settings")
    enable_voice = st.sidebar.toggle(
        "Enable Voice Response (TTS)",
        value=True,
    )
    enable_mic = st.sidebar.toggle(
        "Enable Microphone Input (STT)",
        value=True,
    )

    # New conversation button
    if st.sidebar.button(
        "➕ New Conversation", use_container_width=True, type="primary"
    ):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.session_state.history_loaded_for_thread = None  # Reset history loaded flag
        st.rerun()

    st.sidebar.caption(f"Thread ID: {st.session_state.thread_id}")

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    user_input = st.chat_input("Ask a question about your documents")

    # Voice input (microphone)
    if enable_mic:
        if AUDIO_RECORDER_AVAILABLE:
            # Render right above the chat input compactly
            voice_audio_bytes = audio_recorder(
                text="🎙️ Click to speak",
                recording_color="#e74c3c",
                neutral_color="#6c757d",
                icon_size="1x",
            )
            if voice_audio_bytes is not None and len(voice_audio_bytes) > 0 and not user_input:
                with st.spinner("🎙️ Transcribing your voice..."):
                    transcribed_text = VoiceService().transcribe(voice_audio_bytes)
                if transcribed_text:
                    user_input = transcribed_text
                else:
                    st.warning("Could not transcribe audio. Please try again.")
        else:
            st.warning(
                "Install streamlit-audiorecorder for mic input: "
                "`pip install streamlit-audiorecorder`"
            )

    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Prepare state for customer pipeline
        state = {
            "question": user_input,
            "thread_id": st.session_state.thread_id,
            "bucket_name": bucket_name,
            "embeddings_model": embeddings_model,
            "llm_model": llm_model,
            "temperature": temperature,
            "k": k,
            "search_type": search_type,
            "use_reranker": use_reranker,
            "fetch_k": fetch_k,
            "reranker_model": reranker_model,
            "messages": [],  # Will be managed by the pipeline
        }

        # Stream response from customer pipeline
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    placeholder = st.empty()
                    full_response = ""

                    # Stream from customer pipeline with async checkpointer
                    events = st.session_state.customer.stream(
                        state,
                        config={"configurable": {"thread_id": st.session_state.thread_id}},
                        stream_mode="updates",
                    )

                    for event in events:
                        if "answer" in event:
                            chunk = event["answer"]
                            if "messages" in chunk:
                                for msg in chunk["messages"]:
                                    if hasattr(msg, "content") and msg.content:
                                        full_response += msg.content
                                        placeholder.markdown(full_response + "▌")
                            if "answer" in chunk and isinstance(chunk["answer"], str):
                                full_response += chunk["answer"]
                                placeholder.markdown(full_response + "▌")

                    # Display final response
                    placeholder.markdown(full_response)
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": full_response}
                    )

                    # TTS: Generate and play audio response
                    if enable_voice and full_response:
                        with st.spinner("🔊 Generating audio response..."):
                            tts_audio_bytes = VoiceService().speak(full_response)
                            if tts_audio_bytes:
                                custom_audio_player(tts_audio_bytes, autoplay=True)

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.exception(e)


# Sidebar mode selector and renderer
st.sidebar.markdown("---")
mode = st.sidebar.radio("Select Mode", ["Org", "Customer"], index=0)
st.sidebar.markdown("---")

if mode == "Org":
    render_org()
else:
    render_customer()
