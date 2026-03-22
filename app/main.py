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

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="Modular Monolith API for CallGPT",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(embedding_router, prefix="/api/v1/embeddings", tags=["Embeddings"])
app.include_router(retrieval_router, prefix="/api/v1/retrieval", tags=["Retrieval"])
app.include_router(llm_router, prefix="/api/v1/llm", tags=["LLM"])
app.include_router(
    conversation_router, prefix="/api/v1/conversations", tags=["Conversation"]
)
app.include_router(document_router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(
    vectorstore_router, prefix="/api/v1/vectorstore", tags=["VectorStore"]
)
app.include_router(pipeline_router, prefix="/api/v1/pipeline", tags=["Pipeline"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
