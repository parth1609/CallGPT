"""
Purpose: Business logic for Embedding Service.
Handles text chunking and embedding generation.
"""

import os

# Critical: Enforce HuggingFace offline mode at the absolute top of the module.
# This prevents network update checks in background executor threads.
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["SENTENCE_TRANSFORMERS_HOME"] = "./models_cache"

from typing import List, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv


load_dotenv()


class EmbeddingService:
    """
    Manages text chunking and embedding generation.

    Parameters:
    - default_model (str): Default embedding model name
    """

    # Available models configuration
    AVAILABLE_MODELS = {
        "sentence-transformers/all-MiniLM-L6-v2": {
            "dimension": 384,
            "description": "Fast and efficient model for semantic similarity",
        },
        "sentence-transformers/all-mpnet-base-v2": {
            "dimension": 768,
            "description": "High-quality embeddings with better performance",
        },
        "BAAI/bge-small-en-v1.5": {
            "dimension": 384,
            "description": "Optimized for retrieval tasks",
        },
    }

    def __init__(self, default_model: str = None):
        """
        Initialize Embedding Service.

        Side Effects:
        - Sets default model from environment or parameter
        - Initializes model cache
        """
        self.default_model = default_model or os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )

        # Pre-warm the module-level global singleton to ensure the model is loaded exactly ONCE
        # across all instances of EmbeddingService and the overall application.
        get_embedding_model(self.default_model)

    def _get_embedding_model(self, model_name: str = None):
        """
        Get or create embedding model instance (wrapper for global singleton).
        """
        return get_embedding_model(model_name or self.default_model)

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> List[str]:
        """
        Chunk text using RecursiveCharacterTextSplitter.

        Parameters:
        - text (str): Text to chunk
        - chunk_size (int): Maximum size of each chunk
        - chunk_overlap (int): Overlap between consecutive chunks

        Return Value:
        - List[str]: List of text chunks

        Side Effects:
        - None (pure function)
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
        )

        chunks = splitter.split_text(text)
        return chunks

    def generate_embeddings(
        self,
        texts: List[str],
        model_name: str = None,
    ) -> Tuple[List[List[float]], str, int]:
        """
        Generate embeddings for a list of texts.

        Parameters:
        - texts (List[str]): List of texts to embed
        - model_name (Optional[str]): Model name, uses default if None

        Return Value:
        - Tuple: (embeddings, model_name, dimension)
            - embeddings (List[List[float]]): Embedding vectors
            - model_name (str): Model used
            - dimension (int): Embedding dimension

        Side Effects:
        - Loads embedding model (cached after first use)
        """
        model_name = model_name or self.default_model
        embedding_model = self._get_embedding_model(model_name)

        embeddings = embedding_model.embed_documents(texts)
        dimension = len(embeddings[0]) if embeddings else 0

        return embeddings, model_name, dimension

    def chunk_and_embed(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        model_name: str = None,
    ) -> Tuple[List[str], List[List[float]], str, int]:
        """
        Chunk text and generate embeddings in one operation.

        Parameters:
        - text (str): Text to process
        - chunk_size (int): Maximum size of each chunk
        - chunk_overlap (int): Overlap between chunks
        - model_name (Optional[str]): Model name

        Return Value:
        - Tuple: (chunks, embeddings, model_name, total_chunks)
            - chunks (List[str]): Text chunks
            - embeddings (List[List[float]]): Embedding vectors
            - model_name (str): Model used
            - total_chunks (int): Number of chunks

        Side Effects:
        - Loads embedding model (cached after first use)
        """
        chunks = self.chunk_text(text, chunk_size, chunk_overlap)
        embeddings, model_name, _ = self.generate_embeddings(chunks, model_name)

        return chunks, embeddings, model_name, len(chunks)

    def get_available_models(self) -> List[dict]:
        """
        Get list of available embedding models.

        Return Value:
        - List[dict]: List of model information dictionaries
        """
        return [
            {
                "name": name,
                "dimension": info["dimension"],
                "description": info["description"],
            }
            for name, info in self.AVAILABLE_MODELS.items()
        ]


# ============================================================================
# Pipeline Utilities (Backend-compatible functions for LangGraph integration)
# ============================================================================


# Module-level singleton cache for embedding models.
# Ensures the HuggingFace model is loaded exactly ONCE across all pipeline calls.
_EMBEDDING_MODEL_CACHE: dict = {}

import torch


def get_embedding_model(model_name: str = None):
    """
    Purpose: Return a LangChain Embeddings instance for the specified model.

    Uses a module-level singleton so the model is loaded once and reused,
    avoiding the 4-5 second HuggingFace download/check on every call.

    Parameters:
    - model_name (str): Model name. If None, uses default.

    Return Value:
    - Embeddings: A LangChain-compatible embeddings object (cached singleton).

    Side Effects:
    - Downloads model on first use only, then served from cache.
    """
    global _EMBEDDING_MODEL_CACHE

    if model_name is None:
        model_name = os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )

    # Automatically detect available hardware
    device_name = "cuda:0" if torch.cuda.is_available() else "cpu"

    if model_name not in _EMBEDDING_MODEL_CACHE:
        _EMBEDDING_MODEL_CACHE[model_name] = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": device_name},
            encode_kwargs={"normalize_embeddings": True},
            cache_folder="./models_cache",
        )

    return _EMBEDDING_MODEL_CACHE[model_name]
