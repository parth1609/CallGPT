"""
Purpose: FastAPI router for Conversation Module.
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime
import os

from .models import (
    CreateThreadRequest,
    ThreadResponse,
    AddMessage,
    MessageResponse,
    AllThreadsMessagesResponse,
    ThreadMessagesResponse,
    MessageModel,
    HealthCheckResponse,
    MessagesListResponse,
)
from .service import ConversationService


router = APIRouter(tags=["Conversation"])

conversation_service = ConversationService()


@router.on_event("startup")
async def startup_event():
    """Open connection pool on startup"""
    await conversation_service.open()


@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await conversation_service.close()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(status="healthy", timestamp=datetime.utcnow())


@router.post(
    "/api/v1/conversations/threads",
    response_model=ThreadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_thread(request: CreateThreadRequest):
    """Create a new conversation thread"""
    try:
        thread = await conversation_service.create_thread(metadata=request.metadata)
        return ThreadResponse(**thread)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Thread creation failed: {str(e)}",
        )


@router.get(
    "/api/v1/conversations/view-threads-with-messages",
    response_model=AllThreadsMessagesResponse,
)
async def list_threads(limit: int = 100):
    """List all threads with messages"""
    threads_messages = await conversation_service.list_threads(limit=limit)
    thread_response = []
    for thread_msgs in threads_messages:
        if thread_msgs:
            thread_id = thread_msgs[0]["thread_id"]
            messages = [MessageModel(**msg) for msg in thread_msgs]
            thread_response.append(
                ThreadMessagesResponse(thread_id=thread_id, messages=messages)
            )

    return AllThreadsMessagesResponse(
        threads=thread_response, total=len(thread_response)
    )


"""
Temepory comment off
"""
# @router.delete("/api/v1/conversations/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_thread(thread_id: str):
#     """Delete a thread and all its messages"""
#     success = conversation_service.delete_thread(thread_id)

#     if not success:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Thread {thread_id} not found",
#         )


@router.post(
    "/api/v1/conversations/threads/{thread_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_message(thread_id: str, request: AddMessage):
    """Add a message to a thread"""
    from uuid import uuid4

    # get current message
    existing_message = await conversation_service.get_thread_messages(thread_id)
    next_index = len(existing_message)
    try:
        message = await conversation_service.add_thread_message(
            thread_id=thread_id,
            message_id=str(uuid4()),
            index=next_index,
            message_type=request.type,
            content=request.content,
        )
        return MessageResponse(**message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Message add failed: {str(e)}",
        )


@router.get(
    "/api/v1/conversations/threads/{thread_id}/messages",
    response_model=MessagesListResponse,
)
async def get_thread_messages(thread_id: str):
    """Get all messages for a thread"""
    try:
        messages = await conversation_service.get_thread_messages(thread_id)

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
