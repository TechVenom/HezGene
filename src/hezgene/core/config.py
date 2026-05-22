"""
HezGene Configuration — Manages persistent settings.

Config is stored in .hezgene/config.json and supports:
  - LLM provider selection and model configuration
  - Evolution parameters (generations, min improvement)
  - Safety settings (auto-apply, backup retention)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = {
    "llm": {
        "provider": "ollama",
        "model": "",
        "base_url": "",
        "api_key": "",
        "temperature": 0.3,
        "max_tokens": 4096,
        "timeout": 120,
    },
    "evolution": {
        "generations": 5,
        "min_improvement": 0.001,
        "use_llm": False,
        "llm_only": False,
    },
    "safety": {
        "auto_apply": False,
        "max_backups": 50,
        "verify_after_deploy": True,
    },
}


class HezGeneConfig:
    """Manages HezGene configuration with JSON persistence."""

    CONFIG_FILE = ".hezgene/config.json"

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.config_path = self.project_root / self.CONFIG_FILE
        self._config: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load config from disk, merging with defaults."""
        self._config = json.loads(json.dumps(DEFAULT_CONFIG))
        if self.config_path.exists():
            try:
                saved = json.loads(self.config_path.read_text(encoding="utf-8"))
                self._deep_merge(self._config, saved)
            except (json.JSONDecodeError, Exception):
                pass

    def _save(self) -> None:
        """Save config to disk."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(
            json.dumps(self._config, indent=2, default=str),
            encoding="utf-8",
        )

    def _deep_merge(self, base: dict, override: dict) -> None:
        """Recursively merge override into base."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value using dot notation (e.g. 'llm.provider')."""
        parts = key.split(".")
        current = self._config
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    def set(self, key: str, value: Any) -> None:
        """Set a config value using dot notation and save."""
        # Auto-map common typos
        if key == "llm_provider":
            key = "llm.provider"
        elif key == "llm_model":
            key = "llm.model"

        parts = key.split(".")
        current = self._config
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        # Auto-convert value types
        if isinstance(value, str):
            if value.lower() in ("true", "false"):
                value = value.lower() == "true"
            else:
                try:
                    value = float(value)
                    if value == int(value):
                        value = int(value)
                except ValueError:
                    pass
        current[parts[-1]] = value
        self._save()

    def get_all(self) -> dict[str, Any]:
        """Return the full config dict."""
        return self._config.copy()

    def get_llm_config(self) -> dict[str, Any]:
        """Get LLM-specific config as a flat dict for provider init."""
        llm = self._config.get("llm", {})
        return {
            "model": llm.get("model", ""),
            "base_url": llm.get("base_url", ""),
            "api_key": llm.get("api_key", ""),
            "temperature": llm.get("temperature", 0.3),
            "max_tokens": llm.get("max_tokens", 4096),
            "timeout": llm.get("timeout", 120),
        }

    def get_llm_provider_name(self) -> str:
        """Get the configured LLM provider name."""
        return self._config.get("llm", {}).get("provider", "ollama")

    def is_llm_enabled(self) -> bool:
        """Check if LLM mutations are enabled."""
        return self._config.get("evolution", {}).get("use_llm", False)
