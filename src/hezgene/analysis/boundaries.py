"""
Architecture Boundaries — Enforces rules about which modules can import from which.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any

from hezgene.core.config import HezGeneConfig


@dataclass
class BoundaryViolation:
    file_path: str
    line_number: int
    source_zone: str
    target_zone: str
    imported_module: str


class BoundaryScanner:
    """Scans the project for architectural boundary violations based on imports."""

    def __init__(self, project_root: str = ".", config: HezGeneConfig | None = None):
        self.project_root = Path(project_root)
        self.config = config or HezGeneConfig(project_root)

    def scan(self) -> List[BoundaryViolation]:
        """Scan the project and return boundary violations."""
        boundaries = self.config.get("boundaries", {})
        zones: List[Dict[str, Any]] = boundaries.get("zones", [])
        rules: List[Dict[str, Any]] = boundaries.get("rules", [])

        if not zones or not rules:
            return []

        # Map rules for quick lookup: { "source_zone": ["allowed_zone1", "allowed_zone2"] }
        allowed_imports: Dict[str, List[str]] = {
            rule["from"]: rule.get("allow", []) for rule in rules
        }

        violations = []

        for py_file in self.project_root.rglob("*.py"):
            parts = py_file.parts
            if any(p.startswith(".") for p in parts) or "venv" in parts or "__pycache__" in parts or "node_modules" in parts or "build" in parts:
                continue

            try:
                rel_path = py_file.relative_to(self.project_root)
                source_module = self._path_to_module(rel_path)
                source_zone = self._get_zone_for_module(source_module, zones)

                if not source_zone:
                    continue  # File doesn't belong to any zone, skip

                allowed_for_source = allowed_imports.get(source_zone, [])
                
                # Parse AST to find imports
                source_code = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source_code)

                for node in ast.walk(tree):
                    imported_modules = []
                    line = getattr(node, "lineno", 0)

                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imported_modules.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            # Handle relative imports naively for V1 by ignoring them or prepending the package
                            if node.level > 0:
                                # Quick relative import resolution
                                package_parts = source_module.split(".")[:-node.level]
                                base_mod = ".".join(package_parts)
                                if base_mod:
                                    imported_modules.append(f"{base_mod}.{node.module}")
                                else:
                                    imported_modules.append(node.module)
                            else:
                                imported_modules.append(node.module)

                    for mod in imported_modules:
                        target_zone = self._get_zone_for_module(mod, zones)
                        if target_zone and target_zone != source_zone and target_zone not in allowed_for_source:
                            violations.append(
                                BoundaryViolation(
                                    file_path=str(rel_path),
                                    line_number=line,
                                    source_zone=source_zone,
                                    target_zone=target_zone,
                                    imported_module=mod,
                                )
                            )

            except Exception:
                pass

        return violations

    def _path_to_module(self, path: Path) -> str:
        """Convert a file path to a Python module string (e.g. src/core/main.py -> src.core.main)."""
        parts = list(path.parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        elif parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]
        return ".".join(parts)

    def _get_zone_for_module(self, module_name: str, zones: List[Dict[str, Any]]) -> str | None:
        """Find which zone a module belongs to based on pattern prefix matching."""
        for zone in zones:
            for pattern in zone.get("patterns", []):
                # Simple prefix matching
                if module_name == pattern or module_name.startswith(pattern + "."):
                    return zone["name"]
        return None
