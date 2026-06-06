"""
Dead Code Detection — Identifies unreachable functions and classes.
Uses a directed call graph to find true reachability from known entry points.
"""

from __future__ import annotations

import ast
from pathlib import Path
from dataclasses import dataclass
from typing import List, Set, Dict, Tuple
from collections import defaultdict

from hezgene.analysis.file_ingestor import FileIngestor

@dataclass
class DeadCodeFinding:
    file_path: str
    entity_name: str
    qualified_name: str
    line_number: int
    end_lineno: int
    reason: str


class CallGraphVisitor(ast.NodeVisitor):
    def __init__(self, current_file: str, current_entity: str | None = None):
        self.current_file = current_file
        self.current_entity = current_entity
        self.calls: Set[str] = set()

    def visit_Name(self, node: ast.Name):
        self.calls.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        self.calls.add(node.attr)
        self.generic_visit(node)


class DeadCodeScanner:
    """Scans a project for dead (unreachable) code using a directed graph."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)

    def scan(self) -> List[DeadCodeFinding]:
        if not self.project_root.is_dir():
            raise NotADirectoryError(f"Not a directory: {self.project_root}")

        defined_entities: Dict[str, dict] = {}
        # caller -> set of callees (names)
        call_graph: Dict[str, Set[str]] = defaultdict(set)
        # Entry points (e.g. routes, CLI commands, scripts)
        entry_points: Set[str] = set()

        all_py_files = []

        # 1. Parse all files and extract definitions
        for py_file in self.project_root.rglob("*.py"):
            parts = py_file.parts
            if any(part.startswith(".") for part in parts) or "venv" in parts or "__pycache__" in parts or "node_modules" in parts or "build" in parts:
                continue
            
            all_py_files.append(py_file)
            rel_path = str(py_file.relative_to(self.project_root))

            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source)

                # Find all top-level definitions and collect their outgoing calls
                for node in tree.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        # Skip dunders
                        if node.name.startswith("__") and node.name.endswith("__"):
                            continue

                        is_entry = False

                        # Framework-aware entry point detection:

                        # 1. Decorated functions/classes are often entry points
                        #    (routes, CLI commands, event handlers, etc.)
                        if getattr(node, 'decorator_list', []):
                            is_entry = True

                        # 2. Classes that inherit from framework base classes
                        if isinstance(node, ast.ClassDef):
                            for base in node.bases:
                                base_name = ""
                                if isinstance(base, ast.Name):
                                    base_name = base.id
                                elif isinstance(base, ast.Attribute):
                                    base_name = base.attr

                                # Pydantic models, Django models, dataclasses, etc.
                                if base_name in {
                                    "BaseModel", "BaseSettings",       # Pydantic
                                    "Model", "Form",                   # Django
                                    "Resource",                        # Flask-RESTful
                                    "Schema",                          # Marshmallow
                                    "Base",                            # SQLAlchemy
                                    "Enum", "IntEnum", "StrEnum",      # Python enums
                                }:
                                    is_entry = True

                            # Also check for @dataclass decorator
                            for dec in node.decorator_list:
                                dec_name = ""
                                if isinstance(dec, ast.Name):
                                    dec_name = dec.id
                                elif isinstance(dec, ast.Attribute):
                                    dec_name = dec.attr
                                elif isinstance(dec, ast.Call):
                                    if isinstance(dec.func, ast.Name):
                                        dec_name = dec.func.id
                                    elif isinstance(dec.func, ast.Attribute):
                                        dec_name = dec.func.attr
                                if dec_name in {"dataclass", "dataclasses"}:
                                    is_entry = True
                            
                        # If a file is executed as a script, its functions might be called at module level
                        # We'll handle module level calls later.
                        
                        defined_entities[node.name] = {
                            "file_path": rel_path,
                            "name": node.name,
                            "qualified_name": node.name,
                            "line": node.lineno,
                            "end_lineno": getattr(node, "end_lineno", node.lineno),
                            "is_entry": is_entry
                        }
                        
                        if is_entry:
                            entry_points.add(node.name)

                        # Visit body to find calls
                        visitor = CallGraphVisitor(rel_path, node.name)
                        for child in node.body:
                            visitor.visit(child)
                        
                        call_graph[node.name].update(visitor.calls)
                    
                    elif isinstance(node, ast.If):
                        # check for if __name__ == "__main__":
                        if isinstance(node.test, ast.Compare):
                            left = node.test.left
                            if isinstance(left, ast.Name) and left.id == "__name__":
                                # Module entry point, any calls here are entry points
                                visitor = CallGraphVisitor(rel_path, "__main__")
                                for child in node.body:
                                    visitor.visit(child)
                                entry_points.update(visitor.calls)

                # Also collect module-level usages that aren't inside defs (which also act as entry points)
                for node in tree.body:
                    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        visitor = CallGraphVisitor(rel_path, "__module__")
                        visitor.visit(node)
                        entry_points.update(visitor.calls)

            except Exception:
                pass

        # 2. Graph Reachability Traversal (BFS)
        reachable: Set[str] = set()
        queue = list(entry_points)

        while queue:
            current = queue.pop(0)
            if current not in reachable:
                reachable.add(current)
                # If this name is a defined entity, add all its outgoing calls to the queue
                if current in call_graph:
                    queue.extend(call_graph[current])

        # 3. Find Dead Code
        findings = []
        for name, info in defined_entities.items():
            if name not in reachable:
                findings.append(
                    DeadCodeFinding(
                        file_path=info["file_path"],
                        entity_name=info["name"],
                        qualified_name=info["qualified_name"],
                        line_number=info["line"],
                        end_lineno=info["end_lineno"],
                        reason="Unreachable from any known entry point in the call graph."
                    )
                )

        findings.sort(key=lambda x: (x.file_path, x.line_number))
        return findings

    def apply_fixes(self, findings: List[DeadCodeFinding]) -> int:
        """
        Delete the dead code from the source files.
        Returns the number of deleted entities.
        """
        if not findings:
            return 0

        # Group findings by file
        by_file: Dict[str, List[DeadCodeFinding]] = defaultdict(list)
        for f in findings:
            by_file[f.file_path].append(f)

        deleted_count = 0

        for file_path, file_findings in by_file.items():
            abs_path = self.project_root / file_path
            if not abs_path.exists():
                continue

            try:
                lines = abs_path.read_text(encoding="utf-8").splitlines()
                # Sort findings by line number in descending order so deleting lines doesn't shift earlier line numbers
                file_findings.sort(key=lambda x: x.line_number, reverse=True)

                for finding in file_findings:
                    start_idx = finding.line_number - 1
                    end_idx = finding.end_lineno
                    
                    # Delete the lines and also try to delete the preceding decorators if any
                    # This is slightly naive but effective for standard @decorators immediately preceding
                    while start_idx > 0 and lines[start_idx - 1].strip().startswith("@"):
                        start_idx -= 1
                        
                    del lines[start_idx:end_idx]
                    deleted_count += 1

                # Rejoin and write back
                abs_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            except Exception:
                pass

        return deleted_count
