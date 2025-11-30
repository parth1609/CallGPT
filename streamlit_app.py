import os
import uuid
import tempfile
import streamlit as st
from dotenv import load_dotenv
    
from app.modules.document.router import upload_document
from app.pipeline import (
    Organisations,
    customer,
    # generate_thread_id,
    # load_conversation,
    # retrieve_all_threads,
    # thread_document_metadata,
    # thread_has_document,
    )
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.checkpoint.postgres import PostgresSaver

load_dotenv(override=False)

st.set_page_config(
    page_title="CallGPT",
    page_icon="💬",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .big-font {
        font-size:50px !important;
        font-weight: bold;
    }
    .medium-font {
        font-size:20px !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font">💬 CallGPT</p>', unsafe_allow_html=True)
st.markdown('<p class="medium-font">Enterprise RAG System</p>', unsafe_allow_html=True)

st.divider()


# def load_conversation(graph, thread_id: str) -> list[BaseMessage]:

#     try:
#         config = {"configurable": {"thread_id": thread_id}}
#         state = graph.get_state(config)
#         if state and state.values:
#             return state.values.get("messages", [])
#     except Exception:
#         pass
#     return []


def render_org():
    st.subheader("📄 Organization")
    st.caption("Upload and index your organization's documents")

    st.sidebar.subheader("⚙️ Org Configuration")
    bucket_name = st.sidebar.text_input("Bucket/Index Name", value="openai-bucket")
    chunk_size = st.sidebar.slider("Chunk Size", 500, 2000, 1000, 100)
    chunk_overlap = st.sidebar.slider("Chunk Overlap", 0, 500, 200, 50)
    embeddings_model = st.sidebar.text_input("Embeddings Model", value="sentence-transformers/all-MiniLM-L6-v2")
    rebuild = st.sidebar.checkbox("Rebuild Index", value=False)

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a text file to upload", 
        type=['txt'], 
        help="Upload text documents to be indexed"
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
            
            if st.button("🚀 Process and Index Document", type="primary", use_container_width=True):
                try:
                    # Save uploaded file to temporary location
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='wb') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                        print(tmp_file_path)
                    
                    # Build state for the pipeline
                    state = {
                        "bucket_name": bucket_name,
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap,
                        "embeddings_model": embeddings_model,
                        "rebuild": rebuild,
                        "uploaded_file_path": tmp_file_path,
                        "filename": uploaded_file.name,
                        "thread_id": str(uuid.uuid4()),
                    }
                    
                    # Execute the pipeline
                    with st.spinner("Processing document... This may take a moment."):
                        result = Organisations.invoke(state)
                    
                    # Display results
                    st.success("✅ Document processed and indexed successfully!")
                    
                    with st.expander("📊 Processing Details", expanded=True):
                        if "filename" in result:
                            st.write(f"**Filename:** {result['filename']}")
                        if "metadata" in result:
                            st.write(f"**Metadata:** {result['metadata']}")
                        if "chunks" in result:
                            chunks_value = result.get("chunks")
                            chunks_count = len(chunks_value) if chunks_value is not None else 0
                            st.write(f"**Chunks created:** {chunks_count}")
                        if "dimension" in result:
                            st.write(f"**Embedding dimension:** {result['dimension']}")
                    
                    # Clean up temporary file
                    try:
                        os.unlink(tmp_file_path)
                    except:
                        pass
                        
                except Exception as e:
                    st.error(f"❌ Error processing document: {str(e)}")
                    st.exception(e)
        else:
            st.warning("👆 Please upload a text file to begin processing")
    
# def render_customer():
#     st.subheader("💬 Customer Chat")
#     st.caption("Ask questions about your indexed documents")

#     if "checkpointer" not in st.session_state:
#         db_url = os.getenv("DATABASE_URL")
#         if db_url:
#             try:
#                 cp = PostgresSaver.from_conn_string(db_url)
#                 cp.setup()
#                 st.session_state.checkpointer = cp
#             except Exception as e:
#                 st.warning(f"Could not connect to PostgreSQL: {e}")
#                 st.session_state.checkpointer = None
#         else:
#             st.session_state.checkpointer = None

#     # Initialize thread_id if not present
#     if "thread_id" not in st.session_state:
#         st.session_state.thread_id = str(uuid.uuid4())
    
#     # Compile customer graph with checkpointer
#     if "chatbot" not in st.session_state:
#         st.session_state.chatbot = customer_pipeline.compile(checkpointer=st.session_state.checkpointer)
    
#     if "chat_history" not in st.session_state:
#         st.session_state.chat_history = []

#     if st.session_state.chatbot and not st.session_state.chat_history and st.session_state.get("thread_id"):
#         messages = load_conversation(st.session_state.chatbot, st.session_state.thread_id)
#         for msg in messages:
#             role = "user" if isinstance(msg, HumanMessage) else "assistant"
#             if not (hasattr(msg, '__class__') and 'Chunk' in msg.__class__.__name__):
#                 st.session_state.chat_history.append({"role": role, "content": msg.content})

#     st.sidebar.subheader("⚙️ Chat Settings")
#     bucket_name = st.sidebar.text_input("Bucket/Index Name", value="documents")
#     with st.sidebar.expander("🔧 Advanced Settings", expanded=False):
#         temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.1)
#         k = st.slider("Top-K Results", 1, 10, 4)
#         search_type = st.selectbox("Search Type", ["similarity_search", "mmr_search"], index=0)
#         use_defaults = st.checkbox("Use Backend Defaults", value=True)

#     if st.sidebar.button("➕ New Conversation", use_container_width=True, type="primary"):
#         st.session_state.thread_id = str(uuid.uuid4())
#         st.session_state.chat_history = []
#         st.rerun()
#     st.sidebar.caption(f"Thread ID: {st.session_state.thread_id[:8]}...")

#     for message in st.session_state.chat_history:
#         with st.chat_message(message["role"]):
#             st.markdown(message["content"])

#     if user_input := st.chat_input("Ask a question about your documents"):
#         st.session_state.chat_history.append({"role": "user", "content": user_input})
#         with st.chat_message("user"):
#             st.markdown(user_input)

#         if use_defaults:
#             state = {"question": user_input, "thread_id": st.session_state.thread_id, "bucket_name": bucket_name}
#         else:
#             state = {
#                 "question": user_input,
#                 "thread_id": st.session_state.thread_id,
#                 "bucket_name": bucket_name,
#                 "temperature": temperature,
#                 "k": k,
#                 "search_type": search_type,
#             }

#         with st.chat_message("assistant"):
#             with st.spinner("Thinking..."):
#                 try:
#                     placeholder = st.empty()
#                     full_response = ""
#                     for event in st.session_state.chatbot.stream(state, config={"configurable": {"thread_id": st.session_state.thread_id}}, stream_mode="updates"):
#                         if "answer" in event:
#                             chunk = event["answer"]
#                             if "messages" in chunk:
#                                 for msg in chunk["messages"]:
#                                     if hasattr(msg, "content") and msg.content:
#                                         full_response += msg.content
#                                         placeholder.markdown(full_response + "▌")
#                     placeholder.markdown(full_response)
#                     st.session_state.chat_history.append({"role": "assistant", "content": full_response})
#                 except Exception as e:
#                     st.error(f"Error: {e}")
#                     st.exception(e)

# Sidebar mode selector and renderer
st.sidebar.markdown("---")
mode = st.sidebar.radio("Select Mode", ["Org", "Customer"], index=0)
st.sidebar.markdown("---")

# if mode == "Org":
    # render_org()
# else:
#     render_customer()
render_org()

st.divider()

# Info section
st.markdown("### ℹ️ About")
st.info("""
**CallGPT** is a Retrieval-Augmented Generation (RAG) system that allows organizations to:
- Index their documents efficiently
- Enable customers to chat with document collections
- Get accurate, context-aware responses powered by LLMs
""")
