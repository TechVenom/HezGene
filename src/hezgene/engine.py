from __future__ import annotations

from pathlib import Path

from .analysis.file_ingestor import FileIngestor
from .analysis.project_scanner import ProjectScanner
from .core.dna_tracker import DNATracker
from .deployment.deployer import AutoDeployer
from .evaluation.gauntlet import FitnessGauntlet
from .evaluation.tournament import TournamentManager
from .mutation.ast_mutator import MutationEngine
from .mutation.llm import get_provider, list_providers
from .mutation.llm_mutator import LLMMutator


class EvolutionEngine:
    """
    Main orchestrator for genetic evolution.

    Supports both AST-based mutations and optional LLM-powered mutations.
    """

    def __init__(
        self,
        project_root: str = ".",
        config: dict | None = None,
        use_llm: bool = False,
        llm_only: bool = False,
        llm_provider: str = "",
        llm_model: str = "",
    ):
        self.project_root = project_root
        self.config = config or {}
        self.use_llm = use_llm
        self.llm_only = llm_only

        # Core components — always available.
        self.dna_tracker = DNATracker(project_root)
        self.mutation_engine = MutationEngine()
        self.gauntlet = FitnessGauntlet()
        self.tournament = TournamentManager()
        self.deployer = AutoDeployer(project_root)
        self.scanner = ProjectScanner(project_root, self.dna_tracker)

        # LLM configuration
        self._llm_provider_name = llm_provider
        self._llm_model = llm_model
        self._cfg = None
        self._load_config()

        # LLM mutator is always available (even if the provider is not configured).
        provider_name = (self._llm_provider_name or "ollama").lower()
        available = set(list_providers())
        if provider_name not in available:
            provider_name = "ollama"

        kwargs = {}
        if self._cfg:
            kwargs = self._cfg.get_llm_config()
        if self._llm_model:
            kwargs["model"] = self._llm_model

        self.llm_provider = get_provider(provider_name, **kwargs)
        self.llm_mutator = LLMMutator(self.llm_provider)

    def _load_config(self) -> None:
        """Load LLM settings from .hezgene/config.json if not set via constructor."""
        try:
            from .core.config import HezGeneConfig

            cfg = HezGeneConfig(self.project_root)

            # Constructor args take priority over config file
            if not self.use_llm:
                self.use_llm = cfg.is_llm_enabled()
            if not self._llm_provider_name:
                self._llm_provider_name = cfg.get_llm_provider_name()
            if not self._llm_model:
                self._llm_model = cfg.get("llm.model", "")

            self._cfg = cfg
        except Exception:
            self._cfg = None

    def scan_file(self, path: str) -> dict:
        """
        Scan a single Python file and return evolvable functions with basic DNA hints.

        Returns:
            {
              "file": "<absolute path>",
              "functions": {
                "<name>": {
                  "start_line": int,
                  "end_line": int,
                  "lines_of_code": int,
                  "cyclomatic_complexity": int,
                  "maintainability_index": float,
                  "fitness_hint": float
                },
                ...
              }
            }
        """
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = Path(self.project_root) / file_path
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        funcs = FileIngestor.extract(file_path)
        results: dict[str, dict] = {}
        for f in funcs:
            name = f"{f.class_name}.{f.name}" if f.class_name else f.name
            fitness_hint = max(
                0.0,
                min(
                    100.0,
                    float(f.maintainability_index) - float(max(0, f.cyclomatic_complexity - 1)) * 2.0,
                ),
            )
            results[name] = {
                "start_line": f.start_line,
                "end_line": f.end_line,
                "lines_of_code": f.lines_of_code,
                "cyclomatic_complexity": f.cyclomatic_complexity,
                "maintainability_index": round(float(f.maintainability_index), 2),
                "fitness_hint": round(float(fitness_hint), 2),
            }

        return {"file": str(file_path), "functions": results}

    def evolve(
        self, target: str, generations: int = 5, apply: bool = False, use_llm: bool = False
    ) -> list[dict] | dict:
        """
        Run evolution cycle.

        Public API note:
          - `use_llm` is a per-call toggle. When False (default), only AST mutations are used.
        """
        # The public API supports a per-run `use_llm` toggle.
        prev_use_llm = self.use_llm
        prev_llm_only = self.llm_only
        self.use_llm = bool(use_llm)
        if not use_llm:
            self.llm_only = False

        try:
            # Handle 'slowest' or 'buggiest' directly
            if target in ["slowest", "buggiest"]:
                ranked = self.scanner.get_ranked_targets(metric=target, limit=1)
                if not ranked:
                    return {"status": "error", "reason": f"No targets found for metric {target}"}
                target = ranked[0]

            target_path = Path(self.project_root) / target.split(":")[0]

            # Is it a directory?
            if target_path.is_dir():
                targets = self.scanner.scan_directory(target_path)
                return [self._evolve_single(t, generations, apply) for t in targets]

            # Is it a full file without a specific function?
            if ":" not in target:
                if not target_path.is_file():
                    raise FileNotFoundError(f"Target file not found: {target_path.resolve()}")
                funcs = FileIngestor.extract(target_path)
                results = []
                for f in funcs:
                    entity = f"{f.class_name}.{f.name}" if f.class_name else f.name
                    results.append(
                        self._evolve_single(f"{target}:{entity}", generations, apply, f.source_code)
                    )
                return results

            # Otherwise it's a specific function
            return self._evolve_single(target, generations, apply)
        finally:
            self.use_llm = prev_use_llm
            self.llm_only = prev_llm_only

    def _evolve_single(
        self, target: str, generations: int, apply: bool, source_code: str | None = None
    ) -> dict:
        # Step 1: Extract the function's current DNA
        dna = self.dna_tracker.extract(target, override_source=source_code)
        original_source = dna.source_code

        # Read the full module source for context injection
        file_path = target.split(":")[0]
        try:
            full_module_source = Path(Path(self.project_root) / file_path).read_text(encoding="utf-8")
        except Exception:
            full_module_source = None
        self.gauntlet.module_source = full_module_source

        # --- Evaluate baseline of original ---
        baseline_result = self.gauntlet._evaluate_single(dna, dna)
        dna.avg_execution_time_ms = baseline_result.avg_speed_ms
        dna.peak_memory_bytes = baseline_result.peak_memory_bytes
        dna.readability_score = baseline_result.readability_score

        baseline_info = {
            "fitness": dna.fitness_score,
            "speed_ms": baseline_result.avg_speed_ms,
            "memory_bytes": baseline_result.peak_memory_bytes,
            "readability": baseline_result.readability_score,
        }

        # Step 2: Spawn mutant versions
        mutants = []
        spawn_log = []

        # AST-based mutations (unless llm_only)
        if not self.llm_only:
            ast_mutants = self.mutation_engine.spawn(dna, count=generations)
            mutants.extend(ast_mutants)
            spawn_log.append({"type": "AST", "count": len(ast_mutants)})

        # LLM-powered mutations (if enabled)
        if self.use_llm or self.llm_only:
            try:
                llm_mutants = self.llm_mutator.spawn(dna, count=generations)
                mutants.extend(llm_mutants)
                spawn_log.append(
                    {"type": "LLM", "count": len(llm_mutants), "provider": self.llm_provider.provider_name}
                )
            except Exception as e:
                spawn_log.append({"type": "LLM", "count": 0, "error": str(e)})

        # Step 3: Run the gauntlet — test each mutant
        results = self.gauntlet.evaluate(original=dna, mutants=mutants)

        # Build full battle report
        battle_results = []
        for i, r in enumerate(results):
            entry = {
                "rank": 0,
                "mutant_id": r.mutant_id,
                "strategy": getattr(mutants[i], "strategy", "ast") if i < len(mutants) else "unknown",
                "passed": r.passed_correctness and not r.disqualified,
                "disqualified": r.disqualified,
                "disqualify_reason": r.disqualify_reason,
                "score": r.overall_score,
                "speed_ms": r.avg_speed_ms,
                "memory_bytes": r.peak_memory_bytes,
                "readability": r.readability_score,
                "edge_failures": r.edge_case_failures,
            }
            battle_results.append(entry)

        # Rank them
        ranked = sorted(battle_results, key=lambda x: x["score"], reverse=True)
        for i, entry in enumerate(ranked):
            entry["rank"] = i + 1

        # Step 4: Tournament — pick the winner
        winner = self.tournament.select_winner(dna, results)

        # Step 5: Sandbox output or deploy
        if winner and winner != dna:
            evolved_source = winner.source_code
            improvements = self.tournament.compare(dna, winner)
            sandbox_path = self._write_sandbox(target, original_source, evolved_source)

            if apply:
                self.deployer.deploy(target, winner)
                self.dna_tracker.record_evolution(target, dna, winner)

            return {
                "status": "evolved",
                "target": target,
                "original_source": original_source,
                "evolved_source": evolved_source,
                "sandbox_path": str(sandbox_path),
                "improvements": improvements,
                "applied": apply,
                "baseline": baseline_info,
                "spawn_log": spawn_log,
                "battle_results": ranked,
                "total_mutants": len(mutants),
            }

        return {
            "status": "unchanged",
            "target": target,
            "original_source": original_source,
            "evolved_source": original_source,
            "reason": "No mutant beat the original.",
            "baseline": baseline_info,
            "spawn_log": spawn_log,
            "battle_results": ranked,
            "total_mutants": len(mutants),
        }

    def _write_sandbox(self, target: str, original: str, evolved: str) -> Path:
        """Write original and evolved code to .hezgene/sandbox/ for comparison."""
        sandbox_dir = Path(self.project_root) / ".hezgene" / "sandbox"
        sandbox_dir.mkdir(parents=True, exist_ok=True)

        safe_name = target.replace("/", "_").replace("\\", "_").replace(":", "__").replace(".", "_")
        orig_file = sandbox_dir / f"{safe_name}_original.py"
        evol_file = sandbox_dir / f"{safe_name}_evolved.py"

        orig_file.write_text(f"# ORIGINAL: {target}\n\n{original}\n", encoding="utf-8")
        evol_file.write_text(f"# EVOLVED: {target}\n\n{evolved}\n", encoding="utf-8")

        return sandbox_dir

    def evolve_all(self, apply: bool = False) -> list[dict]:
        """Evolve all tracked functions in the project."""
        targets = self.dna_tracker.get_all_tracked()
        return [self.evolve(t, apply=apply, use_llm=self.use_llm or self.llm_only) for t in targets]
