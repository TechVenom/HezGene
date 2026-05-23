"""
OpenAI Provider — GPT-4, GPT-3.5, etc.

Uses the OpenAI-compatible chat completions API.
Also works with any OpenAI-compatible endpoint (Azure, local servers, etc.)

Requires: OPENAI_API_KEY environment variable or api_key parameter.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from hezgene.mutation.llm.base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """LLM provider for OpenAI and OpenAI-compatible APIs."""

    DEFAULT_MODEL = "gpt-4o-mini"
    DEFAULT_URL = "https://api.openai.com/v1"

    def __init__(self, model: str = "", base_url: str = "", api_key: str = "", **kwargs: Any):
        super().__init__(
            model=model or self.DEFAULT_MODEL,
            base_url=base_url or self.DEFAULT_URL,
            api_key=api_key or os.environ.get("OPENAI_API_KEY", ""),
            **kwargs,
        )

    @property
    def provider_name(self) -> str:
        return "OpenAI"

    def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> LLMResponse:
        """Generate using OpenAI Chat Completions API."""
        if not self.api_key:
            return LLMResponse(
                text="",
                model=self.model,
                provider=self.provider_name,
                error="No API key. Set OPENAI_API_KEY or pass api_key.",
                success=False,
            )

        url = f"{self.base_url}/chat/completions"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }

        try:
            req = Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                method="POST",
            )

            with urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            choice = data.get("choices", [{}])[0]
            text = choice.get("message", {}).get("content", "")
            usage = data.get("usage", {})

            return LLMResponse(
                text=text,
                model=data.get("model", self.model),
                provider=self.provider_name,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                raw=data,
            )

        except URLError as e:
            return LLMResponse(
                text="",
                model=self.model,
                provider=self.provider_name,
                error=f"OpenAI connection failed: {e}",
                success=False,
            )
        except Exception as e:
            return LLMResponse(
                text="",
                model=self.model,
                provider=self.provider_name,
                error=f"OpenAI error: {e}",
                success=False,
            )

    def is_available(self) -> bool:
        """Check if the API key is set and the API is reachable."""
        if not self.api_key:
            return False
        try:
            req = Request(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                method="GET",
            )
            with urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception:
            return False

    @property
    def total_cost_estimate(self) -> float:
        """Rough per-1K-token cost for common models."""
        costs = {
            "gpt-4o": 0.005,
            "gpt-4o-mini": 0.00015,
            "gpt-4-turbo": 0.01,
            "gpt-3.5-turbo": 0.0005,
        }
        return costs.get(self.model, 0.001)
