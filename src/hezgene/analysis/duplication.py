"""
Code Duplication Detection — Identifies copy-pasted or structurally identical functions.
"""

from __future__ import annotations

import ast
import hashlib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

from hezgene.analysis.file_ingestor import FileIngestor

@dataclass
class DuplicateGroup:
    hash_id: str
    functions: List[dict]


class ASTNormalizer(ast.NodeTransformer):
    """
    Normalizes variable names, constants, and function names so that
    structurally identical functions produce the same AST dump.
    """
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        # Normalize the function name
        node.name = "FUNC"
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        node.name = "FUNC"
        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> ast.AST:
        # Replace all variable names with a generic placeholder
        return ast.Name(id="VAR", ctx=node.ctx)

    def visit_arg(self, node: ast.arg) -> ast.AST:
        # Replace all arguments with a generic placeholder
        return ast.arg(arg="ARG", annotation=None)

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        # Replace all literal constants with a generic placeholder
        return ast.Constant(value="CONST")


class DuplicationScanner:
    """Scans a project for duplicated or structurally identical functions."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)

    def scan(self) -> List[DuplicateGroup]:
        """Scan the project and return groups of duplicated functions."""
        if not self.project_root.is_dir():
            raise NotADirectoryError(f"Not a directory: {self.project_root}")

        ast_hashes: Dict[str, List[dict]] = defaultdict(list)

        for py_file in self.project_root.rglob("*.py"):
            parts = py_file.parts
            if any(part.startswith(".") for part in parts) or "venv" in parts or "__pycache__" in parts or "node_modules" in parts or "build" in parts:
                continue
            
            try:
                funcs = FileIngestor.extract(py_file, include_non_evolvable=False)
                for f in funcs:
                    # Parse the function's source code back into an AST
                    # We need the source since ExtractedFunction doesn't keep the AST node
                    func_tree = ast.parse(f.source_code)
                    
                    # Normalize the tree (remove variable names, constants, etc.)
                    normalizer = ASTNormalizer()
                    normalized_tree = normalizer.visit(func_tree)
                    
                    # Dump the normalized AST structure
                    ast_dump = ast.dump(normalized_tree)
                    
                    # Generate a hash for this structure
                    struct_hash = hashlib.md5(ast_dump.encode("utf-8")).hexdigest()[:8]
                    
                    ast_hashes[struct_hash].append({
                        "file_path": str(py_file.relative_to(self.project_root)),
                        "name": f.name,
                        "qualified_name": f.qualified_name,
                        "line": f.start_line,
                        "loc": f.lines_of_code
                    })
            except Exception:
                pass

        # Filter out hashes that only have 1 function (no duplicates)
        # Also require the function to be at least 3 lines of code to avoid trivial clones (like simple getters/setters)
        duplicate_groups = []
        for hash_id, funcs in ast_hashes.items():
            if len(funcs) > 1 and funcs[0]["loc"] >= 3:
                duplicate_groups.append(DuplicateGroup(hash_id=f"dup:{hash_id}", functions=funcs))

        # Sort by number of duplicates in the group (descending)
        duplicate_groups.sort(key=lambda g: len(g.functions), reverse=True)
        return duplicate_groups
