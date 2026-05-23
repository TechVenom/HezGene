"""
Anthropic Provider — Claude models.

Uses the Anthropic Messages API.

Requires: ANTHROPIC_API_KEY environment variable or api_key parameter.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from hezgene.mutation.llm.base import LLMProvider, LLMResponse


class AnthropicProvider(LLMProvider):
    """LLM provider for Anthropic Claude models."""

    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    DEFAULT_URL = "https://api.anthropic.com/v1"

    def __init__(self, model: str = "", base_url: str = "", api_key: str = "", **kwargs: Any):
        super().__init__(
            model=model or self.DEFAULT_MODEL,
            base_url=base_url or self.DEFAULT_URL,
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY", ""),
            **kwargs,
        )

    @property
    def provider_name(self) -> str:
        return "Anthropic"

    def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> LLMResponse:
        """Generate using Anthropic Messages API."""
        if not self.api_key:
            return LLMResponse(
                text="",
                model=self.model,
                provider=self.provider_name,
                error="No API key. Set ANTHROPIC_API_KEY or pass api_key.",
                success=False,
            )

        url = f"{self.base_url}/messages"

        payload: dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            req = Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                },
                method="POST",
            )

            with urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            # Extract text from content blocks
            content = data.get("content", [])
            text = "".join(
                block.get("text", "") for block in content if block.get("type") == "text"
            )
            usage = data.get("usage", {})

            return LLMResponse(
                text=text,
                model=data.get("model", self.model),
                provider=self.provider_name,
                prompt_tokens=usage.get("input_tokens", 0),
                completion_tokens=usage.get("output_tokens", 0),
                total_tokens=(usage.get("input_tokens", 0) + usage.get("output_tokens", 0)),
                raw=data,
            )

        except URLError as e:
            return LLMResponse(
                text="",
                model=self.model,
                provider=self.provider_name,
                error=f"Anthropic connection failed: {e}",
                success=False,
            )
        except Exception as e:
            return LLMResponse(
                text="",
                model=self.model,
                provider=self.provider_name,
                error=f"Anthropic error: {e}",
                success=False,
            )

    def is_available(self) -> bool:
        """Check if the API key is set."""
        return bool(self.api_key)
