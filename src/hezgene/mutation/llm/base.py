"""
LLM Provider — Abstract base class for all LLM backends.

Every LLM provider must implement:
  - generate(prompt, **kwargs) → LLMResponse
  - is_available() → bool

This makes it trivial to add new providers:
  1. Subclass LLMProvider
  2. Implement generate() and is_available()
  3. Register in factory.py
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""

    text: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    success: bool = True

    @property
    def total_cost_estimate(self) -> float:
        """Rough cost estimate in USD (for paid providers)."""
        # Override per provider for accurate pricing
        return 0.0


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Subclass this to add support for any LLM backend.
    The only required methods are generate() and is_available().
    """

    def __init__(
        self,
        model: str = "",
        base_url: str = "",
        api_key: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        timeout: int = 60,
        **kwargs: Any,
    ):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.extra_config = kwargs

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name of this provider (e.g. 'Ollama', 'OpenAI')."""
        ...

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            prompt: The user prompt to send.
            system_prompt: Optional system-level instructions.
            **kwargs: Provider-specific overrides (temperature, max_tokens, etc.)

        Returns:
            LLMResponse with the generated text or error info.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this provider is reachable and ready.

        Returns:
            True if the provider can accept requests right now.
        """
        ...

    def generate_timed(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> LLMResponse:
        """Generate with automatic latency measurement."""
        start = time.perf_counter()
        response = self.generate(prompt, system_prompt=system_prompt, **kwargs)
        response.latency_ms = (time.perf_counter() - start) * 1000
        return response

    def __repr__(self) -> str:
        return f"<{self.provider_name}(model={self.model!r})>"
