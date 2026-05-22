"""
🏆 Tournament Manager — Ranks mutants and selects the winner.

Takes gauntlet results, applies weighted scoring, and determines
which mutant (if any) deserves to replace the original.
"""

from __future__ import annotations

from hezgene.core.dna_tracker import FunctionDNA


class TournamentManager:
    """Selects the best mutant from gauntlet results."""

    def __init__(self, min_improvement: float = 0.001):
        self.min_improvement = min_improvement

    def select_winner(self, original: FunctionDNA, results: list) -> FunctionDNA | None:
        """
        Pick the best mutant that passed all gates.
        Returns None if no mutant beat the original by min_improvement.
        """
        valid = [r for r in results if not r.disqualified and r.passed_correctness]
        if not valid:
            return None

        best = max(valid, key=lambda r: r.overall_score)

        if best.overall_score > original.fitness_score + self.min_improvement:
            # Find the mutant object to get its DNA
            return getattr(best, "dna", None) or self._result_to_dna(best)

        return None

    def compare(self, original: FunctionDNA, winner: FunctionDNA) -> dict:
        """Compare original vs winner DNA and return improvements."""
        return {
            "speed_change_ms": original.avg_execution_time_ms - winner.avg_execution_time_ms,
            "memory_change_bytes": original.peak_memory_bytes - winner.peak_memory_bytes,
            "complexity_change": original.cyclomatic_complexity - winner.cyclomatic_complexity,
            "loc_change": original.lines_of_code - winner.lines_of_code,
            "fitness_before": original.fitness_score,
            "fitness_after": winner.fitness_score,
            "fitness_delta": winner.fitness_score - original.fitness_score,
            "speed_before": original.avg_execution_time_ms,
            "speed_after": winner.avg_execution_time_ms,
            "memory_before": original.peak_memory_bytes,
            "memory_after": winner.peak_memory_bytes,
        }

    def rank_all(self, results: list) -> list[dict]:
        """Rank all mutants by score (including disqualified)."""
        ranked = sorted(results, key=lambda r: r.overall_score, reverse=True)
        return [
            {
                "rank": i + 1,
                "mutant_id": r.mutant_id,
                "score": r.overall_score,
                "passed": r.passed_correctness and not r.disqualified,
                "reason": r.disqualify_reason if r.disqualified else "OK",
            }
            for i, r in enumerate(ranked)
        ]

    @staticmethod
    def _result_to_dna(result) -> FunctionDNA | None:
        """Fallback: extract DNA from result metadata."""
        if hasattr(result, "mutant_id"):
            return FunctionDNA(
                name=result.mutant_id.split("::")[0].rsplit(".", 1)[-1],
                module=result.mutant_id.split("::")[0].rsplit(".", 1)[0],
                qualified_name=result.mutant_id.split("::")[0],
                avg_execution_time_ms=result.avg_speed_ms,
                peak_memory_bytes=result.peak_memory_bytes,
                readability_score=result.readability_score,
            )
        return None
