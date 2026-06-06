"""
Dependency Hygiene — Scans for unused or missing dependencies.
Matches project imports against declared requirements.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set, Dict
import sys

# Standard library module names to ignore during dependency checks
stdlib_modules = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else {
    "os", "sys", "pathlib", "json", "ast", "re", "dataclasses", "typing", 
    "collections", "itertools", "functools", "time", "datetime", "math", 
    "random", "hashlib", "subprocess", "logging", "asyncio", "importlib"
}

@dataclass
class HygieneIssue:
    package_name: str
    issue_type: str  # "unused", "missing"
    reason: str


class DependencyScanner:
    """Scans the project for dependency hygiene issues."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)

    def scan(self) -> List[HygieneIssue]:
        if not self.project_root.is_dir():
            raise NotADirectoryError(f"Not a directory: {self.project_root}")

        declared_deps = self._get_declared_dependencies()
        imported_modules = self._get_imported_modules()
        
        # Package names in requirements often differ slightly from import names (e.g., beautifulsoup4 -> bs4)
        # For a robust Fallow-like system, we'd need a mapping, but for V1 we use normalized names.
        normalized_declared = {self._normalize_pkg_name(p) for p in declared_deps}
        normalized_imported = {self._normalize_pkg_name(m) for m in imported_modules}

        issues = []

        # Find Unused Dependencies (in requirements but not imported)
        for pkg in declared_deps:
            norm_pkg = self._normalize_pkg_name(pkg)
            if norm_pkg not in normalized_imported:
                issues.append(
                    HygieneIssue(
                        package_name=pkg,
                        issue_type="unused",
                        reason="Declared in requirements but never imported in the codebase."
                    )
                )

        # Find Missing Dependencies (imported but not in requirements)
        # Note: We must be careful not to flag internal modules
        internal_modules = self._get_internal_modules()
        
        for mod in imported_modules:
            norm_mod = self._normalize_pkg_name(mod)
            if norm_mod not in normalized_declared and mod not in internal_modules:
                issues.append(
                    HygieneIssue(
                        package_name=mod,
                        issue_type="missing",
                        reason="Imported in the codebase but not listed in requirements."
                    )
                )

        # Sort issues
        issues.sort(key=lambda x: (x.issue_type, x.package_name))
        return issues

    def _normalize_pkg_name(self, name: str) -> str:
        """Normalize package name (e.g. 'PyYAML' -> 'yaml', 'rich-click' -> 'rich_click')."""
        name = name.lower().replace("-", "_")
        # Common aliases
        aliases = {
            "beautifulsoup4": "bs4",
            "pyyaml": "yaml",
            "python_dotenv": "dotenv",
            "gitpython": "git"
        }
        return aliases.get(name, name)

    def _get_declared_dependencies(self) -> Set[str]:
        deps = set()
        # 1. Parse requirements.txt
        req_file = self.project_root / "requirements.txt"
        if req_file.exists():
            for line in req_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    # Extract package name (remove ==, >=, etc.)
                    pkg = re.split(r'[<>=!~]', line)[0].strip()
                    if pkg:
                        deps.add(pkg)

        # 2. Parse pyproject.toml [project.dependencies]
        pyproject_file = self.project_root / "pyproject.toml"
        if pyproject_file.exists():
            try:
                content = pyproject_file.read_text(encoding="utf-8")
                # Simple TOML parser for the dependencies array
                # Look for the [project] section, then find 'dependencies = ['
                in_project = False
                in_deps = False
                for line in content.splitlines():
                    stripped = line.strip()
                    if stripped == "[project]":
                        in_project = True
                        continue
                    elif stripped.startswith("[") and stripped != "[project]":
                        in_project = False
                        in_deps = False
                        continue
                    if in_project and stripped.startswith("dependencies"):
                        in_deps = True
                        # Handle inline: dependencies = ["click>=8.0", ...]
                        if "[" in stripped:
                            for match in re.findall(r'"([^"]+)"', stripped):
                                pkg = re.split(r'[<>=!~\[]', match)[0].strip()
                                if pkg:
                                    deps.add(pkg)
                            if "]" in stripped:
                                in_deps = False
                        continue
                    if in_deps:
                        if "]" in stripped:
                            # Parse any remaining entries on the closing line
                            for match in re.findall(r'"([^"]+)"', stripped):
                                pkg = re.split(r'[<>=!~\[]', match)[0].strip()
                                if pkg:
                                    deps.add(pkg)
                            in_deps = False
                            continue
                        for match in re.findall(r'"([^"]+)"', stripped):
                            pkg = re.split(r'[<>=!~\[]', match)[0].strip()
                            if pkg:
                                deps.add(pkg)
            except Exception:
                pass

        return deps

    def _get_imported_modules(self) -> Set[str]:
        imports = set()
        for py_file in self.project_root.rglob("*.py"):
            parts = py_file.parts
            if any(p.startswith(".") for p in parts) or "venv" in parts or "__pycache__" in parts or "node_modules" in parts or "build" in parts:
                continue

            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            root_mod = alias.name.split(".")[0]
                            if root_mod not in stdlib_modules:
                                imports.add(root_mod)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.level == 0:
                            root_mod = node.module.split(".")[0]
                            if root_mod not in stdlib_modules:
                                imports.add(root_mod)
            except Exception:
                pass
        return imports

    def _get_internal_modules(self) -> Set[str]:
        """Get top-level directory names and python file names to treat as internal packages."""
        internal = set()
        for item in self.project_root.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                internal.add(item.name)
            elif item.is_file() and item.name.endswith(".py"):
                internal.add(item.name[:-3])
        # Also add anything in 'src/'
        src_dir = self.project_root / "src"
        if src_dir.exists() and src_dir.is_dir():
            for item in src_dir.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    internal.add(item.name)
                elif item.is_file() and item.name.endswith(".py"):
                    internal.add(item.name[:-3])
        return internal

    def apply_fixes(self, issues: List[HygieneIssue]) -> int:
        """
        Delete unused dependencies from requirements.txt.
        Returns the number of removed dependencies.
        """
        unused_packages = {i.package_name.lower() for i in issues if i.issue_type == "unused"}
        if not unused_packages:
            return 0

        req_file = self.project_root / "requirements.txt"
        if not req_file.exists():
            return 0

        deleted_count = 0
        try:
            lines = req_file.read_text(encoding="utf-8").splitlines()
            new_lines = []
            
            for line in lines:
                clean_line = line.strip()
                if clean_line and not clean_line.startswith("#"):
                    pkg = re.split(r'[<>=!~]', clean_line)[0].strip().lower()
                    if pkg in unused_packages:
                        deleted_count += 1
                        continue
                new_lines.append(line)
                
            if deleted_count > 0:
                req_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        except Exception:
            pass

        return deleted_count
