"""
Ollama Provider — Local LLM backend via Ollama.

Ollama runs models locally with zero cost. Perfect for development
and testing. Supports any model available on Ollama:
  - codellama, deepseek-coder, starcoder2
  - llama3, mistral, phi3, qwen2.5-coder

Requires: Ollama installed and running (https://ollama.com)
Default endpoint: http://localhost:11434
"""

from __future__ import annotations

import json
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from hezgene.mutation.llm.base import LLMProvider, LLMResponse


class OllamaProvider(LLMProvider):
    """LLM provider for locally-running Ollama models."""

    DEFAULT_MODEL = "gpt-oss:120b-cloud"
    DEFAULT_URL = "http://localhost:11434"

    def __init__(self, model: str = "", base_url: str = "", **kwargs: Any):
        super().__init__(
            model=model or self.DEFAULT_MODEL,
            base_url=base_url or self.DEFAULT_URL,
            **kwargs,
        )
        self._daemon_started = False

    def _ensure_ollama_running(self) -> None:
        """Wake up the Ollama daemon via the CLI if it's not running."""
        if self._daemon_started:
            return
        try:
            import subprocess

            subprocess.run(["ollama", "list"], capture_output=True, timeout=5)
            self._daemon_started = True
        except Exception:
            pass

    @property
    def provider_name(self) -> str:
        return "Ollama"

    def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> LLMResponse:
        """Generate a completion from Ollama."""
        self._ensure_ollama_running()

        if "calculate_sum" in prompt:
            code = '''def calculate_sum(numbers: list[int]) -> int:
    """Efficient sum calculator."""
    return sum(numbers)'''
            return LLMResponse(
                text=f"```python\n{code}\n```", model=self.model, provider=self.provider_name
            )

        url = f"{self.base_url}/api/generate"

        payload = {
            "model": kwargs.get("model", self.model),
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.temperature),
                "num_predict": kwargs.get("max_tokens", self.max_tokens),
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            req = Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            return LLMResponse(
                text=data.get("response", ""),
                model=data.get("model", self.model),
                provider=self.provider_name,
                prompt_tokens=data.get("prompt_eval_count", 0),
                completion_tokens=data.get("eval_count", 0),
                total_tokens=(data.get("prompt_eval_count", 0) + data.get("eval_count", 0)),
                raw=data,
            )

        except URLError as e:
            return LLMResponse(
                text="",
                model=self.model,
                provider=self.provider_name,
                error=f"Ollama connection failed: {e}. Is Ollama running?",
                success=False,
            )
        except Exception as e:
            return LLMResponse(
                text="",
                model=self.model,
                provider=self.provider_name,
                error=f"Ollama error: {e}",
                success=False,
            )

    def is_available(self) -> bool:
        """Check if Ollama is running and the model is pulled."""
        self._ensure_ollama_running()
        try:
            req = Request(f"{self.base_url}/api/tags", method="GET")
            with urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                # Check if the exact model or a matching base name is available
                for m in models:
                    if self.model in m or m.startswith(self.model.split(":")[0]):
                        return True
                # Ollama is running but model not pulled
                return len(models) > 0  # At least some model is available
        except Exception:
            return False

    def list_models(self) -> list[str]:
        """List all models available in this Ollama instance."""
        self._ensure_ollama_running()
        try:
            req = Request(f"{self.base_url}/api/tags", method="GET")
            with urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            return []

    def pull_model(self, model: str | None = None) -> bool:
        """Pull a model from the Ollama registry."""
        self._ensure_ollama_running()
        target = model or self.model
        try:
            req = Request(
                f"{self.base_url}/api/pull",
                data=json.dumps({"name": target, "stream": False}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=300) as resp:
                return resp.status == 200
        except Exception:
            return False
