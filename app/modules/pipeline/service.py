"""
Purpose: Service layer for Pipeline orchestration.
Handles business logic for LangGraph workflow execution.
"""

import tempfile
import os
from typing import Dict, Any

from .pipeline import Organisations, customer, RAGState


class PipelineService:
    """
    Service class for pipeline orchestration using LangGraph workflows.

    This service wraps the LangGraph workflows and provides a clean
    interface for executing document processing and query pipelines.
    """

    def __init__(self):
        """Initialize the pipeline service."""
        self.organisations_pipeline = Organisations
        self.customer_pipeline = customer

    def process_organisation_document(
        self,
        filename: str,
        content: str,
        bucket_name: str,
        embeddings_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Process an organisation document through the LangGraph pipeline.

        Pipeline Flow:
        START → document_load → embedding → vectorstore → END

        Parameters:
        - filename (str): Original filename
        - content (str): Text content of the document
        - bucket_name (str): Supabase bucket and Pinecone index name
        - embeddings_model (str): Model to use for embeddings
        - chunk_size (int): Size of text chunks
        - chunk_overlap (int): Overlap between chunks
        - metadata (Dict): Additional metadata

        Return Value:
        - Dict containing processing results

        Side Effects:
        - Creates temporary file for processing
        - Uploads document to Supabase storage
        - Generates embeddings
        - Stores vectors in Pinecone

        Raises:
        - ValueError: If content is empty or invalid
        - Exception: If pipeline execution fails
        """
        if not content or not content.strip():
            raise ValueError("Document content cannot be empty")

        if not filename:
            raise ValueError("Filename is required")

        if not bucket_name:
            raise ValueError("Bucket name is required")

        # Create temporary file for pipeline processing
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".txt", encoding="utf-8"
            ) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            # Initialize LangGraph state
            state: RAGState = {
                "bucket_name": bucket_name,
                "filename": filename,
                "uploaded_file_path": tmp_path,
                "embeddings_model": embeddings_model,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "rebuild": True,
            }

            # Add metadata if provided
            if metadata:
                state["metadata"] = metadata

            # Execute LangGraph workflow
            result = self.organisations_pipeline.invoke(state)

            return result

        finally:
            # Cleanup temporary file
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass  # Ignore cleanup errors

    def process_organisation_file(
        self,
        file_path: str,
        filename: str,
        bucket_name: str,
        embeddings_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> Dict[str, Any]:
        """
        Process an organisation document from a file path.

        Parameters:
        - file_path (str): Path to the uploaded file
        - filename (str): Original filename
        - bucket_name (str): Supabase bucket and Pinecone index name
        - embeddings_model (str): Model to use for embeddings
        - chunk_size (int): Size of text chunks
        - chunk_overlap (int): Overlap between chunks

        Return Value:
        - Dict containing processing results

        Raises:
        - ValueError: If file doesn't exist or is invalid
        - Exception: If pipeline execution fails
        """
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        # Initialize LangGraph state
        state: RAGState = {
            "bucket_name": bucket_name,
            "filename": filename,
            "uploaded_file_path": file_path,
            "embeddings_model": embeddings_model,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "rebuild": True,
        }

        # Execute LangGraph workflow
        result = self.organisations_pipeline.invoke(state)

        return result

    async def query_documents(
        self,
        bucket_name: str,
        question: str,
        embeddings_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        llm_model: str = "openai/gpt-oss-120b",
        temperature: float = 0.5,
        search_type: str = "similarity_search",
        k: int = 4,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
        thread_id: str = None,
    ) -> Dict[str, Any]:
        """
        Query documents through the customer pipeline.

        Pipeline Flow:
        START → vectorstore → answer → save_conversation → END

        Parameters:
        - bucket_name (str): Pinecone index name to query
        - question (str): User's question
        - embeddings_model (str): Model for query embedding
        - llm_model (str): LLM model for answer generation
        - temperature (float): Temperature for LLM
        - search_type (str): Type of search (similarity_search or mmr_search)
        - k (int): Number of documents to retrieve
        - fetch_k (int): For MMR search
        - lambda_mult (float): For MMR search
        - thread_id (str): Thread ID for conversation tracking

        Return Value:
        - Dict containing the answer and metadata

        Raises:
        - ValueError: If question or bucket_name is empty
        - Exception: If pipeline execution fails
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        if not bucket_name:
            raise ValueError("Bucket name is required")

        # Initialize state
        state: RAGState = {
            "bucket_name": bucket_name,
            "question": question,
            "embeddings_model": embeddings_model,
            "llm_model": llm_model,
            "temperature": temperature,
            "search_type": search_type,
            "k": k,
            "fetch_k": fetch_k,
            "lambda_mult": lambda_mult,
            "thread_id": thread_id,
            "messages": [],
            "rebuild": False,
        }

        # Execute workflow and get final result
        config = {"configurable": {"thread_id": thread_id or "default"}}
        result = await self.customer_pipeline.ainvoke(state, config=config)

        return result

    async def stream_query(
        self,
        bucket_name: str,
        question: str,
        embeddings_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        llm_model: str = "openai/gpt-oss-120b",
        temperature: float = 0.5,
        search_type: str = "similarity_search",
        k: int = 4,
        thread_id: str = None,
    ):
        """
        Stream query responses from the customer pipeline.

        Parameters:
        - bucket_name (str): Pinecone index name to query
        - question (str): User's question
        - embeddings_model (str): Model for query embedding
        - llm_model (str): LLM model for answer generation
        - temperature (float): Temperature for LLM
        - search_type (str): Type of search
        - k (int): Number of documents to retrieve
        - thread_id (str): Thread ID for conversation tracking

        Yields:
        - Dict chunks containing message updates and final answer

        Raises:
        - ValueError: If question or bucket_name is empty
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        if not bucket_name:
            raise ValueError("Bucket name is required")

        # Initialize state
        state: RAGState = {
            "bucket_name": bucket_name,
            "question": question,
            "embeddings_model": embeddings_model,
            "llm_model": llm_model,
            "temperature": temperature,
            "search_type": search_type,
            "k": k,
            "thread_id": thread_id,
            "messages": [],
            "rebuild": False,
        }

        # Stream results from pipeline
        config = {"configurable": {"thread_id": thread_id or "default"}}
        async for chunk in self.customer_pipeline.astream(state, config=config):
            yield chunk
