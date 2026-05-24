"""
🧬 HezGene — Project Manager

Handles full project ingestion from zip files, local folders, and GitHub
repositories. Builds hierarchical project trees with per-file AST analysis
and aggregate statistics.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hezgene.analysis.file_ingestor import FileIngestor


# ── Data Classes ──────────────────────────────────────────────────


@dataclass
class FunctionInfo:
    """Lightweight function summary for tree display."""
    name: str
    qualified_name: str
    lines_of_code: int
    evolvable: bool
    skip_reason: str | None = None
    is_method: bool = False
    class_name: str | None = None
    fitness_score: float | None = None
    evolution_count: int = 0
    frozen: bool = False


@dataclass
class FileNode:
    """A single Python file in the project tree."""
    name: str
    rel_path: str
    abs_path: str
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    total_functions: int = 0
    evolvable_functions: int = 0
    avg_fitness: float | None = None
    error: str | None = None


@dataclass
class DirNode:
    """A directory in the project tree."""
    name: str
    rel_path: str
    children_dirs: list[DirNode] = field(default_factory=list)
    children_files: list[FileNode] = field(default_factory=list)


@dataclass
class ProjectTree:
    """Complete project analysis tree."""
    project_name: str
    root_path: str
    root: DirNode | None = None
    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_evolvable: int = 0
    avg_fitness: float | None = None
    fitness_excellent: int = 0  # >= 75
    fitness_fair: int = 0       # >= 50
    fitness_poor: int = 0       # < 50
    recommendation: str | None = None


# Directories/patterns to always skip
SKIP_DIRS = {
    ".hezgene", ".git", ".svn", ".hg", "__pycache__", ".mypy_cache",
    ".pytest_cache", ".tox", ".eggs", "node_modules", "venv", ".venv",
    "env", ".env", "dist", "build", ".idea", ".vscode",
}

SKIP_FILE_PREFIXES = (".", "_")


class ProjectManager:
    """
    Manages full project ingestion: zip upload, folder scan, GitHub clone.
    Produces a ProjectTree with per-file analysis for the web UI.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.projects_dir = self.project_root / ".hezgene" / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    # ── Ingestion Methods ─────────────────────────────────────────

    def ingest_zip(self, zip_path: str | Path) -> ProjectTree:
        """Extract a zip file and analyze the project inside."""
        zip_path = Path(zip_path)
        if not zip_path.exists():
            raise FileNotFoundError(f"Zip file not found: {zip_path}")
        if not zipfile.is_zipfile(zip_path):
            raise ValueError(f"Not a valid zip file: {zip_path}")

        project_id = str(uuid.uuid4())[:8]
        extract_dir = self.projects_dir / project_id
        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        # If the zip has a single top-level directory, use that as root
        top_entries = list(extract_dir.iterdir())
        if len(top_entries) == 1 and top_entries[0].is_dir():
            actual_root = top_entries[0]
        else:
            actual_root = extract_dir

        return self.build_tree(actual_root)

    def ingest_zip_bytes(self, zip_bytes: bytes, filename: str = "project.zip") -> ProjectTree:
        """Accept raw zip bytes (from HTTP upload) and analyze."""
        project_id = str(uuid.uuid4())[:8]
        extract_dir = self.projects_dir / project_id
        extract_dir.mkdir(parents=True, exist_ok=True)

        zip_path = extract_dir / filename
        zip_path.write_bytes(zip_bytes)

        return self.ingest_zip(zip_path)

    def ingest_folder(self, folder_path: str | Path) -> ProjectTree:
        """Analyze an existing folder in-place."""
        folder_path = Path(folder_path).resolve()
        if not folder_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {folder_path}")
        return self.build_tree(folder_path)

    def ingest_github(self, url: str) -> ProjectTree:
        """Clone a GitHub repository and analyze it."""
        # Sanitize URL
        url = url.strip()
        if not url.startswith(("https://", "http://", "git@")):
            url = f"https://github.com/{url}"
        if url.endswith("/"):
            url = url[:-1]

        # Derive project name from URL
        project_name = url.rstrip("/").split("/")[-1]
        if project_name.endswith(".git"):
            project_name = project_name[:-4]

        project_id = f"{project_name}_{str(uuid.uuid4())[:6]}"
        clone_dir = self.projects_dir / project_id

        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", url, str(clone_dir)],
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to clone {url}: {e.stderr.strip()}")
        except FileNotFoundError:
            raise RuntimeError("git is not installed. Please install git to clone repositories.")

        return self.build_tree(clone_dir)

    # ── Tree Builder ──────────────────────────────────────────────

    def build_tree(self, root_path: Path) -> ProjectTree:
        """
        Recursively scan a directory and build a full project tree
        with per-file AST analysis.
        """
        root_path = Path(root_path).resolve()
        project_name = root_path.name

        tree = ProjectTree(
            project_name=project_name,
            root_path=str(root_path),
        )

        root_node = self._scan_dir(root_path, root_path)
        tree.root = root_node

        # Compute aggregate stats
        all_files = self._collect_files(root_node)
        tree.total_files = len(all_files)

        all_fitness: list[float] = []
        worst_file: tuple[str, float] | None = None

        for fnode in all_files:
            tree.total_functions += fnode.total_functions
            tree.total_evolvable += fnode.evolvable_functions
            tree.total_classes += len(fnode.classes)

            for func in fnode.functions:
                if func.fitness_score is not None:
                    score = func.fitness_score
                    all_fitness.append(score)
                    if score >= 75:
                        tree.fitness_excellent += 1
                    elif score >= 50:
                        tree.fitness_fair += 1
                    else:
                        tree.fitness_poor += 1

            if fnode.avg_fitness is not None:
                if worst_file is None or fnode.avg_fitness < worst_file[1]:
                    worst_file = (fnode.rel_path, fnode.avg_fitness)

        if all_fitness:
            tree.avg_fitness = sum(all_fitness) / len(all_fitness)

        if worst_file:
            tree.recommendation = f"Evolve {worst_file[0]} (lowest avg fitness: {worst_file[1]:.1f})"

        return tree

    def _scan_dir(self, dir_path: Path, root_path: Path) -> DirNode:
        """Recursively scan a directory."""
        try:
            rel = str(dir_path.relative_to(root_path)).replace("\\", "/")
        except ValueError:
            rel = dir_path.name
        if rel == ".":
            rel = ""

        node = DirNode(name=dir_path.name, rel_path=rel)

        try:
            entries = sorted(dir_path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return node

        for entry in entries:
            if entry.is_dir():
                if entry.name in SKIP_DIRS or entry.name.startswith("."):
                    continue
                child = self._scan_dir(entry, root_path)
                # Only add non-empty directories
                if child.children_dirs or child.children_files:
                    node.children_dirs.append(child)

            elif entry.is_file() and entry.suffix == ".py":
                if entry.name.startswith("."):
                    continue
                file_node = self._analyze_file(entry, root_path)
                node.children_files.append(file_node)

        return node

    def _analyze_file(self, file_path: Path, root_path: Path) -> FileNode:
        """Analyze a single Python file and return a FileNode."""
        try:
            rel = str(file_path.relative_to(root_path)).replace("\\", "/")
        except ValueError:
            rel = file_path.name

        fnode = FileNode(
            name=file_path.name,
            rel_path=rel,
            abs_path=str(file_path),
        )

        try:
            all_funcs = FileIngestor.extract(file_path, include_non_evolvable=True)
            evolvable = [f for f in all_funcs if f.evolvable]

            fnode.total_functions = len(all_funcs)
            fnode.evolvable_functions = len(evolvable)

            # Collect class names
            classes = set()
            for f in all_funcs:
                if f.class_name:
                    classes.add(f.class_name)
            fnode.classes = sorted(classes)

            # Build function info list
            fitness_scores: list[float] = []
            for f in all_funcs:
                fi = FunctionInfo(
                    name=f.name,
                    qualified_name=f.qualified_name or f.name,
                    lines_of_code=f.lines_of_code,
                    evolvable=f.evolvable,
                    skip_reason=f.skip_reason,
                    is_method=f.is_method,
                    class_name=f.class_name,
                )
                fnode.functions.append(fi)

            if fitness_scores:
                fnode.avg_fitness = sum(fitness_scores) / len(fitness_scores)

        except Exception as e:
            fnode.error = str(e)

        return fnode

    # ── Helpers ────────────────────────────────────────────────────

    def _collect_files(self, node: DirNode) -> list[FileNode]:
        """Flatten all FileNodes from a directory tree."""
        files = list(node.children_files)
        for child in node.children_dirs:
            files.extend(self._collect_files(child))
        return files

    def tree_to_dict(self, tree: ProjectTree) -> dict[str, Any]:
        """Serialize a ProjectTree to a JSON-safe dictionary."""
        return {
            "project_name": tree.project_name,
            "root_path": tree.root_path,
            "total_files": tree.total_files,
            "total_functions": tree.total_functions,
            "total_classes": tree.total_classes,
            "total_evolvable": tree.total_evolvable,
            "avg_fitness": round(tree.avg_fitness, 1) if tree.avg_fitness else None,
            "fitness_excellent": tree.fitness_excellent,
            "fitness_fair": tree.fitness_fair,
            "fitness_poor": tree.fitness_poor,
            "recommendation": tree.recommendation,
            "tree": self._dir_to_dict(tree.root) if tree.root else None,
        }

    def _dir_to_dict(self, node: DirNode) -> dict:
        return {
            "type": "directory",
            "name": node.name,
            "path": node.rel_path,
            "children": [
                self._dir_to_dict(d) for d in node.children_dirs
            ] + [
                self._file_to_dict(f) for f in node.children_files
            ],
        }

    def _file_to_dict(self, node: FileNode) -> dict:
        # Compute fitness indicator
        indicator = None
        if node.avg_fitness is not None:
            if node.avg_fitness >= 75:
                indicator = "excellent"
            elif node.avg_fitness >= 50:
                indicator = "fair"
            else:
                indicator = "poor"

        return {
            "type": "file",
            "name": node.name,
            "path": node.rel_path,
            "total_functions": node.total_functions,
            "evolvable_functions": node.evolvable_functions,
            "classes": node.classes,
            "avg_fitness": round(node.avg_fitness, 1) if node.avg_fitness else None,
            "fitness_indicator": indicator,
            "error": node.error,
            "functions": [
                {
                    "name": f.name,
                    "qualified_name": f.qualified_name,
                    "lines_of_code": f.lines_of_code,
                    "evolvable": f.evolvable,
                    "skip_reason": f.skip_reason,
                    "is_method": f.is_method,
                    "class_name": f.class_name,
                    "fitness_score": f.fitness_score,
                    "evolution_count": f.evolution_count,
                    "frozen": f.frozen,
                }
                for f in node.functions
            ],
        }

    def list_projects(self) -> list[dict]:
        """List all ingested projects."""
        projects = []
        if not self.projects_dir.exists():
            return projects
        for d in self.projects_dir.iterdir():
            if d.is_dir() and not d.name.startswith("."):
                projects.append({
                    "id": d.name,
                    "path": str(d),
                    "name": d.name,
                })
        return projects

    def delete_project(self, project_id: str) -> bool:
        """Delete an ingested project."""
        project_dir = self.projects_dir / project_id
        if project_dir.exists() and project_dir.is_dir():
            shutil.rmtree(project_dir)
            return True
        return False
