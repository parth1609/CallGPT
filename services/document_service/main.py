"""
Purpose: FastAPI application for Document Service.
Handles document uploads, storage, and retrieval operations.

Usage:
    uvicorn main:app --host 0.0.0.0 --port 8001 --reload
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

from models import (
    DocumentUploadRequest,
    DocumentUploadResponse,
    DocumentMetadataResponse,
    DocumentListResponse,
    DocumentContentResponse,
    HealthCheckResponse,
)
from service import DocumentService


app = FastAPI(
    title="Document Service",
    description="Microservice for document storage and retrieval",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service
doc_service = DocumentService()


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint to verify service availability.
    
    Return Value:
    - HealthCheckResponse: Service status and timestamp
    """
    return HealthCheckResponse(
        status="healthy",
        service="document_service",
        timestamp=datetime.utcnow(),
    )


@app.post("/api/v1/documents/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
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


@app.post("/api/v1/documents/upload-file", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
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
            metadata={"original_filename": file.filename, "content_type": file.content_type},
        )
        return DocumentUploadResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}",
        )


@app.get("/api/v1/documents/{document_id}", response_model=DocumentContentResponse)
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
    derived_filename = document_id.split("_", 1)[1] if "_" in document_id else (metadata.get("filename") if metadata else "unknown")
    
    return DocumentContentResponse(
        document_id=document_id,
        filename=derived_filename,
        content=content,
    )


@app.get("/api/v1/documents/{document_id}/metadata", response_model=DocumentMetadataResponse)
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


@app.get("/api/v1/documents/", response_model=DocumentListResponse)
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


@app.delete("/api/v1/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
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


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
