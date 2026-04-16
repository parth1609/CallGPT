import os
import time
import logging

# Force HuggingFace offline mode BEFORE any transformers/sentence-transformers imports.
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["SENTENCE_TRANSFORMERS_HOME"] = "./models_cache"

from fileinput import filename
from typing import Any, Dict, List, Optional, TypedDict
from typing import Annotated, Sequence

from langgraph.graph import StateGraph, START, END
from langchain_core.documents import Document
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, AIMessageChunk
from torch.nn import Embedding

# Import utility functions from modules (backend pattern)
from app.modules.embedding.service import get_embedding_model, EmbeddingService
from app.modules.llm.service import get_groq_llm, get_qa_prompt, get_llm_service, LLMService
from app.modules.document.service import (
    chunk_documents,
    load_text_file,
    DocumentService,
)
from app.modules.retrieval.service import get_retrieval_service, RetrievalService
from app.modules.conversation.service import ConversationService
from app.modules.vectorstore.service import VectorStoreService

import logging

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


from dotenv import load_dotenv
import uuid
from langgraph.checkpoint.postgres import PostgresSaver

load_dotenv()

# Global variables for checkpointer and thread tracking
# Initialize PostgreSQL checkpointer for conversation persistence
DB_URI = os.getenv("DATABASE_URL")

if DB_URI:
    try:
        # Fix for "prepared statement already exists" error
        # We need to create a connection pool with prepare_threshold=None to disable prepared statements
        # This is necessary when using PostgresSaver to avoid conflicts
        from psycopg_pool import ConnectionPool
        
        # Create connection pool with prepare_threshold=None to disable prepared statements
        pool = ConnectionPool(
            conninfo=DB_URI,
            max_size=10,
            kwargs={
                "autocommit": True,
                "prepare_threshold": None,  # Disable prepared statements to avoid conflicts
            },
            open=True
        )
        
        # Create PostgresSaver with the connection pool
        checkpointer = PostgresSaver(pool)
        checkpointer.setup()  # Initialize the required database tables
        logger.info("✅ PostgreSQL checkpointer initialized successfully (prepared statements disabled)")
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize PostgreSQL checkpointer: {e}")
        logger.warning("Conversations will not be persisted to database")
        checkpointer = None
else:
    logger.warning("⚠️ DATABASE_URL not found. Checkpointer disabled.")
    logger.warning("Set DATABASE_URL in .env to enable conversation persistence")
    checkpointer = None

# Thread-specific storage for retrievers and metadata
_THREAD_RETRIEVERS = {}
_THREAD_METADATA = {}


def get_thread_history(thread_id: str, db_uri: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve the full conversation history for a specific thread from PostgreSQL checkpointer.
    
    This is a convenience wrapper around ConversationService.get_thread_history that uses
    the global checkpointer instance.
    
    Parameters:
    - thread_id: The specific thread ID to retrieve history for
    - db_uri: PostgreSQL connection string (defaults to DATABASE_URL env variable)
    
    Returns:
    - List of message dictionaries with 'type' and 'content' keys
    
    Example:
        messages = get_thread_history("your_thread_id")
        for msg in messages:
            print(f"{msg['type']}: {msg['content']}")
    """
    from app.modules.conversation.service import ConversationService
    
    # Use global checkpointer if available and no custom db_uri provided
    if checkpointer is not None and db_uri is None:
        return ConversationService.get_thread_history(thread_id, checkpointer_instance=checkpointer)
    else:
        return ConversationService.get_thread_history(thread_id, db_uri=db_uri)



class RAGState(TypedDict, total=False):
    # Inputs / config
    table_name: str
    query_name: str
    rebuild: bool

    # Document
    filename: str
    content: Optional[str] = None
    uploaded_file_path: Optional[str]  # Path to uploaded file for processing
    # input_path: str
    metadata: str = None

    # Supabase
    bucket_name: str  # same for pinecone-index name

    # Embedding
    chunks: List[Document]
    embeddings: List[list]
    chunk_size: Optional[int]
    chunk_overlap: Optional[int]
    embeddings_model: str

    # llm
    temperature: float
    template: str
    question: str

    # retrieva
    search_type: str
    k: int
    fetch_k: int
    lambda_mult: float

    # Reranking (two-stage retrieval)
    use_reranker: bool
    reranker_model: str

    # Conversational memory (accumulated across turns via checkpointer)
    messages: Annotated[Sequence[BaseMessage], add_messages]
    thread_id: Optional[str]  # Thread identifier for conversation tracking

    answer: str



#  LangGraph Nodes


def document_service_node(state: RAGState) -> Dict[str, Any]:
    """
    Load and process document from uploaded file.
    Expects 'uploaded_file_path' in state.
    """
    # Get the uploaded file path from state
    uploaded_file = state.get("uploaded_file_path")
    if not uploaded_file:
        raise ValueError("No uploaded_file_path provided in state")

    # Initiate the service
    doc_service = DocumentService(bucket_name=state.get("bucket_name"))

    # Load the file
    docs = load_text_file(uploaded_file)
    if not docs:
        raise ValueError("No content loaded from file")
    file = docs[0]

    # Prefer original filename from state
    original_filename = state.get("filename")

    # Upload to Supabase (handles bucket creation internally if needed)
    upload_result = doc_service.upload_document(
        filename=original_filename,
        content=file.page_content,
        metadata=file.metadata,
    )

    return {
        "content": file.page_content,
        "metadata": upload_result,
        "filename": original_filename,
    }


def embedding_node(state: RAGState):
    """
    Chunk the document content and generate embeddings.
    Returns chunks as Document objects, embeddings, and dimension.
    """
    Embedding_Service = EmbeddingService()

    embedding_model = state.get("embeddings_model")
    content = state.get("content")

    # Validate content exists
    if not content:
        raise ValueError("No content available to chunk and embed")

    # Unpack the tuple returned by chunk_and_embed
    # Returns: (chunks, embeddings, model_name, total_chunks)
    try:
        chunks_text = Embedding_Service.chunk_text(text=state.get("content"))
        all_embeddings, _, dimension = Embedding_Service.generate_embeddings(
            texts=chunks_text, model_name=embedding_model
        )
    except Exception as e:
        raise ValueError(f"Failed to chunk and embed content: {str(e)}")

    # Validate embeddings
    if not all_embeddings or all_embeddings is None:
        raise ValueError("Embedding generation failed - no embeddings returned")

    if not chunks_text or chunks_text is None:
        raise ValueError("Text chunking failed - no chunks returned")

    # Convert text chunks to Document objects for vectorstore compatibility
    from langchain_core.documents import Document

    chunks_docs = [Document(page_content=chunk) for chunk in chunks_text]

    # Debug: show sizes produced by embedding node
    print(
        f"DEBUG embedding_node: chunks={len(chunks_docs)}, embeddings={len(all_embeddings)}, dim={dimension}"
    )

    return {
        "chunks": chunks_docs,  # Return as Document objects
        "embeddings": all_embeddings,
        "dimension": dimension,
    }


def node_vectorstore(state: RAGState) -> Dict[str, Any]:
    """Upsert chunks to Pinecone vector store when rebuild is requested"""
    # Pinecone-only: upsert when explicitly requested via rebuild
    vstore = VectorStoreService()
    idx = state.get("bucket_name").lower()

    # Extract chunks and embeddings from state
    chunks = state.get("chunks")
    embeddings = state.get("embeddings")
    print(
        f"DEBUG node_vectorstore: chunks={None if chunks is None else len(chunks)}, embeddings={None if embeddings is None else len(embeddings)}"
    )
    if chunks is None or embeddings is None:
        raise ValueError(
            "Vectorstore node requires chunks and embeddings to be present in state"
        )

    # Extract text content from chunks for upsert_vectors
    chunks_text = [chunk.page_content for chunk in chunks]

    # Prepare per-chunk metadata list if metadata is present
    raw_metadata = state.get("metadata") or {}
    metadata_list = [raw_metadata] * len(chunks_text) if raw_metadata else None

    # Ensure index exists before upserting
    if embeddings and len(embeddings) > 0:
        dimension = len(embeddings[0])
        print(f"DEBUG: Ensuring index '{idx}' exists with dimension={dimension}")
        try:
            vstore._ensure_index(idx, dimension)
            print(f"✅ Index '{idx}' ready for upsert")
        except Exception as e:
            print(f"⚠️ Warning: Could not ensure index: {str(e)}")
            # Continue anyway - might exist but check failed

    vstore.upsert_vectors(
        chunks=chunks_text,
        embeddings=embeddings,
        index_name=idx,
        metadata=metadata_list,
    )
    return {}


def node_answer(state: RAGState):
    """Retrieve documents and generate answer with streaming from pinecone vector store"""
    logger.debug("=" * 80)
    logger.debug("NODE: answer - Starting")
    logger.debug(
        f"INPUT STATE: bucket_name={state.get('bucket_name')}, question={state.get('question')[:50] if state.get('question') else None}..."
    )
    logger.debug(
        f"INPUT STATE: embeddings_model={state.get('embeddings_model')}, llm_model={state.get('llm_model')}"
    )
    logger.debug(
        f"INPUT STATE: search_type={state.get('search_type')}, k={state.get('k')}"
    )

    # Get index name and ensure it exists
    index_name = state.get("bucket_name").lower()
    logger.debug(f"STEP 0: Ensuring index '{index_name}' exists")

    # Use VectorStoreService to ensure index exists (it has _ensure_index method)
    # Get dimension based on embedding model
    embeddings_model = state.get(
        "embeddings_model", "sentence-transformers/all-MiniLM-L6-v2"
    )
    if "all-MiniLM-L6-v2" in embeddings_model:
        dimension = 384
    else:
        dimension = 384  # Default

    logger.debug(f"STEP 0a: Index dimension={dimension} for model={embeddings_model}")

    try:
        # Create temporary VectorStoreService instance to ensure index
        vector_service = VectorStoreService()
        vector_service._ensure_index(index_name, dimension)
        logger.debug(f"STEP 0 OUTPUT: Index '{index_name}' ready")
    except Exception as e:
        logger.warning(f"STEP 0 WARNING: Could not ensure index: {str(e)}")
        # Continue anyway - index might exist but check failed

    # Retrieval service (Module-level singleton to avoid 2-3s setup)
    retriever_service = get_retrieval_service(index_name=index_name)
    
    # LLM Service (Module-level singleton)
    llm_service = get_llm_service()

    query = state.get("question")
    logger.debug(f"STEP 3: Query extracted: {query[:100] if query else None}...")

    # Get query embedding (Cached model)
    logger.debug("STEP 4: Getting query embedding")
    t_embed_start = time.time()
    query_embedding = retriever_service._get_query_embedding(
        query, model_name=state.get("embeddings_model")
    )
    t_embed = time.time() - t_embed_start
    logger.debug(
        f"STEP 4 OUTPUT: Query embedding dimension={len(query_embedding) if query_embedding else 0} | ⏱️ {t_embed:.2f}s"
    )

    # Get QA prompt template
    logger.debug("STEP 5: Getting QA prompt template")
    prompt = get_qa_prompt()

    # Perform search based on search_type
    # Force search_type=similarity_search and use_reranker=False for sub-3s voicebot speed
    search_type = "similarity_search"
    use_reranker = False
    
    # Use k=4 for a more detailed context while still remaining fast
    k = 4
    
    logger.debug(f"STEP 6: Performing {search_type}, use_reranker={use_reranker}, k={k}")

    if search_type == "similarity_search":
        t_search_start = time.time()
        search_results = retriever_service.similarity_search(
            query=query,
            k=k,
            embedding_model=state.get("embeddings_model"),
            use_reranker=use_reranker,
        )
        t_search = time.time() - t_search_start
        logger.debug(f"STEP 6a OUTPUT: Found {len(search_results)} results | ⏱️ {t_search:.2f}s")
    elif search_type == "mmr_search":
        logger.debug(
            f"STEP 6b: mmr_search with k={state.get('k', 4)}, fetch_k={state.get('fetch_k', 20)}"
        )
        search_results = retriever_service.mmr_search(
            text_query=query,
            k=state.get("k", 4),
            fetch_k=state.get("fetch_k", 20),
            lambda_mult=state.get("lambda_mult", 0.5),
            embedding_model=state.get("embeddings_model"),
        )
        logger.debug(f"STEP 6b OUTPUT: Found {len(search_results)} results")
    else:
        logger.warning(
            f"Unknown search_type: {search_type}, defaulting to similarity_search"
        )
        search_results = retriever_service.similarity_search(
            query=query,
            k=state.get("k", 4),
            embedding_model=state.get("embeddings_model"),
            use_reranker=use_reranker,
            fetch_k=state.get("fetch_k", 20),
            reranker_model=state.get("reranker_model", "bge-reranker-v2-m3"),
        )

    # Convert search results to Document objects
    logger.debug("STEP 7: Converting search results to Document objects")
    from langchain_core.documents import Document

    docs = [
        Document(
            page_content=result.get("content", ""), metadata=result.get("metadata", {})
        )
        for result in search_results
    ]
    logger.debug(f"STEP 7 OUTPUT: Created {len(docs)} Document objects")

    # Prepare context from documents (with deduplication)
    logger.debug("STEP 8: Preparing context from retrieved documents")
    seen_content = set()
    unique_docs = []
    for d in docs:
        if d.page_content not in seen_content:
            unique_docs.append(d.page_content)
            seen_content.add(d.page_content)
    
    context = "\n\n".join(unique_docs)
    logger.debug(f"STEP 8 OUTPUT: Context length={len(context)} characters (deduplicated)")

    # Create the full message list
    logger.debug("STEP 9: Building message history")
    history = list(state.get("messages", []))
    logger.debug(f"STEP 9a: History has {len(history)} messages")

    current = prompt.format_messages(context=context, question=state.get("question"))
    logger.debug(f"STEP 9b: Current prompt has {len(current)} messages")

    messages = [*history, *current]
    logger.debug(f"STEP 9 OUTPUT: Total messages={len(messages)}")

    # Convert LangChain messages to dict format for LLMService
    logger.debug("STEP 10: Converting messages to dict format")
    messages_dict = []
    for msg in messages:
        if hasattr(msg, "type") and hasattr(msg, "content"):
            # Map LangChain message types to role
            role_mapping = {
                "system": "system",
                "human": "user",
                "ai": "assistant",
            }
            role = role_mapping.get(msg.type, "user")
            messages_dict.append({"role": role, "content": msg.content})
    logger.debug(f"STEP 10 OUTPUT: Converted {len(messages_dict)} messages")

    # Stream tokens and yield AI message chunks for smoother UI
    logger.debug(
        f"STEP 11: Starting LLM streaming with model={state.get('llm_model', 'llama-3.3-70b-versatile')}"
    )
    t_llm_start = time.time()
    t_first_token = None
    answer_accum = ""
    chunk_count = 0
    for chunk in llm_service.stream_chat(
        messages=messages_dict,
        model=state.get("llm_model", "llama-3.3-70b-versatile"),
        temperature=state.get("temperature", 0.5),
    ):
        if t_first_token is None:
            t_first_token = time.time() - t_llm_start
            logger.debug(f"⏱️ Time to first token: {t_first_token:.2f}s")

        delta = chunk.get("content", "")
        if not delta:
            continue
        answer_accum += delta
        chunk_count += 1
        # Emit incremental assistant chunks via the messages channel
        yield {"messages": [AIMessageChunk(content=delta)]}

    t_llm_total = time.time() - t_llm_start
    logger.debug(
        f"STEP 11 OUTPUT: Streamed {chunk_count} chunks, total answer length={len(answer_accum)} | ⏱️ Total LLM duration: {t_llm_total:.2f}s"
    )

    # Finalize: return full answer and persist the turn into memory
    logger.debug("STEP 12: Finalizing answer and updating messages")
    final_output = {
        "answer": answer_accum,
        "messages": [
            HumanMessage(content=state["question"]),
            AIMessage(content=answer_accum),
        ],
    }
    logger.debug(f"STEP 12 OUTPUT: Final answer length={len(answer_accum)}")
    logger.debug("NODE: answer - Complete")
    logger.debug("=" * 80)
    yield final_output



# Organisaton graph
"""
Graph Flow:
START -> document_load -> embedding -> vectorstore -> END
 """
Orgs_pipeline = StateGraph(RAGState)
Orgs_pipeline.add_node("document_load", document_service_node)
Orgs_pipeline.add_node("embedding", embedding_node)
Orgs_pipeline.add_node("vectorstore", node_vectorstore)

Orgs_pipeline.add_edge(START, "document_load")
Orgs_pipeline.add_edge("document_load", "embedding")
Orgs_pipeline.add_edge("embedding", "vectorstore")
Orgs_pipeline.add_edge("vectorstore", END)


Organisations = Orgs_pipeline.compile()


"""
Graph Flow:
START  → answer → save_conversation → END
"""
customer_pipeline = StateGraph(RAGState)

# Add nodes
customer_pipeline.add_node("answer", node_answer)
# customer_pipeline.add_node("save_conversation", node_save_conversation)

# Build flow
customer_pipeline.add_edge(START, "answer")
customer_pipeline.add_edge("answer", END)
# customer_pipeline.add_edge("save_conversation", END)

customer = customer_pipeline.compile(checkpointer=checkpointer)
