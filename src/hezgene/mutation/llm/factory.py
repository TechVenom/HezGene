"""
LLM Provider Factory — Creates the right provider from a name string.

Registry pattern: add new providers by importing and registering them.
"""

from __future__ import annotations

from typing import Any

from hezgene.mutation.llm.base import LLMProvider

_PROVIDERS: dict[str, type[LLMProvider]] = {}


def _ensure_registered() -> None:
    """Lazy-load all built-in providers on first access."""
    if _PROVIDERS:
        return

    from hezgene.mutation.llm.anthropic_provider import AnthropicProvider
    from hezgene.mutation.llm.gemini_provider import GeminiProvider
    from hezgene.mutation.llm.ollama import OllamaProvider
    from hezgene.mutation.llm.openai_provider import OpenAIProvider
    from hezgene.mutation.llm.venomx_provider import VenomXProvider

    _PROVIDERS.update(
        {
            "ollama": OllamaProvider,
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "gemini": GeminiProvider,
            "venomx": VenomXProvider,
        }
    )


def register_provider(name: str, provider_class: type[LLMProvider]) -> None:
    """Register a custom LLM provider."""
    _PROVIDERS[name.lower()] = provider_class


def get_provider(name: str, **kwargs: Any) -> LLMProvider:
    """Create an LLM provider instance by name."""
    _ensure_registered()
    key = name.lower()
    if key not in _PROVIDERS:
        available = ", ".join(sorted(_PROVIDERS.keys()))
        raise ValueError(f"Unknown LLM provider: {name!r}. Available: {available}")
    return _PROVIDERS[key](**kwargs)


def list_providers() -> list[str]:
    """Return a list of all registered provider names."""
    _ensure_registered()
    return sorted(_PROVIDERS.keys())
