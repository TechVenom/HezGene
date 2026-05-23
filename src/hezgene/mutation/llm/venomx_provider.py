"""
VENOMX Provider — Uses VENOMX's own intelligence for code evolution.

VENOMX is the Sovereign Autonomous Intelligence Engine.
This provider allows VENOMX to evolve code using its own brain.

Requires: VENOMX running with API access.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from hezgene.mutation.llm.base import LLMProvider, LLMResponse


class VenomXProvider(LLMProvider):
    """LLM provider for VENOMX's own intelligence engine."""

    DEFAULT_MODEL = "default"
    DEFAULT_URL = "http://localhost:8000"

    def __init__(self, model: str = "", base_url: str = "", api_key: str = "", **kwargs: Any):
        super().__init__(
            model=model or self.DEFAULT_MODEL,
            base_url=base_url or os.environ.get("VENOMX_URL", self.DEFAULT_URL),
            api_key=api_key or os.environ.get("VENOMX_API_KEY", ""),
            **kwargs,
        )

    @property
    def provider_name(self) -> str:
        return "VENOMX"

    def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> LLMResponse:
        """Generate using VENOMX's brain execution API."""
        url = f"{self.base_url}/api/v1/generate"

        payload = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "model": kwargs.get("model", self.model),
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            req = Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )

            with urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            return LLMResponse(
                text=data.get("response", data.get("text", "")),
                model=data.get("model", self.model),
                provider=self.provider_name,
                prompt_tokens=data.get("prompt_tokens", 0),
                completion_tokens=data.get("completion_tokens", 0),
                total_tokens=data.get("total_tokens", 0),
                raw=data,
            )

        except URLError as e:
            return LLMResponse(
                text="",
                model=self.model,
                provider=self.provider_name,
                error=f"VENOMX connection failed: {e}. Is VENOMX running?",
                success=False,
            )
        except Exception as e:
            return LLMResponse(
                text="",
                model=self.model,
                provider=self.provider_name,
                error=f"VENOMX error: {e}",
                success=False,
            )

    def is_available(self) -> bool:
        """Check if VENOMX is running."""
        try:
            req = Request(f"{self.base_url}/api/v1/health", method="GET")
            with urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False
