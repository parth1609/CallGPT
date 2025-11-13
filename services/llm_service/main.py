"""
Purpose: FastAPI application for LLM Service.

Usage:
    uvicorn main:app --host 0.0.0.0 --port 8005 --reload
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from datetime import datetime
import os
import json

from models import (
    ChatRequest,
    ChatResponse,
    Message,
    StreamChunk,
    ModelsListResponse,
    ModelInfo,
    HealthCheckResponse,
)
from service import LLMService


app = FastAPI(
    title="LLM Service",
    description="Microservice for chat completion with various LLM providers",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm_service = LLMService()


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(status="healthy", timestamp=datetime.utcnow())


@app.post("/api/v1/llm/chat", response_model=ChatResponse)
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


@app.post("/api/v1/llm/stream")
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


@app.get("/api/v1/llm/models", response_model=ModelsListResponse)
async def list_models():
    """Get list of available models"""
    models = llm_service.get_available_models()
    return ModelsListResponse(
        models=[ModelInfo(**m) for m in models]
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_PORT", 8005))
    uvicorn.run(app, host="0.0.0.0", port=port)
