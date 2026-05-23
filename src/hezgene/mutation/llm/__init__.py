"""
LLM Provider System — Pluggable LLM backends for intelligent mutations.

Supports multiple providers through a unified interface:
  - Ollama (local, free, default for development)
  - OpenAI (GPT-4, GPT-3.5)
  - Anthropic (Claude)
  - Google (Gemini)
  - Custom HTTP endpoints

Usage:
    from hezgene.mutation.llm import get_provider
    provider = get_provider("ollama", model="codellama")
    response = provider.generate("Optimize this function...")
"""

from hezgene.mutation.llm.base import LLMProvider, LLMResponse
from hezgene.mutation.llm.factory import get_provider, list_providers

__all__ = [
    "LLMProvider",
    "LLMResponse",
    "get_provider",
    "list_providers",
]
