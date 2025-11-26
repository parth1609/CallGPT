"""
Purpose: FastAPI router for LLM Module.
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from datetime import datetime
import os
import json

from .models import (
    ChatRequest,
    ChatResponse,
    Message,
    StreamChunk,
    ModelsListResponse,
    ModelInfo,
    HealthCheckResponse,
)
from .service import LLMService


router = APIRouter(tags=["LLM"])

llm_service = LLMService()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(status="healthy", timestamp=datetime.utcnow())


@router.post("/api/v1/llm/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    """Generate chat completion"""
    try:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        
        result = llm_service.chat(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        return ChatResponse(
            message=Message(**result["message"]),
            model=result["model"],
            usage=result.get("usage"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat completion failed: {str(e)}",
        )


@router.post("/api/v1/llm/stream")
async def stream_chat_completion(request: ChatRequest):
    """Stream chat completion"""
    try:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        
        def generate():
            for chunk in llm_service.stream_chat(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stream chat failed: {str(e)}",
        )


@router.get("/api/v1/llm/models", response_model=ModelsListResponse)
async def list_models():
    """Get list of available models"""
    models = llm_service.get_available_models()
    return ModelsListResponse(
        models=[ModelInfo(**m) for m in models]
    )
