"""
Health Score — Calculates an overall 0-100 score for the project based on complexity,
duplication, dead code, and runtime properties.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict

from hezgene.core.dna_tracker import DNATracker
from hezgene.analysis.dead_code import DeadCodeScanner
from hezgene.analysis.duplication import DuplicationScanner


@dataclass
class RefactorTarget:
    qualified_name: str
    complexity: int
    maintainability_index: float
    reason: str


@dataclass
class HealthReport:
    score: int
    grade: str
    total_functions: int
    dead_code_count: int
    duplicate_groups: int
    avg_complexity: float
    avg_maintainability: float
    refactor_targets: List[RefactorTarget]


class HealthScanner:
    """Calculates overall project health and identifies refactoring targets."""

    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.dna_tracker = DNATracker(project_root)

    def scan(self, changed_files: List[str] | None = None) -> HealthReport:
        all_dna = self.dna_tracker.get_all_tracked()
        
        if changed_files is not None:
            # Filter DNA targets that match the changed files
            filtered_dna = []
            for target in all_dna:
                file_part = target.split(":")[0] if ":" in target else target
                # Basic matching: if any changed file path is part of the target path
                if any(cf.endswith(file_part) or file_part.endswith(cf) for cf in changed_files):
                    filtered_dna.append(target)
            all_dna = filtered_dna

        total_functions = len(all_dna)

        # 1. Complexity & Maintainability Metrics
        total_complexity = 0
        total_mi = 0.0
        targets = []

        for target in all_dna:
            dna = self.dna_tracker.get_dna(target)
            if not dna:
                continue

            total_complexity += dna.cyclomatic_complexity
            total_mi += dna.maintainability_index

            # Identify refactor targets (e.g., complexity > 10 or MI < 65)
            if dna.cyclomatic_complexity > 10 or dna.maintainability_index < 65.0:
                targets.append(
                    RefactorTarget(
                        qualified_name=dna.qualified_name,
                        complexity=dna.cyclomatic_complexity,
                        maintainability_index=dna.maintainability_index,
                        reason="High complexity" if dna.cyclomatic_complexity > 10 else "Low maintainability"
                    )
                )

        if total_functions > 0:
            avg_complexity = total_complexity / total_functions
            avg_mi = total_mi / total_functions
        else:
            avg_complexity = 0.0
            avg_mi = 100.0

        # Sort targets by lowest maintainability index first
        targets.sort(key=lambda t: t.maintainability_index)

        # 2. Dead Code Penalty
        try:
            dead_scanner = DeadCodeScanner(self.project_root)
            dead_findings = dead_scanner.scan()
            if changed_files is not None:
                dead_findings = [f for f in dead_findings if any(cf.endswith(f.file_path) or f.file_path.endswith(cf) for cf in changed_files)]
            dead_code_count = len(dead_findings)
        except Exception:
            dead_code_count = 0

        # 3. Duplication Penalty
        try:
            dupes_scanner = DuplicationScanner(self.project_root)
            dupe_groups = dupes_scanner.scan()
            if changed_files is not None:
                filtered_groups = []
                for g in dupe_groups:
                    # Keep group if any of its functions are in changed files
                    if any(any(cf.endswith(f["file_path"]) or f["file_path"].endswith(cf) for cf in changed_files) for f in g.functions):
                        filtered_groups.append(g)
                dupe_groups = filtered_groups
            duplicate_groups = len(dupe_groups)
        except Exception:
            duplicate_groups = 0

        # Calculate Score (0-100)
        # Base score starts at avg maintainability index (usually 0-100)
        score = avg_mi

        # Penalties
        score -= (avg_complexity * 1.5)  # Penalize high average complexity
        score -= min(30, dead_code_count * 2)  # Up to 30 points off for dead code
        score -= min(30, duplicate_groups * 5)  # Up to 30 points off for duplication

        final_score = max(0, min(100, int(score)))

        # Determine Grade
        if final_score >= 90:
            grade = "A"
        elif final_score >= 80:
            grade = "B"
        elif final_score >= 70:
            grade = "C"
        elif final_score >= 60:
            grade = "D"
        else:
            grade = "F"

        return HealthReport(
            score=final_score,
            grade=grade,
            total_functions=total_functions,
            dead_code_count=dead_code_count,
            duplicate_groups=duplicate_groups,
            avg_complexity=round(avg_complexity, 2),
            avg_maintainability=round(avg_mi, 2),
            refactor_targets=targets[:10]  # Top 10 targets
        )
