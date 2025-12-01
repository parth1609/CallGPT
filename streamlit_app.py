import os
import uuid
import tempfile
import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv(override=False)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

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

    # Check API connection
    try:
        health_response = requests.get(f"{API_BASE_URL}/api/v1/pipeline/health", timeout=2)
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
                    # Prepare multipart form data
                    files = {
                        'file': (uploaded_file.name, uploaded_file.getvalue(), 'text/plain')
                    }
                    
                    # Prepare query parameters
                    params = {
                        'bucket_name': bucket_name,
                        'embeddings_model': embeddings_model,
                        'chunk_size': chunk_size,
                        'chunk_overlap': chunk_overlap,
                    }
                    
                    # Call the pipeline API endpoint
                    with st.spinner("Processing document... This may take a moment."):
                        response = requests.post(
                            f"{API_BASE_URL}/api/v1/pipeline/organisations/upload-file",
                            files=files,
                            params=params,
                            timeout=300  # 5 minutes timeout for large files
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
                            st.write(f"**Bucket/Index:** {result.get('bucket_name', 'N/A')}")
                            st.write(f"**Chunks created:** {result.get('chunks_created', 0)}")
                            
                            if result.get('metadata'):
                                st.write(f"**Metadata:**")
                                st.json(result['metadata'])
                    else:
                        # Handle error response
                        error_detail = response.json().get('detail', 'Unknown error')
                        st.error(f"❌ Error processing document: {error_detail}")
                        st.error(f"Status code: {response.status_code}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("❌ Error: Could not connect to API server. Please ensure the FastAPI server is running.")
                    st.info("💡 Start the server with: `uvicorn app.main:app --reload`")
                except requests.exceptions.Timeout:
                    st.error("❌ Error: Request timed out. The file might be too large or processing is taking too long.")
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
st.info(f"""
**CallGPT** is a Retrieval-Augmented Generation (RAG) system that allows organizations to:
- Index their documents efficiently using LangGraph pipelines
- Enable customers to chat with document collections
- Get accurate, context-aware responses powered by LLMs

**Architecture:** This Streamlit frontend communicates with a FastAPI backend via REST API.

**API Endpoint:** `{API_BASE_URL}`
""")
