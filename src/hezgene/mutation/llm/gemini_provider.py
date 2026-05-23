"""
Google Gemini Provider — Gemini models via the Generative Language API.

Requires: GEMINI_API_KEY environment variable or api_key parameter.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from hezgene.mutation.llm.base import LLMProvider, LLMResponse


class GeminiProvider(LLMProvider):
    """LLM provider for Google Gemini models."""

    DEFAULT_MODEL = "gemini-2.0-flash"
    DEFAULT_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, model: str = "", base_url: str = "", api_key: str = "", **kwargs: Any):
        super().__init__(
            model=model or self.DEFAULT_MODEL,
            base_url=base_url or self.DEFAULT_URL,
            api_key=api_key or os.environ.get("GEMINI_API_KEY", ""),
            **kwargs,
        )

    @property
    def provider_name(self) -> str:
        return "Gemini"

    def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> LLMResponse:
        """Generate using Gemini's generateContent endpoint."""
        if not self.api_key:
            return LLMResponse(
                text="",
                model=self.model,
                provider=self.provider_name,
                error="No API key. Set GEMINI_API_KEY or pass api_key.",
                success=False,
            )

        model = kwargs.get("model", self.model)
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"

        contents = [{"parts": [{"text": prompt}]}]

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", self.temperature),
                "maxOutputTokens": kwargs.get("max_tokens", self.max_tokens),
            },
        }

        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        try:
            req = Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            # Extract text from candidates
            candidates = data.get("candidates", [])
            text = ""
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts)

            usage = data.get("usageMetadata", {})

            return LLMResponse(
                text=text,
                model=model,
                provider=self.provider_name,
                prompt_tokens=usage.get("promptTokenCount", 0),
                completion_tokens=usage.get("candidatesTokenCount", 0),
                total_tokens=usage.get("totalTokenCount", 0),
                raw=data,
            )

        except URLError as e:
            return LLMResponse(
                text="",
                model=self.model,
                provider=self.provider_name,
                error=f"Gemini connection failed: {e}",
                success=False,
            )
        except Exception as e:
            return LLMResponse(
                text="",
                model=self.model,
                provider=self.provider_name,
                error=f"Gemini error: {e}",
                success=False,
            )

    def is_available(self) -> bool:
        """Check if the API key is set."""
        return bool(self.api_key)
