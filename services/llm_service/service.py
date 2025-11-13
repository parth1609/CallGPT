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
        "llama-3.1-70b-versatile": {
            "provider": "groq",
            "description": "Llama 3.1 70B on Groq",
        },
        "mixtral-8x7b-32768": {
            "provider": "groq",
            "description": "Mixtral 8x7B on Groq",
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
