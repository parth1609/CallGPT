import os
import hashlib
from typing import Optional, List, Dict, Any
import uuid

import streamlit as st
from dotenv import load_dotenv
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

# Import from new modular structure
from app import pipeline as app_pipeline
from app.modules.document.service import DocumentService
from app.modules.embedding.service import EmbeddingService
from app.modules.vectorstore.service import VectorStoreService

load_dotenv(override=False)

st.set_page_config(page_title="CallGPT", layout="wide", page_icon="💬")

# Custom CSS for ChatGPT-like UI
st.markdown("""
<style>
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #202123;
    }
    
    /* Chat message styling */
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    
    /* Main title */
    h1 {
        font-size: 2rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("💬 CallGPT")

##################### Utilities #####################

# Initialize services
doc_service = DocumentService()
embedding_service = EmbeddingService()
vectorstore_service = VectorStoreService()

def generate_thread_id():
    return uuid.uuid4().hex

def add_thread(thread_id: str) -> None:
    if "chat_threads" not in st.session_state:
        st.session_state["chat_threads"] = []
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)

def reset_chat_ui() -> None:
    tid = generate_thread_id()
    st.session_state["thread_id"] = tid
    add_thread(tid)
    st.session_state["message_history"] = []

def retrieve_all_threads():
    all_threads = set()
    cp = st.session_state.get("checkpointer")
    if not cp:
        return list(all_threads)
    try:
        # SqliteSaver.list returns an iterator of CheckpointTuple
        for checkpoint in cp.list(None):
            tid = checkpoint.config.get('configurable', {}).get('thread_id')
            if tid:
                all_threads.add(tid)
    except Exception:
        pass
    return list(all_threads)

def load_conversation(graph, thread_id: str) -> List[BaseMessage]:
    """Load conversation history from the graph state."""
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = graph.get_state(config)
        if state and state.values:
            return state.values.get("messages", [])
    except Exception:
        pass
    return []

def convert_messages_to_chat_history(messages: List[BaseMessage]) -> List[Dict[str, Any]]:
    """Convert LangChain messages to Streamlit chat history format."""
    history = []
    for m in messages:
        role = "user" if isinstance(m, HumanMessage) else "assistant"
        history.append({"role": role, "content": m.content})
    return history

def get_thread_preview(graph, thread_id: str, max_length: int = 50) -> str:
    """Get a preview of the thread (first user message)."""
    messages = load_conversation(graph, thread_id)
    for m in messages:
        if isinstance(m, HumanMessage):
            content = m.content
            return content[:max_length] + ("..." if len(content) > max_length else "")
    return "New conversation"

def reset_chat(current_threads, current_histories):
    """Create a new chat thread."""
    new_tid = generate_thread_id()
    if new_tid not in current_threads:
        current_threads.append(new_tid)
    if new_tid not in current_histories:
        current_histories[new_tid] = []
    return new_tid, current_threads, current_histories

def docs_from_upload(uploaded_file) -> List[Document]:
    content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    return [Document(page_content=content, metadata={"source": uploaded_file.name})]

def stream_ai_tokens(graph, state, thread_id):
    """Stream AI tokens from the graph."""
    config = {"configurable": {"thread_id": thread_id}}
    
    # Use stream_mode="updates" to get node outputs as they happen
    for event in graph.stream(state, config=config, stream_mode="updates"):
        # event is a dict {node_name: output}
        # Our node_answer yields chunks like {"messages": [AIMessageChunk(...)]}
        # But wait, node_answer is a generator.
        # When a node is a generator, graph.stream yields the values yielded by the node.
        
        # Check if event comes from 'answer' node
        if "answer" in event:
            chunk_data = event["answer"]
            # Check if it has messages
            if "messages" in chunk_data:
                for msg in chunk_data["messages"]:
                    if isinstance(msg, (AIMessage, type(None))) and hasattr(msg, 'content'): # AIMessageChunk inherits AIMessage
                         # In newer LangGraph, it might be AIMessageChunk
                         yield msg.content
                    elif hasattr(msg, 'content'):
                        yield msg.content

##################### Session State #####################

if "vstore" not in st.session_state:
    st.session_state.vstore = None
if "table_name" not in st.session_state:
    st.session_state.table_name = "documents"
if "query_name" not in st.session_state:
    st.session_state.query_name = "match_documents"
if "embeddings_model" not in st.session_state:
    st.session_state.embeddings_model = "sentence-transformers/all-MiniLM-L6-v2"
if "llm_model" not in st.session_state:
    st.session_state.llm_model = "openai/gpt-oss-120b"
 
if "checkpointer" not in st.session_state:
    db_path = os.path.join('db', 'chatbot.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(database=db_path, check_same_thread=False)
    st.session_state.checkpointer = SqliteSaver(conn=conn)
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []
if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = retrieve_all_threads() or []
if "thread_id" not in st.session_state:
    if st.session_state["chat_threads"]:
        # Prefer an existing persisted thread so its messages can be shown immediately
        st.session_state["thread_id"] = st.session_state["chat_threads"][0]
    else:
        # No persisted threads: create a fresh one and add it to the list
        st.session_state["thread_id"] = generate_thread_id()
        st.session_state["chat_threads"].append(st.session_state["thread_id"])
if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = {st.session_state.thread_id: []}

# Ensure chatbot is available to read persisted messages on first load
if "chatbot" not in st.session_state or st.session_state["chatbot"] is None:
    try:
        st.session_state["chatbot"] = app_pipeline.build_rag_graph(checkpointer=st.session_state.checkpointer)
    except Exception:
        st.session_state["chatbot"] = None

# Hydrate the active thread's history from the checkpointer so messages appear after refresh
try:
    if st.session_state.get("chatbot"):
        _msgs = load_conversation(st.session_state["chatbot"], st.session_state["thread_id"])
        _hist = convert_messages_to_chat_history(_msgs)
        st.session_state.chat_histories[st.session_state["thread_id"]] = _hist
except Exception:
    pass

# ============ Sidebar: Conversation History ============
st.sidebar.title("💬 CallGPT")

if st.sidebar.button("➕ New Chat", use_container_width=True, type="primary"):
    new_tid, new_threads, new_histories = reset_chat(
        st.session_state.chat_threads,
        st.session_state.chat_histories,
    )
    st.session_state.thread_id = new_tid
    st.session_state.chat_threads = new_threads
    st.session_state.chat_histories = new_histories
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("📚 My Conversations")

# Display conversations in reverse chronological order (newest first)
for thread_id in st.session_state.chat_threads[::-1]:
    # Get preview for thread
    if st.session_state.get("chatbot"):
        preview = get_thread_preview(st.session_state.chatbot, thread_id, max_length=35)
    else:
        # Fallback if chatbot not ready
        preview = f"Thread {thread_id[:8]}..."
    
    # Highlight active thread
    is_active = (thread_id == st.session_state.thread_id)
    button_type = "primary" if is_active else "secondary"
    
    if st.sidebar.button(
        f"{'🟢 ' if is_active else ''}  {preview}",
        key=f"thread_{thread_id}",
        use_container_width=True,
        type=button_type,
    ):
        if thread_id != st.session_state.thread_id:
            # Switch to this thread
            st.session_state.thread_id = thread_id
            
            # Load conversation from checkpointer if chatbot is ready
            if st.session_state.get("chatbot"):
                messages = load_conversation(st.session_state.chatbot, thread_id)
                chat_history = convert_messages_to_chat_history(messages)
                st.session_state.chat_histories[thread_id] = chat_history
            
            st.rerun()

st.sidebar.divider()

# Sidebar controls
with st.sidebar.expander("⚙️ Settings", expanded=False):
    llm_model = st.text_input("LLM Model", value=st.session_state.llm_model)
    llm_temperature = st.slider("Temperature", 0.0, 1.0, 0.5)
    
    emb_model = st.text_input("Embeddings Model", value=st.session_state.embeddings_model)
    
    search_type = st.radio("Search Type", ["mmr", "similarity"], index=0)
    k = st.slider("Top-K", 1, 10, 4)
    fetch_k = st.slider("Fetch-K (MMR)", 5, 50, 20)
    lambda_mult = st.slider("Lambda (MMR)", 0.0, 1.0, 0.5, 0.05)
    
    table_name = st.text_input("Supabase Table", value=st.session_state.table_name)
    query_name = st.text_input("Supabase RPC (query)", value=st.session_state.query_name)

    # Sync back to session
    st.session_state.llm_model = llm_model
    st.session_state.embeddings_model = emb_model
    st.session_state.table_name = table_name
    st.session_state.query_name = query_name

# File uploader
uploaded = st.file_uploader("Upload a .txt file", type=["txt"]) 

col1, col2 = st.columns([2, 1])
with col1:
    if uploaded is not None:
        st.subheader("Preview")
        preview = uploaded.getvalue().decode("utf-8", errors="ignore")[:800]
        st.code(preview, language="text")

        if st.button("Build / Update Index", type="primary"):
            try:
                docs = docs_from_upload(uploaded)
                
                # Chunking using EmbeddingService
                chunks = []
                for doc in docs:
                    text_chunks = embedding_service.chunk_text(doc.page_content)
                    chunks.extend(text_chunks)
                
                # Generate embeddings
                embeddings, _, _ = embedding_service.generate_embeddings(chunks, model_name=emb_model)
                
                # Upsert to VectorStore (Supabase)
                # Note: VectorStoreService expects chunks as strings, embeddings as list of lists
                vectorstore_service.upsert_vectors(
                    chunks=chunks,
                    embeddings=embeddings,
                    index_name=st.session_state.table_name,
                    metadata=[{"source": uploaded.name} for _ in chunks]
                )
                
                st.session_state.vstore = f"supabase:{st.session_state.table_name}"
                st.session_state.embeddings_model = emb_model or None
                st.session_state.llm_model = llm_model or None

                st.success("Index is ready.")
                
                # Persist the uploaded content to Supabase Storage using DocumentService
                try:
                    file_bytes = uploaded.getvalue()
                    content_full = file_bytes.decode("utf-8", errors="ignore")
                    
                    # Upload document
                    doc_service.upload_document(
                        filename=uploaded.name,
                        content=content_full,
                        metadata={"content_type": "text/plain"}
                    )

                    # Prepare LangGraph chatbot for chat mode
                    st.session_state.chatbot = app_pipeline.build_rag_graph(checkpointer=st.session_state.checkpointer)
                except Exception as persist_e:
                    st.info(f"Saved upload for chat failed (chat still usable without graph): {persist_e}")
            except Exception as e:
                st.error(f"Failed to build index: {e}")

with col2:
    st.subheader("Status")
    st.write("Index:", "Ready" if st.session_state.vstore is not None else "Not built")
    st.write("Table:", st.session_state.table_name)
    st.write("RPC:", st.session_state.query_name)

st.divider()

# Chat UI using session message history keyed by thread_id
tid = st.session_state.get("thread_id")
if tid not in st.session_state.chat_histories:
    st.session_state.chat_histories[tid] = []
st.session_state["message_history"] = st.session_state.chat_histories[tid]

# Render history
for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Type here")

if user_input:
    # Add user message
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Ensure index and chatbot are ready (no local file path required)
    if not st.session_state.get("vstore"):
        st.warning("Please build the index with an uploaded file first.")
    else:
        try:
            base_state = {
                "table_name": st.session_state.get("table_name"),
                "query_name": st.session_state.get("query_name"),
                "rebuild": False,
                "embeddings_model": st.session_state.get("embeddings_model"),
                "llm_model": st.session_state.get("llm_model"),
                "temperature": llm_temperature,
                "search_type": search_type,
                "k": k,
                "fetch_k": fetch_k,
                "lambda_mult": lambda_mult,
                "question": user_input, # Add question to state
            }
            if "chatbot" not in st.session_state or st.session_state["chatbot"] is None:
                st.session_state["chatbot"] = app_pipeline.build_rag_graph(checkpointer=st.session_state.checkpointer)
            
            # Build state with messages
            state = base_state.copy()
            # We don't need to manually build messages list if we use checkpointer, 
            # but we need to pass the new user message.
            # The graph expects 'messages' in state.
            state["messages"] = [HumanMessage(content=user_input)]

            def ai_only_stream():
                yield from stream_ai_tokens(
                    st.session_state["chatbot"],
                    state,
                    st.session_state["thread_id"],
                )

            with st.chat_message("assistant"):
                ai_message = st.write_stream(ai_only_stream())
            st.session_state["message_history"].append({"role": "assistant", "content": ai_message})
            st.session_state.chat_histories[tid] = st.session_state["message_history"]
        except Exception as e:
            st.error(f"Chat failed: {e}")
