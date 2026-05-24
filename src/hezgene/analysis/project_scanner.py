"""
Project Scanner — Scans directories for Python files, extracts functions,
and ranks them by evolution priority (slowest, buggiest).
"""

from __future__ import annotations

from pathlib import Path

from hezgene.analysis.file_ingestor import FileIngestor
from ..core.dna_tracker import DNATracker


class ProjectScanner:
    """Scans projects and ranks targets for evolution."""

    def __init__(self, project_root: str = ".", dna_tracker: DNATracker | None = None):
        self.project_root = Path(project_root)
        self.dna_tracker = dna_tracker or DNATracker(project_root)

    def scan_directory(self, directory: str | Path) -> list[str]:
        """
        Scan a directory for all Python files, extract functions,
        register their DNA, and return a list of function qualified names.
        """
        path = Path(directory)
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        all_targets = []

        # Find all Python files excluding virtual environments and hidden dirs
        for py_file in path.rglob("*.py"):
            parts = py_file.parts
            if any(part.startswith(".") for part in parts) or "venv" in parts or "__pycache__" in parts or "node_modules" in parts:
                continue

            try:
                funcs = FileIngestor.extract(py_file)
                for f in funcs:
                    # Construct a target string like "path/to/file.py:func_name"
                    # Or just use the file path relative to project root
                    try:
                        rel_path = py_file.relative_to(self.project_root)
                    except ValueError:
                        rel_path = py_file

                    # Format: "path/to/file.py:func_name"
                    # If it's a method: "path/to/file.py:ClassName.func_name"
                    entity = f.name
                    if f.class_name:
                        entity = f"{f.class_name}.{f.name}"

                    target = f"{rel_path}:{entity}"
                    all_targets.append(target)

                    # Ensure it's tracked in DNA
                    self.dna_tracker.extract(target, override_source=f.source_code)
            except Exception:
                pass  # Skip files with syntax errors

        return all_targets

    def get_ranked_targets(self, metric: str = "slowest", limit: int = 10) -> list[str]:
        """
        Rank tracked functions based on a metric.
        Valid metrics: 'slowest', 'buggiest', 'fitness'
        """
        tracked = []
        for target in self.dna_tracker.get_all_tracked():
            dna = self.dna_tracker.get_dna(target)
            if dna:
                tracked.append((target, dna))

        if not tracked:
            return []

        if metric == "slowest":
            ranked = sorted(tracked, key=lambda x: x[1].avg_execution_time_ms, reverse=True)
        elif metric == "buggiest":
            ranked = sorted(tracked, key=lambda x: x[1].bug_count, reverse=True)
        else:  # fitness (lowest fitness first)
            ranked = sorted(tracked, key=lambda x: x[1].fitness_score)

        return [t[0] for t in ranked[:limit]]
