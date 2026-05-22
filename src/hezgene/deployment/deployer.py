"""
Auto Deployer — Deploys winning mutants with rollback safety.

Uses line-number-based replacement to surgically swap functions
while preserving the rest of the file exactly as-is.
"""

from __future__ import annotations

import ast
import shutil
import time
from pathlib import Path
from typing import Any

from hezgene.core.dna_tracker import FunctionDNA


class DeploymentError(Exception):
    """Raised when deployment fails."""


class AutoDeployer:
    """Deploys evolved functions back into the source with safety nets."""

    BACKUP_DIR = ".hezgene/backups"

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.backup_path = self.project_root / self.BACKUP_DIR

    def deploy(self, target: str, winner: FunctionDNA) -> dict[str, Any]:
        """
        Replace the original function source with the winner.
        Target format: 'file_path.py:entity_name'

        Uses line-number-based replacement to preserve file formatting.
        """
        if ":" not in target:
            raise ValueError(f"Invalid target format for deployer: {target}")

        file_path_str, entity_name = target.split(":", 1)
        file_path = self.project_root / ".hezgene" / "uploads" / file_path_str
        if not file_path.exists():
            file_path = self.project_root / file_path_str

        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path_str} not found")

        # Step 1: Backup
        backup = self._backup(file_path)

        try:
            # Step 2: Read file and parse to find function location
            original_text = file_path.read_text(encoding="utf-8")
            tree = ast.parse(original_text)

            # Step 3: Find the function node to get line numbers
            func_node = self._find_function(tree, entity_name)
            if func_node is None:
                raise DeploymentError(f"Function {entity_name} not found in {file_path}")

            start_line = func_node.lineno  # 1-indexed
            end_line = func_node.end_lineno  # 1-indexed, inclusive

            # Step 4: Get the indentation of the original function
            lines = original_text.splitlines(keepends=True)
            original_first_line = lines[start_line - 1]
            indent = len(original_first_line) - len(original_first_line.lstrip())
            indent_str = original_first_line[:indent]

            # Step 5: Re-indent the winner's source code to match
            winner_lines = winner.source_code.splitlines()
            # Determine the winner's current indentation
            winner_indent = 0
            for wl in winner_lines:
                if wl.strip():
                    winner_indent = len(wl) - len(wl.lstrip())
                    break

            reindented = []
            for wl in winner_lines:
                if wl.strip():
                    # Remove winner's indent, add original indent
                    stripped = wl[winner_indent:] if len(wl) >= winner_indent else wl.lstrip()
                    reindented.append(indent_str + stripped + "\n")
                else:
                    reindented.append("\n")

            # Step 6: Replace the lines
            new_lines = lines[: start_line - 1] + reindented + lines[end_line:]
            new_text = "".join(new_lines)

            # Step 7: Verify new file parses
            ast.parse(new_text)

            # Step 8: Write
            file_path.write_text(new_text, encoding="utf-8")

            return {
                "status": "deployed",
                "target": target,
                "file": str(file_path),
                "backup": str(backup),
                "timestamp": time.time(),
            }

        except Exception as e:
            self._rollback(file_path, backup)
            raise DeploymentError(f"Deployment failed, rolled back: {e}") from e

    def _find_function(self, tree: ast.Module, entity_name: str) -> ast.AST | None:
        """Find a function/method node by entity name."""
        # Handle "ClassName.method_name"
        if "." in entity_name:
            class_name, method_name = entity_name.split(".", 1)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if item.name == method_name:
                                return item
        else:
            # Top-level function
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name == entity_name:
                        return node
        return None

    def _backup(self, file_path: Path) -> Path:
        """Create a timestamped backup of the file."""
        self.backup_path.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        backup = self.backup_path / f"{file_path.stem}_{ts}{file_path.suffix}"
        shutil.copy2(file_path, backup)
        return backup

    @staticmethod
    def _rollback(file_path: Path, backup: Path) -> None:
        """Restore from backup."""
        if backup.exists():
            shutil.copy2(backup, file_path)
