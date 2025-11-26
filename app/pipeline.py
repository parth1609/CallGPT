from __future__ import annotations
from fileinput import filename
from typing import Any, Dict, List, Optional, TypedDict
from typing import Annotated, Sequence

from langgraph.graph import StateGraph, START, END
from langchain_core.documents import Document
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, AIMessageChunk

# Import utility functions from modules (backend pattern)
from app.modules.embedding.service import get_embedding_model
from app.modules.llm.service import get_groq_llm, get_qa_prompt
from app.modules.vectorstore.service import build_supabase_from_documents, load_supabase
from app.modules.document.service import chunk_documents, load_text_file,DocumentService
from app.modules.retrieval.service import get_retriever, retrieve


# Import from new modular structure
from app import pipeline as app_pipeline
from app.modules.embedding.service import EmbeddingService
from app.modules.vectorstore.service import VectorStoreService


class RAGState(TypedDict, total=False):
    # Inputs / config
    table_name: str
    query_name: str
    rebuild: bool

    # Document
    filename: str
    content: Optional[str] = None
    # input_path: str
    metadata : str =None
    chunks: List[Document]


    embeddings_model: str

    llm_model: str
    temperature: float

    search_type: str
    k: int
    fetch_k: int
    lambda_mult: float

    template: str
    question: str

    # Conversational memory (accumulated across turns via checkpointer)
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Artifacts
    docs: List[Document]
    answer: str



#  LangGraph Nodes

def document_service_node(
    state: RAGState,
    uploaded_file: uploaded_file
    )-> Dict[str, Any]:
    # initiate the service
    doc_service = DocumentService()
    # load the file
    file = doc_service.load_text_file(uploaded_file)
    # chunk the file
    file_chunks = doc_service.chunk_documents(file)
    # get the metadata
    metadata = doc_service.get_document_metadata(file)  
    
    return{
        "content": file.page_content,
        "metadata": metadata,
        "chunks": file_chunks
    }
        


def node_vectorstore(state: RAGState) -> Dict[str, Any]:
    """Upsert chunks to Supabase vector store when rebuild is requested"""
    # Supabase-only: upsert when explicitly requested via rebuild
    emb = get_embedding_model(state.get("embeddings_model"))
    if state.get("rebuild", False):
        table_name = state.get("table_name", "documents")
        query_name = state.get("query_name", "match_documents")
        build_supabase_from_documents(
            state["chunks"], emb, table_name=table_name, query_name=query_name
        )
    return {}


def node_answer(state: RAGState):
    """Retrieve documents and generate answer with streaming"""
    prompt = get_qa_prompt()
    
    # Ephemerally load vectorstore and create retriever (Supabase)
    emb = get_embedding_model(state.get("embeddings_model"))
    vstore = load_supabase(
        state.get("table_name", "documents"),
        emb,
        query_name=state.get("query_name", "match_documents"),
    )
    
    if state.get("search_type", "mmr") == "mmr":
        retriever = get_retriever(
            vstore,
            search_type="mmr",
            k=state.get("k", 4),
            fetch_k=state.get("fetch_k", 20),
            lambda_mult=state.get("lambda_mult", 0.5),
        )
    else:
        retriever = get_retriever(vstore, search_type="similarity", k=state.get("k", 4))

    # Retrieve and prepare context
    docs = retrieve(retriever, state["question"])
    context = "\n\n".join(d.page_content for d in docs)

    # Create LLM ephemerally
    temperature = state.get("temperature", 0.1)
    llm = get_groq_llm(model=state.get("llm_model", "openai/gpt-oss-120b"), temperature=temperature)

    history = list(state.get("messages", []))  # previous turns
    current = prompt.format_messages(context=context, question=state["question"])
    messages = [*history, *current]

    # Stream tokens and yield AI message chunks for smoother UI
    answer_accum = ""
    for chunk in llm.stream(messages):
        delta = getattr(chunk, "content", "")
        if not delta:
            continue
        answer_accum += delta
        # Emit incremental assistant chunks via the messages channel
        yield {"messages": [AIMessageChunk(content=delta)]}

    # Finalize: return full answer and persist the turn into memory
    yield {
        "answer": answer_accum,
        "messages": [
            HumanMessage(content=state["question"]),
            AIMessage(content=answer_accum),
        ],
    }


def build_rag_graph(checkpointer: Optional[Any] = None) -> Any:
    """
    Purpose: Build the RAG graph with LangGraph.
    
    This follows the backend pattern exactly, using utility functions for
    all operations instead of service classes.
    
    Parameters:
    - checkpointer: Optional checkpointer for conversation persistence
    
    Return Value:
    - Compiled LangGraph application
    """
    builder = StateGraph(RAGState)
    builder.add_node("load", node_load)
    builder.add_node("chunk", node_chunk)
    builder.add_node("vectorstore", node_vectorstore)
    builder.add_node("answer", node_answer)

    builder.add_edge(START, "load")
    builder.add_edge("load", "chunk")
    builder.add_edge("chunk", "vectorstore")
    builder.add_edge("vectorstore", "answer")
    builder.add_edge("answer", END)

    return builder.compile(checkpointer=checkpointer)

