"""
Purpose: FastAPI application for Conversation Service.

Usage:
    uvicorn main:app --host 0.0.0.0 --port 8006 --reload
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

from models import (
    CreateThreadRequest,
    ThreadResponse,
    AddMessageRequest,
    MessageResponse,
    ThreadListResponse,
    MessagesListResponse,
    ThreadPreviewResponse,
    HealthCheckResponse,
)
from service import ConversationService


app = FastAPI(
    title="Conversation Service",
    description="Microservice for conversation thread and message management",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conversation_service = ConversationService()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    conversation_service.close()


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(status="healthy", timestamp=datetime.utcnow())


@app.post("/api/v1/conversations/threads", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(request: CreateThreadRequest):
    """Create a new conversation thread"""
    try:
        thread = conversation_service.create_thread(metadata=request.metadata)
        return ThreadResponse(**thread)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Thread creation failed: {str(e)}",
        )


@app.get("/api/v1/conversations/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(thread_id: str):
    """Get thread by ID"""
    thread = conversation_service.get_thread(thread_id)
    
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread {thread_id} not found",
        )
    
    return ThreadResponse(**thread)


@app.get("/api/v1/conversations/threads", response_model=ThreadListResponse)
async def list_threads(limit: int = 100, offset: int = 0):
    """List all threads with pagination"""
    threads = conversation_service.list_threads(limit=limit, offset=offset)
    
    return ThreadListResponse(
        threads=[ThreadResponse(**t) for t in threads],
        total=len(threads),
    )


@app.delete("/api/v1/conversations/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(thread_id: str):
    """Delete a thread and all its messages"""
    success = conversation_service.delete_thread(thread_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread {thread_id} not found",
        )


@app.post("/api/v1/conversations/threads/{thread_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_message(thread_id: str, request: AddMessageRequest):
    """Add a message to a thread"""
    try:
        message = conversation_service.add_message(
            thread_id=thread_id,
            role=request.role,
            content=request.content,
            metadata=request.metadata,
        )
        return MessageResponse(**message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Message add failed: {str(e)}",
        )


@app.get("/api/v1/conversations/threads/{thread_id}/messages", response_model=MessagesListResponse)
async def get_messages(thread_id: str):
    """Get all messages for a thread"""
    try:
        messages = conversation_service.get_messages(thread_id)
        
        return MessagesListResponse(
            messages=[MessageResponse(**m) for m in messages],
            thread_id=thread_id,
            total=len(messages),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get messages: {str(e)}",
        )


@app.get("/api/v1/conversations/threads/{thread_id}/preview", response_model=ThreadPreviewResponse)
async def get_thread_preview(thread_id: str, max_length: int = 50):
    """Get a preview of a thread"""
    try:
        preview = conversation_service.get_thread_preview(thread_id, max_length)
        return ThreadPreviewResponse(**preview)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preview: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_PORT", 8006))
    uvicorn.run(app, host="0.0.0.0", port=port)
