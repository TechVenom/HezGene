"""
🧬 DNA Tracker — The genetic registry.

Extracts and stores function "DNA": performance metrics, bug history,
complexity scores, dependency maps, and evolution lineage.
"""

from __future__ import annotations

import ast
import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from hezgene.analysis.dependencies import analyze_project_dependencies, calculate_impact_score


@dataclass
class FunctionDNA:
    """Genetic metadata for a single function."""

    name: str
    module: str
    qualified_name: str
    source_hash: str = ""
    source_code: str = ""

    # Performance genes
    avg_execution_time_ms: float = 0.0
    peak_memory_bytes: int = 0
    call_count: int = 0

    # History genes
    bug_count: int = 0
    last_error: str = ""
    evolution_count: int = 0
    created_at: float = field(default_factory=time.time)
    last_evolved_at: float = 0.0

    # Dependency genes
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)

    # Quality genes
    test_coverage: float = 0.0
    cyclomatic_complexity: int = 0
    lines_of_code: int = 0
    readability_score: float = 0.0
    halstead_effort: float = 0.0
    halstead_volume: float = 0.0
    maintainability_index: float = 100.0

    # Advanced Analysis
    time_complexity: str = "Unknown"
    space_complexity: str = "Unknown"
    scalability_score: str = "Unknown"
    leak_detected: bool = False
    uncovered_branches: list[str] = field(default_factory=list)
    impact_score: str = "Low"

    # Evolution control
    frozen: bool = False
    priority: str = "normal"

    def to_dict(self) -> dict[str, Any]:
        import math

        data = asdict(self)
        if math.isinf(data.get("avg_execution_time_ms", 0)):
            data["avg_execution_time_ms"] = 0.0
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FunctionDNA:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @property
    def fitness_score(self) -> float:
        """Composite fitness score (higher is better)."""
        # Better scaling for speed (sensitive to 0-10ms range)
        speed = 100 / (1.0 + (self.avg_execution_time_ms / 10.0))
        memory = 100 / (1.0 + (self.peak_memory_bytes / (50 * 1024)))  # Scale against 50KB
        reliability = max(0, 100 - self.bug_count * 10)
        readability = self.readability_score * 100
        coverage = self.test_coverage * 100
        complexity_pen = min(self.cyclomatic_complexity * 4, 80)

        if self.lines_of_code < 10:
            loc_bonus = 15
        else:
            loc_bonus = max(0, 100 - self.lines_of_code) * 0.1

        # Maintainability and Halstead penalty
        mi_penalty = max(0, 85 - self.maintainability_index) * 0.5
        halstead_pen = min(self.halstead_effort / 1000, 20)

        # Big O Penalties
        big_o_pen = 0
        if "O(n²)" in self.time_complexity or "O(2ⁿ)" in self.time_complexity:
            big_o_pen += 30
        if "O(n²)" in self.space_complexity:
            big_o_pen += 20
        if self.leak_detected:
            big_o_pen += 50

        return (
            speed * 0.20
            + memory * 0.15
            + reliability * 0.20
            + readability * 0.15
            + coverage * 0.10
            - complexity_pen * 0.05
            - mi_penalty
            - halstead_pen
            - big_o_pen
            + loc_bonus
        )


class DNATracker:
    """Manages the genetic registry for all tracked functions."""

    REGISTRY_FILE = ".hezgene/dna_registry.json"

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.registry_path = self.project_root / self.REGISTRY_FILE
        self._registry: dict[str, FunctionDNA] = {}
        self._dep_calls = None
        self._dep_called_by = None
        self._load()

    def _load(self) -> None:
        if self.registry_path.exists():
            raw = json.loads(self.registry_path.read_text(encoding="utf-8"))
            self._registry = {k: FunctionDNA.from_dict(v) for k, v in raw.items()}

    def _save(self) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        raw = {k: v.to_dict() for k, v in self._registry.items()}
        self.registry_path.write_text(json.dumps(raw, indent=2, default=str), encoding="utf-8")

    def extract(self, target: str, override_source: str | None = None) -> FunctionDNA:
        """Extract or refresh DNA for a target function. Format: 'file.py:func' or 'file.py:Class.func'"""  # noqa: E501
        if ":" not in target:
            raise ValueError(f"Target must be 'file_path.py:function_name', got: {target!r}")

        file_path, entity_name = target.split(":", 1)

        source = override_source
        if not source:
            from hezgene.analysis.file_ingestor import FileIngestor

            funcs = FileIngestor.extract_specific(self.project_root / file_path, entity_name)
            if not funcs:
                raise ValueError(f"Could not find {entity_name} in {file_path}")
            source = funcs[0].source_code

        source_hash = hashlib.sha256(source.encode()).hexdigest()

        if target in self._registry:
            dna = self._registry[target]
            dna.source_code = source
            dna.source_hash = source_hash
        else:
            module_name = str(Path(file_path).with_suffix("")).replace("\\", "/").replace("/", ".")
            # Lazy load dependency graph
            if self._dep_calls is None:
                self._dep_calls, self._dep_called_by = analyze_project_dependencies(
                    str(self.project_root)
                )

            func_name = entity_name.split(".")[-1]
            calls = self._dep_calls.get(func_name, [])
            called_by = self._dep_called_by.get(func_name, [])

            cyclomatic_complexity = 0
            halstead_effort = 0.0
            halstead_volume = 0.0
            maintainability_index = 100.0
            lines_of_code = len(source.strip().splitlines())

            if override_source:
                cyclomatic_complexity = self._calc_complexity(source)
                try:
                    import textwrap

                    from hezgene.analysis.complexity import (
                        calculate_halstead_metrics,
                        calculate_maintainability_index,
                    )

                    tree = ast.parse(textwrap.dedent(source))
                    metrics = calculate_halstead_metrics(tree)
                    halstead_effort = metrics["effort"]
                    halstead_volume = metrics["volume"]
                    maintainability_index = calculate_maintainability_index(
                        lines_of_code, cyclomatic_complexity, halstead_volume
                    )
                except Exception:
                    pass
            else:
                cyclomatic_complexity = funcs[0].cyclomatic_complexity
                halstead_effort = funcs[0].halstead_effort
                halstead_volume = funcs[0].halstead_volume
                maintainability_index = funcs[0].maintainability_index

            dna = FunctionDNA(
                name=func_name,
                module=module_name,
                qualified_name=target,
                source_code=source,
                source_hash=source_hash,
                lines_of_code=lines_of_code,
                cyclomatic_complexity=cyclomatic_complexity,
                halstead_effort=halstead_effort,
                halstead_volume=halstead_volume,
                maintainability_index=maintainability_index,
                dependencies=calls,
                dependents=called_by,
                impact_score=calculate_impact_score(called_by),
            )
            self._registry[target] = dna

        self._save()
        return dna

    def record_evolution(self, target: str, old: FunctionDNA, new: FunctionDNA) -> None:
        new.evolution_count = old.evolution_count + 1
        new.last_evolved_at = time.time()
        self._registry[target] = new
        self._save()

    def get_all_tracked(self) -> list[str]:
        return [k for k, v in self._registry.items() if not v.frozen]

    def freeze(self, target: str) -> None:
        if target in self._registry:
            self._registry[target].frozen = True
            self._save()

    def unfreeze(self, target: str) -> None:
        if target in self._registry:
            self._registry[target].frozen = False
            self._save()

    def get_dna(self, target: str) -> FunctionDNA | None:
        return self._registry.get(target)

    def get_evolution_log(self) -> list[dict]:
        entries = []
        for name, dna in self._registry.items():
            entries.append(
                {
                    "target": name,
                    "evolutions": dna.evolution_count,
                    "last_evolved": dna.last_evolved_at,
                    "fitness": dna.fitness_score,
                    "frozen": dna.frozen,
                }
            )
        return sorted(entries, key=lambda e: e["last_evolved"], reverse=True)

    @staticmethod
    def _calc_complexity(source: str) -> int:
        import textwrap

        try:
            tree = ast.parse(textwrap.dedent(source))
        except SyntaxError:
            return 0
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity
