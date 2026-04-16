# Windows Event Loop Fix: psycopg (async PostgreSQL driver) cannot run on
# Windows' default ProactorEventLoop. Switch to SelectorEventLoop.
import sys
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # Fix Windows console encoding (cp1252 can't handle emoji in print statements)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Python 3.13 Compatibility Shim: audioop was removed in 3.13. 
# We use audioop-lts as a drop-in replacement.
try:
    import audioop
except ImportError:
    import sys
    try:
        import audioop_lts as audioop
        sys.modules["audioop"] = audioop
        sys.modules["pyaudioop"] = audioop # For specific pydub forks looking for pyaudioop
    except ImportError:
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.modules.embedding.router import router as embedding_router
from app.modules.retrieval.router import router as retrieval_router
from app.modules.llm.router import router as llm_router
from app.modules.conversation.router import router as conversation_router
from app.modules.document.router import router as document_router
from app.modules.vectorstore.router import router as vectorstore_router
from app.modules.pipeline.router import router as pipeline_router
from app.modules.voicebot.router import router as voicebot_router

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Performance Optimization: Pre-warm models and services at startup.
    Ensures that the 400MB embedding model and Pinecone index are ready
    BEFORE the first call arrives, eliminating the 8-second cold start.
    """
    import asyncio
    print("⏳ [Startup] Pre-warming models and services...")
    
    try:
        # 1. Warm up Embedding Service (Loads HuggingFace model into RAM)
        from app.modules.embedding.service import get_embedding_model
        await asyncio.to_thread(get_embedding_model)
        print("✅ [Startup] Embedding model loaded")
        
        # 2. Warm up Retrieval Service (Initializes Pinecone connection)
        from app.modules.retrieval.service import get_retrieval_service
        await asyncio.to_thread(get_retrieval_service)
        print("✅ [Startup] Retrieval service initialized")
        
        # 3. Warm up LLM Service (Initializes Groq client)
        from app.modules.llm.service import get_llm_service
        await asyncio.to_thread(get_llm_service)
        print("✅ [Startup] LLM service initialized")

        # 4. Optional: Run a dummy pipeline turn to warm up graph execution
        from app.modules.voicebot.router import _voicebot_pipeline
        dummy_state = {
            "question": "warmup",
            "thread_id": "warmup",
            "messages": [],
            "bucket_name": "openai-bucket"
        }
        await asyncio.to_thread(
            lambda: list(_voicebot_pipeline.stream(
                dummy_state, 
                config={"configurable": {"thread_id": "warmup"}},
                stream_mode="updates"
            ))
        )
        print("✅ [Startup] Pipeline execution warmed up")
        
    except Exception as e:
        print(f"⚠️ [Startup] Pre-warm optimization partially failed: {e}")
        
    yield
    print("👋 [Shutdown] Cleaning up...")

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="Modular Monolith API for CallGPT",
    lifespan=lifespan
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

# IMPORTANT: CORSMiddleware is REQUIRED for WebSocket connections from 
# external services like Exotel AgentStream. Without it, incoming 
# connections from unknown origins will be blocked with '403 Forbidden'.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for AgentStream
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers Inclusion
# ---------------------------------------------------------------------------

# Register all modular routers
app.include_router(embedding_router, prefix="/api/v1/embedding", tags=["Embedding"])
app.include_router(retrieval_router, prefix="/api/v1/retrieval", tags=["Retrieval"])
app.include_router(llm_router, prefix="/api/v1/llm", tags=["LLM"])
app.include_router(conversation_router, prefix="/api/v1/conversation", tags=["Conversation"])
app.include_router(document_router, prefix="/api/v1/document", tags=["Document"])
app.include_router(vectorstore_router, prefix="/api/v1/vectorstore", tags=["VectorStore"])
app.include_router(pipeline_router, prefix="/api/v1/pipeline", tags=["Pipeline"])
app.include_router(voicebot_router) # No prefix for the main voicebot WebSocket endpoint


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, loop="asyncio")
