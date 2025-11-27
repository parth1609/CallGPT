from __future__ import annotations
import os
from fileinput import filename
from typing import Any, Dict, List, Optional, TypedDict
from typing import Annotated, Sequence

from langgraph.graph import StateGraph, START, END
from langchain_core.documents import Document
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, AIMessageChunk

# Import utility functions from modules (backend pattern)
from app.modules.embedding.service import get_embedding_model
from app.modules.llm.service import get_groq_llm, get_qa_prompt,LLMService
from app.modules.document.service import chunk_documents, load_text_file,DocumentService
from app.modules.retrieval.service import get_retriever, retrieve, RetrievalService


# Import from new modular structure
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

    # Supabase
    bucket_name: str  # same for pinecone-index name

    # Embedding
    chunks: List[Document]
    chunk_size: Optional[int] 
    chunk_overlap: Optional[int]
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
    uploaded_file: str,
    )-> Dict[str, Any]:
    # initiate the service
    doc_service = DocumentService(bucket_name=state.get("bucket_name"))
    
    # load the file
    docs = load_text_file(uploaded_file)
    if not docs:
        raise ValueError("No content loaded from file")
    file = docs[0]
    
    # Upload to Supabase (handles bucket creation internally if needed)
    upload_result = doc_service.upload_document(
        filename=os.path.basename(uploaded_file), 
        content=file.page_content, 
        metadata=file.metadata
    )
    
    return{
        "content": file.page_content,
        "metadata": upload_result,
        "filename": os.path.basename(uploaded_file)
    }

def embedding_node(state: RAGState):
    Embedding_Service = EmbeddingService()

    embedding_model = state.get('embeddings_model')
    
    # Unpack the tuple returned by chunk_and_embed
    # Returns: (chunks, embeddings, model_name, total_chunks)
    chunks_text, all_embeddings, model_name, total_chunks = Embedding_Service.chunk_and_embed(
        state.get('content'), 
        state.get('chunk_size'), 
        state.get('chunk_overlap'),
        embedding_model
    )
    
    # Calculate dimension from the first embedding if available
    dimension = len(all_embeddings[0]) if all_embeddings else 0
    
    return {
        "embeddings": all_embeddings,
        "dimension": dimension
    }

    


def node_vectorstore(state: RAGState) -> Dict[str, Any]:
    """Upsert chunks to Pinecone vector store when rebuild is requested"""
    # Pinecone-only: upsert when explicitly requested via rebuild
    vstore = VectorStoreService()
    idx = state.get("bucket_name").lower()
    
    # Extract text content from chunks for upsert_vectors
    chunks_text = [chunk.page_content for chunk in state.get("chunks")]
    
    vstore.upsert_vectors(
        chunks = chunks_text,
        embeddings = state.get("embeddings"),
        index_name = idx,
        metadata = vstore._sanitize_metadata(state.get("metadata"))
    )
    return {}


def node_answer(state: RAGState):
    """Retrieve documents and generate answer with streaming from pinecone vector store"""
    retriever_service = RetrievalService(
        index_name = state.get("bucket_name").lower(),
    )
    llm_service = LLMService()
    query = state.get("question") 
    # convert query to embedding => embeddings[0]
    query_embedding = retriever_service._get_query_embedding(query)
    # chatpromptTemplate
    prompt = get_qa_prompt()
    
    if state.get("search_type", "similarity_search") == "similarity_search":
        retriever = retriever_service.similarity_search(
            query = query,
            k = state.get("k", 4),
            embedding_model = state.get("embeddings_model"),
        )
    if state.get("search_type", "mmr_search") == "mmr_search":
        retriever = retriever_service.mmr_search(
            query = query,
            k = state.get("k", 4),
            fetch_k = state.get("fetch_k", 20),
            lambda_mult = state.get("lambda_mult", 0.5),
            embedding_model = state.get("embeddings_model"),
        )
     
    # Retrieve and prepare context
    docs = retriever_service.retrieve(retriever, query)
    context = "\n\n".join(d.page_content for d in docs)

    # Create LLM ephemerally
    temperature = state.get("temperature", 0.1)
    llm = get_groq_llm(model=state.get("llm_model", "openai/gpt-oss-120b"), temperature=temperature)


    # Create the full message list
    history = list(state.get("messages", []))
    current = prompt.format_messages(context=context, question=state.get("question"))
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


def Orgs_pipeline(checkpointer: Optional[Any] = None) -> Any:
    """
    Purpose: Build the RAG graph for document processing and indexing.
    
    This pipeline handles the complete document ingestion workflow: loading
    documents, creating embeddings, and storing vectors in Pinecone. This is
    typically used by organizations to index their documents.
    
    Parameters:
    - checkpointer: Optional checkpointer for conversation persistence
    
    Return Value:
    - Compiled LangGraph application
    
    Graph Flow:
    START -> document_load -> embedding -> vectorstore -> END
    """
    builder = StateGraph(RAGState)
    builder.add_node("document_load", document_service_node)
    builder.add_node("embedding", embedding_node)
    builder.add_node("vectorstore", node_vectorstore)

    builder.add_edge(START, "document_load")
    builder.add_edge("document_load", "embedding")
    builder.add_edge("embedding", "vectorstore")
    builder.add_edge("vectorstore", END)

   
    return builder.compile(checkpointer=checkpointer)

def customer_pipeline():
    """
    Purpose: Build a simplified customer-facing RAG graph for Q&A.
    
    This pipeline is designed for customer interactions where documents are
    already loaded and indexed. It only handles the query and answer flow.
    
    Return Value:
    - Compiled LangGraph application
    
    Graph Flow:
    START -> answer -> END
    """
    builder = StateGraph(RAGState)
    builder.add_node("answer", node_answer)
    builder.add_node("vectorstore", node_vectorstore)

    builder.add_edge(START, "vectorstore")
    builder.add_edge("vectorstore", "answer")
    builder.add_edge("answer", END)

    return builder.compile()

