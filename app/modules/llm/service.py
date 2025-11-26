"""
Purpose: Business logic for LLM Service.
Handles chat completion with various LLM providers.
"""

import os
from typing import List, Dict, Any, Iterator
from groq import Groq
from dotenv import load_dotenv


load_dotenv()


class LLMService:
    """Manages LLM interactions with multiple providers"""
    
    AVAILABLE_MODELS = {
        "openai/gpt-oss-120b": {
            "provider": "groq",
            "description": "Fast inference with Groq",
        },
    }
    
    def __init__(self, default_model: str = None):
        """Initialize LLM Service"""
        self.default_model = default_model or os.getenv(
            "LLM_MODEL",
            "openai/gpt-oss-120b"
        )
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY must be set")
        
        self.groq_client = Groq(api_key=self.groq_api_key)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.5,
        max_tokens: int = None,
    ) -> Dict[str, Any]:
        """
        Generate chat completion.
        
        Parameters:
        - messages: List of message dicts with 'role' and 'content'
        - model: Model name
        - temperature: Sampling temperature
        - max_tokens: Maximum tokens to generate
        
        Returns:
        - Dict with response message and metadata
        """
        model = model or self.default_model
        
        # Convert to format expected by Groq
        groq_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]
        
        completion = self.groq_client.chat.completions.create(
            model=model,
            messages=groq_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        response_message = completion.choices[0].message
        
        return {
            "message": {
                "role": response_message.role,
                "content": response_message.content,
            },
            "model": model,
            "usage": {
                "prompt_tokens": completion.usage.prompt_tokens,
                "completion_tokens": completion.usage.completion_tokens,
                "total_tokens": completion.usage.total_tokens,
            },
        }
    
    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.5,
        max_tokens: int = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Stream chat completion.
        
        Parameters:
        - messages: List of message dicts
        - model: Model name
        - temperature: Sampling temperature
        - max_tokens: Maximum tokens
        
        Yields:
        - Dicts with content chunks and finish_reason
        """
        model = model or self.default_model
        
        groq_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]
        
        stream = self.groq_client.chat.completions.create(
            model=model,
            messages=groq_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        
        for chunk in stream:
            delta = chunk.choices[0].delta
            finish_reason = chunk.choices[0].finish_reason
            
            if delta.content:
                yield {
                    "content": delta.content,
                    "finish_reason": finish_reason,
                }
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        return [
            {
                "name": name,
                "provider": info["provider"],
                "description": info["description"],
            }
            for name, info in self.AVAILABLE_MODELS.items()
        ]


# ============================================================================
# Pipeline Utilities (Backend-compatible functions for LangGraph integration)
# ============================================================================

def get_groq_llm(model: str = "llama-3.1-8b-instant", temperature: float = 0.1):
    """
    Purpose: Initialize a Groq chat LLM via langchain_groq for pipeline usage.
    
    This utility function returns a LangChain ChatModel instance that can be used
    directly in the RAG pipeline, following the backend pattern.

    Parameters:
    - model (str): Groq model name.
    - temperature (float): Sampling temperature.

    Return Value:
    - BaseChatModel: A LangChain ChatModel instance.

    Side Effects:
    - Requires environment variable GROQ_API_KEY.

    Examples:
    >>> llm = get_groq_llm(model="openai/gpt-oss-120b", temperature=0.5)
    >>> isinstance(llm, object)
    True
    """
    from langchain_groq import ChatGroq

    if not os.getenv("GROQ_API_KEY"):
        raise EnvironmentError("GROQ_API_KEY is not set in environment.")

    return ChatGroq(model=model, temperature=temperature)


def get_qa_prompt():
    """
    Purpose: Return a chat prompt template for RAG QA.
    
    This prompt template is optimized for voice-friendly, conversational responses
    in the CallGPT system.

    Return Value:
    - ChatPromptTemplate: A LangChain chat prompt ready to be formatted.

    Side Effects:
    - None.

    Examples:
    >>> prompt = get_qa_prompt()
    >>> from langchain_core.prompts import ChatPromptTemplate
    >>> isinstance(prompt, ChatPromptTemplate)
    True
    """
    from langchain_core.prompts import ChatPromptTemplate
    
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are CallGPT — a voice-friendly AI support assistant.\n"
                    "Your role is to assist customers calling the company by giving clear, polite, and accurate spoken-style answers.\n"
                    "Use ONLY the provided context to answer the question.\n"
                    "If the answer is not found in the context, say politely that you don't have that information.\n"
                    "Keep responses short, natural, and conversational (like talking on a call).\n"
                    "Do NOT make up information. Do NOT reference 'documents' or 'context' explicitly."
                ),
            ),
            (
                "human",
                (
                    "Context:\n{context}\n\n"
                    "Customer Question: {question}\n\n"
                    "Answer naturally as if you are speaking to the customer on a call."
                ),
            ),
        ]
    )
