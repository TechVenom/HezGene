"""
File Ingestor — Extracts functions and classes from Python files.

Smart extraction rules:
  - Functions: Evolvable
  - Class methods: Evolvable (except __init__ and simple wrappers)
  - Constructors (__init__): Skipped by default (too risky)
  - Imports, constants, module-level code: Never touched
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hezgene.analysis.complexity import calculate_halstead_metrics, calculate_maintainability_index


@dataclass
class ExtractedFunction:
    """Represents a function extracted from a file."""

    file_path: str
    name: str
    qualified_name: str  # e.g. "utils.py:process_users" or "utils.py:UserManager.get_user"
    source_code: str
    start_line: int
    end_line: int
    is_method: bool = False
    class_name: str | None = None
    type_hints: dict[str, str] = field(default_factory=dict)
    lines_of_code: int = 0
    cyclomatic_complexity: int = 0
    halstead_effort: float = 0.0
    halstead_volume: float = 0.0
    maintainability_index: float = 100.0
    is_simple_wrapper: bool = False
    evolvable: bool = True
    skip_reason: str = ""


# Dunder methods that should never be evolved
SKIP_DUNDERS = {
    "__init__",
    "__new__",
    "__del__",
    "__repr__",
    "__str__",
    "__hash__",
    "__eq__",
    "__ne__",
    "__lt__",
    "__le__",
    "__gt__",
    "__ge__",
    "__enter__",
    "__exit__",
    "__iter__",
    "__next__",
    "__len__",
    "__getitem__",
    "__setitem__",
    "__delitem__",
    "__contains__",
    "__call__",
    "__bool__",
}


class FileIngestor:
    """Parses Python files and extracts evolvable functions/methods."""

    @staticmethod
    def extract(
        file_path: str | Path, include_non_evolvable: bool = False
    ) -> list[ExtractedFunction]:
        """
        Extract all functions and methods from a file.
        By default, filters out non-evolvable items (constructors, simple wrappers).
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in {file_path}: {e}")

        functions: list[ExtractedFunction] = []
        method_nodes: set[int] = set()  # Track method node ids to avoid double-counting

        # First pass: collect class methods
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_nodes.add(id(item))
                        ef = FileIngestor._create_extracted(
                            path, source, item, is_method=True, class_name=node.name
                        )
                        functions.append(ef)

        # Second pass: collect top-level functions
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if id(node) not in method_nodes:
                    ef = FileIngestor._create_extracted(path, source, node)
                    functions.append(ef)

        if not include_non_evolvable:
            functions = [f for f in functions if f.evolvable]

        return functions

    @staticmethod
    def extract_specific(file_path: str | Path, target_name: str) -> list[ExtractedFunction]:
        """
        Extract a specific function or all methods of a specific class.
        target_name can be 'func_name' or 'ClassName' or 'ClassName.method_name'.
        """
        all_funcs = FileIngestor.extract(file_path, include_non_evolvable=True)

        # "ClassName.method_name" — exact method
        if "." in target_name:
            class_name, method_name = target_name.split(".", 1)
            return [f for f in all_funcs if f.class_name == class_name and f.name == method_name]

        # Is it a class name? Return all its methods
        class_methods = [f for f in all_funcs if f.class_name == target_name]
        if class_methods:
            return class_methods

        # Is it a function name?
        return [f for f in all_funcs if f.name == target_name]

    @staticmethod
    def analyze_file(file_path: str | Path) -> dict[str, Any]:
        """
        Full analysis of a file — what's evolvable, what's skipped, and why.
        Used for the CLI display.
        """
        path = Path(file_path)
        all_funcs = FileIngestor.extract(path, include_non_evolvable=True)
        evolvable = [f for f in all_funcs if f.evolvable]
        skipped = [f for f in all_funcs if not f.evolvable]

        classes = set()
        for f in all_funcs:
            if f.class_name:
                classes.add(f.class_name)

        return {
            "file": str(path),
            "total_functions": len(all_funcs),
            "evolvable_count": len(evolvable),
            "skipped_count": len(skipped),
            "classes": list(classes),
            "evolvable": evolvable,
            "skipped": skipped,
        }

    @staticmethod
    def _create_extracted(
        path: Path,
        source: str,
        node: ast.AST,
        is_method: bool = False,
        class_name: str | None = None,
    ) -> ExtractedFunction:
        """Helper to create an ExtractedFunction with smart classification."""
        func_source = ast.get_source_segment(source, node) or ""
        loc = len(func_source.strip().splitlines())

        # Build qualified name
        if class_name:
            qualified_name = f"{class_name}.{node.name}"
        else:
            qualified_name = node.name

        # Extract type hints
        type_hints = FileIngestor._extract_type_hints(node)

        # Determine if evolvable
        evolvable = True
        skip_reason = ""

        # Rule 1: Skip dunder methods
        if node.name in SKIP_DUNDERS:
            evolvable = False
            skip_reason = f"Dunder method ({node.name})"

        # Rule 2: Skip simple wrappers (≤ 2 meaningful lines)
        is_simple = FileIngestor._is_simple_wrapper(node)
        if is_simple and not evolvable:
            skip_reason += " + simple wrapper"
        elif is_simple:
            # Simple wrappers still evolvable but flagged
            pass

        # Rule 3: Skip if too short (just a return or pass)
        if loc <= 2:
            evolvable = False
            skip_reason = "Too short to optimize"

        # Calculate complexity
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        # Calculate Halstead and Maintainability
        halstead = calculate_halstead_metrics(node)
        mi = calculate_maintainability_index(loc, complexity, halstead["volume"])

        return ExtractedFunction(
            file_path=str(path),
            name=node.name,
            qualified_name=qualified_name,
            source_code=func_source,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            is_method=is_method,
            class_name=class_name,
            type_hints=type_hints,
            lines_of_code=loc,
            cyclomatic_complexity=complexity,
            halstead_effort=halstead["effort"],
            halstead_volume=halstead["volume"],
            maintainability_index=mi,
            is_simple_wrapper=is_simple,
            evolvable=evolvable,
            skip_reason=skip_reason,
        )

    @staticmethod
    def _extract_type_hints(node: ast.FunctionDef) -> dict[str, str]:
        """Extract parameter and return type hints as strings."""
        hints = {}
        for arg in node.args.args:
            if arg.annotation:
                try:
                    hints[arg.arg] = ast.unparse(arg.annotation)
                except Exception:
                    pass
        if node.returns:
            try:
                hints["return"] = ast.unparse(node.returns)
            except Exception:
                pass
        return hints

    @staticmethod
    def _is_simple_wrapper(node: ast.FunctionDef) -> bool:
        """Check if a function is just a simple wrapper (single call or return)."""
        body = [
            s
            for s in node.body
            if not isinstance(s, (ast.Expr,)) or not isinstance(s.value, ast.Constant)
        ]
        # Filter out docstrings
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
            body = body[1:]
        # A wrapper has 1-2 statements that are just calls or returns
        if len(body) <= 2:
            for stmt in body:
                if isinstance(stmt, ast.Return):
                    continue
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                    continue
                return False
            return True
        return False
