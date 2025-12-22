"""
Purpose: FastAPI router for Document Module.
Handles document uploads, storage, and retrieval operations.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from datetime import datetime
import os

from .models import (
    DocumentUploadRequest,
    DocumentUploadResponse,
    DocumentMetadataResponse,
    DocumentListResponse,
    DocumentContentResponse,
    HealthCheckResponse,
    ChunkDocumentsRequest,
    ChunkDocumentsResponse,
)
from .service import DocumentService


router = APIRouter(tags=["Documents"])

# Initialize service
doc_service = DocumentService()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint to verify service availability.

    Return Value:
    - HealthCheckResponse: Service status and timestamp
    """
    return HealthCheckResponse(
        status="healthy",
        service="document_module",
        timestamp=datetime.utcnow(),
    )


@router.post(
    "/api/v1/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(request: DocumentUploadRequest):
    """
    Upload a document to storage.

    Parameters:
    - request (DocumentUploadRequest): Document upload request with filename, content, and metadata

    Return Value:
    - DocumentUploadResponse: Upload result with document ID and metadata

    Side Effects:
    - Uploads file to Supabase Storage
    - Stores metadata in database
    """
    try:
        result = doc_service.upload_document(
            filename=request.filename,
            content=request.content,
            metadata=request.metadata,
        )
        return DocumentUploadResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(e)}",
        )


@router.post(
    "/api/v1/documents/upload-file",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file directly (multipart/form-data).

    Parameters:
    - file (UploadFile): File uploaded via multipart form

    Return Value:
    - DocumentUploadResponse: Upload result with document ID and metadata

    Side Effects:
    - Reads file content
    - Uploads to Supabase Storage
    """
    try:
        content = await file.read()
        text_content = content.decode("utf-8", errors="ignore")

        result = doc_service.upload_document(
            filename=file.filename,
            content=text_content,
            metadata={
                "original_filename": file.filename,
                "content_type": file.content_type,
            },
        )
        return DocumentUploadResponse(**result)
        # return Document(page_content=text_content,metadata=result['metadata'])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}",
        )


@router.get("/api/v1/documents/{document_id}", response_model=DocumentContentResponse)
async def get_document(document_id: str):
    """
    Retrieve document content by ID.

    Parameters:
    - document_id (str): Unique document identifier

    Return Value:
    - DocumentContentResponse: Document content and metadata
    """
    content = doc_service.get_document_content(document_id)
    metadata = doc_service.get_document_metadata(document_id)

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    # Derive filename if metadata is missing
    derived_filename = (
        document_id.split("_", 1)[1]
        if "_" in document_id
        else (metadata.get("filename") if metadata else "unknown")
    )

    return DocumentContentResponse(
        document_id=document_id,
        filename=derived_filename,
        content=content,
    )


@router.get(
    "/api/v1/documents/{document_id}/metadata", response_model=DocumentMetadataResponse
)
async def get_document_metadata(document_id: str):
    """
    Retrieve document metadata by ID.

    Parameters:
    - document_id (str): Unique document identifier

    Return Value:
    - DocumentMetadataResponse: Document metadata
    """
    metadata = doc_service.get_document_metadata(document_id)

    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    return DocumentMetadataResponse(**metadata)


@router.get("/api/v1/documents/", response_model=DocumentListResponse)
async def list_documents(limit: int = 100, offset: int = 0):
    """
    List all documents with pagination.

    Parameters:
    - limit (int): Maximum number of documents to return (default: 100)
    - offset (int): Number of documents to skip (default: 0)

    Return Value:
    - DocumentListResponse: List of documents and total count
    """
    documents = doc_service.list_documents(limit=limit, offset=offset)

    return DocumentListResponse(
        documents=[DocumentMetadataResponse(**doc) for doc in documents],
        total=len(documents),
    )


@router.delete(
    "/api/v1/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_document(document_id: str):
    """
    Delete a document by ID.

    Parameters:
    - document_id (str): Unique document identifier

    Side Effects:
    - Removes file from storage
    - Deletes metadata from database
    """
    success = doc_service.delete_document(document_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found or deletion failed",
        )


# ============================================================================
# Utility Endpoints (Backend-compatible functions exposed as API)
# ============================================================================


@router.post("/api/v1/documents/utils/chunk", response_model=ChunkDocumentsResponse)
async def chunk_document_text(request: ChunkDocumentsRequest):
    """
    Chunk text into smaller segments using the pipeline utility function.

    This endpoint exposes the chunk_documents() utility function for testing
    and frontend access before using in the pipeline.

    Parameters:
    - request (ChunkDocumentsRequest): Text and chunking parameters

    Return Value:
    - ChunkDocumentsResponse: List of chunks
    """
    from .service import chunk_documents
    from langchain_core.documents import Document

    try:
        # Create a temporary document object
        doc = Document(page_content=request.content, metadata={})

        # Use the utility function
        chunks = chunk_documents(
            docs=[doc],
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
        )

        # Extract text from chunked documents
        chunk_texts = [chunk.page_content for chunk in chunks]

        return ChunkDocumentsResponse(
            chunks=chunk_texts,
            total_chunks=len(chunk_texts),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chunking failed: {str(e)}",
        )
