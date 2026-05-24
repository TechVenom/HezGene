"""
HezGene Web — Background evolution worker with WebSocket streaming.

Runs the actual EvolutionEngine pipeline and streams each stage
to the connected WebSocket client in real-time.
"""

from __future__ import annotations

# ruff: noqa: E501
import asyncio
import time
import traceback
import gc
import psutil
import os
from pathlib import Path
from typing import Any

from hezgene.analysis.file_ingestor import FileIngestor
from ..core.dna_tracker import DNATracker
from ..deployment.deployer import AutoDeployer
from ..evaluation.gauntlet import FitnessGauntlet
from ..evaluation.tournament import TournamentManager
from ..mutation.ast_mutator import MutationEngine
from .websocket import manager

# In-memory session store
sessions: dict[str, dict[str, Any]] = {}

# Global state for project evolution (to support pause/resume/cancel)
# project_evolution_state[session_id] = "running" | "paused" | "cancelled"
project_evolution_state: dict[str, str] = {}



async def run_evolution(
    session_id: str,
    file_path: str,
    function_name: str | None,
    use_llm: bool,
    apply: bool,
    generations: int,
    project_root: str = ".",
):
    """
    Run a full evolution cycle and stream updates via WebSocket.

    Stages sent over WS:
      - extracting_dna
      - spawning_mutants (one per mutant spawned)
      - arena_fight (per-ring results)
      - winner_selected / no_improvement
      - deploying (if apply=True)
      - complete
      - error
    """
    sessions[session_id] = {
        "status": "running",
        "file_id": file_path,
        "function_name": function_name,
        "started_at": time.time(),
        "result": None,
    }

    # Give the WebSocket time to connect
    await asyncio.sleep(0.8)

    try:
        tracker = DNATracker(project_root)
        mutation_engine = MutationEngine()
        gauntlet = FitnessGauntlet()
        tournament = TournamentManager()
        deployer = AutoDeployer(project_root)

        # Resolve path
        if file_path == ".":
            from hezgene.analysis.project_scanner import ProjectScanner
            targets = ProjectScanner(project_root).scan_directory(Path(project_root))
            
            funcs_to_evolve = []
            for t in targets:
                fpath, func_name = t.split(":")
                extracted = FileIngestor.extract(Path(project_root) / fpath)
                for f in extracted:
                    if f.name == func_name or f.qualified_name == func_name:
                        funcs_to_evolve.append((fpath, f))
                        break
                        
            if not funcs_to_evolve:
                await manager.send(
                    session_id,
                    {
                        "stage": "error",
                        "message": "No evolvable functions found in project",
                    },
                )
                sessions[session_id]["status"] = "error"
                return
        else:
            full_path = Path(project_root) / file_path
            if not full_path.exists():
                # Try uploads dir
                upload_path = Path(project_root) / ".hezgene" / "uploads" / file_path
                if upload_path.exists():
                    full_path = upload_path
                else:
                    await manager.send(
                        session_id,
                        {
                            "stage": "error",
                            "message": f"File not found: {file_path}",
                        },
                    )
                    sessions[session_id]["status"] = "error"
                    return

            # Extract functions
            funcs = FileIngestor.extract(full_path)
            if not funcs:
                await manager.send(
                    session_id,
                    {
                        "stage": "error",
                        "message": f"No evolvable functions found in {file_path}",
                    },
                )
                sessions[session_id]["status"] = "error"
                return

            # Filter to specific function if requested
            if function_name:
                funcs = [
                    f for f in funcs if f.name == function_name or f.qualified_name == function_name
                ]
                if not funcs:
                    await manager.send(
                        session_id,
                        {
                            "stage": "error",
                            "message": f"Function '{function_name}' not found or not evolvable",
                        },
                    )
                    sessions[session_id]["status"] = "error"
                    return
            
            funcs_to_evolve = [(file_path, f) for f in funcs]

        all_results = []

        for current_file_path, func in funcs_to_evolve:
            entity = f"{func.class_name}.{func.name}" if func.class_name else func.name
            target = f"{current_file_path}:{entity}"

            # ── Stage: Extracting DNA ──
            await manager.send(
                session_id,
                {
                    "stage": "extracting_dna",
                    "function": entity,
                    "message": f"Extracting DNA for {entity}...",
                },
            )
            await asyncio.sleep(0.3)

            dna = await asyncio.to_thread(tracker.extract, target, override_source=func.source_code)

            # Evaluate baseline
            baseline_result = await asyncio.to_thread(gauntlet._evaluate_single, dna, dna)
            dna.avg_execution_time_ms = baseline_result.avg_speed_ms
            dna.peak_memory_bytes = baseline_result.peak_memory_bytes
            dna.readability_score = baseline_result.readability_score

            await manager.send(
                session_id,
                {
                    "stage": "dna_extracted",
                    "function": entity,
                    "dna": {
                        "fitness_score": round(dna.fitness_score, 2),
                        "speed_ms": (
                            round(dna.avg_execution_time_ms, 4)
                            if dna.avg_execution_time_ms != float("inf")
                            else -1.0
                        ),
                        "memory_bytes": dna.peak_memory_bytes,
                        "complexity": dna.cyclomatic_complexity,
                        "loc": dna.lines_of_code,
                        "readability": round(dna.readability_score, 2),
                    },
                    "original_source": dna.source_code,
                },
            )
            await asyncio.sleep(0.2)

            # ── Stage: Spawning Mutants ──
            await manager.send(
                session_id,
                {
                    "stage": "spawning_mutants",
                    "function": entity,
                    "message": f"Spawning mutants for {entity}...",
                },
            )

            mutants = await asyncio.to_thread(mutation_engine.spawn, dna, count=generations)

            # LLM mutations if requested
            llm_mutants = []
            if use_llm:
                try:
                    from ..core.config import HezGeneConfig
                    from hezgene.mutation.llm import get_provider
                    from hezgene.mutation.llm_mutator import LLMMutator

                    cfg = HezGeneConfig(project_root)
                    provider_name = cfg.get_llm_provider_name()
                    llm_kwargs = cfg.get_llm_config()
                    provider = get_provider(provider_name, **llm_kwargs)
                    llm_mut = LLMMutator(provider)
                    # Use asyncio.to_thread so we don't block the FastAPI event loop during slow LLM calls
                    llm_mutants = await asyncio.to_thread(llm_mut.spawn, dna, generations)
                    mutants.extend(llm_mutants)
                except Exception as e:
                    await manager.send(
                        session_id,
                        {
                            "stage": "spawning_mutants",
                            "function": entity,
                            "warning": f"LLM mutations failed: {str(e)}",
                        },
                    )

            # Stream each mutant as it's "spawned"
            for idx, m in enumerate(mutants):
                await manager.send(
                    session_id,
                    {
                        "stage": "mutant_spawned",
                        "function": entity,
                        "mutant": {
                            "id": m.id,
                            "index": idx,
                            "strategy": m.strategy,
                            "source_code": m.source_code,
                            "loc": m.dna.lines_of_code,
                            "complexity": m.dna.cyclomatic_complexity,
                        },
                    },
                )
                await asyncio.sleep(0.15)

            if not mutants:
                await manager.send(
                    session_id,
                    {
                        "stage": "no_mutants",
                        "function": entity,
                        "message": f"No valid mutants could be generated for {entity}",
                    },
                )
                continue

            # ── Stage: Arena Fight ──
            await manager.send(
                session_id,
                {
                    "stage": "arena_fight",
                    "function": entity,
                    "message": f"Running {len(mutants)} mutants through the Fitness Gauntlet...",
                    "total_mutants": len(mutants),
                },
            )
            await asyncio.sleep(0.2)

            results = await asyncio.to_thread(gauntlet.evaluate, original=dna, mutants=mutants)

            # Stream ring results per mutant
            battle_results = []
            for i, r in enumerate(results):
                strategy = (
                    getattr(mutants[i], "strategy", "unknown") if i < len(mutants) else "unknown"
                )
                entry = {
                    "rank": 0,
                    "mutant_id": r.mutant_id,
                    "strategy": strategy,
                    "passed": r.passed_correctness and not r.disqualified,
                    "disqualified": r.disqualified,
                    "disqualify_reason": r.disqualify_reason,
                    "score": round(r.overall_score, 2),
                    "speed_ms": (
                        round(r.avg_speed_ms, 4) if r.avg_speed_ms != float("inf") else -1.0
                    ),
                    "memory_bytes": r.peak_memory_bytes,
                    "readability": round(r.readability_score, 2),
                    "edge_failures": r.edge_case_failures,
                }
                battle_results.append(entry)

                await manager.send(
                    session_id,
                    {
                        "stage": "fight_result",
                        "function": entity,
                        "mutant_result": entry,
                        "mutant_index": i,
                    },
                )
                await asyncio.sleep(0.1)

            # Rank them
            ranked = sorted(battle_results, key=lambda x: x["score"], reverse=True)
            for i, entry in enumerate(ranked):
                entry["rank"] = i + 1

            await manager.send(
                session_id,
                {
                    "stage": "arena_ranked",
                    "function": entity,
                    "rankings": ranked,
                    "baseline_score": round(dna.fitness_score, 2),
                },
            )

            # ── Stage: Select Winner ──
            winner = await asyncio.to_thread(tournament.select_winner, dna, results)

            if winner and winner != dna:
                improvements = tournament.compare(dna, winner)

                # Find winning mutant index/strategy
                winner_strategy = "unknown"
                winner_source = winner.source_code
                for i, r in enumerate(results):
                    if r.dna and r.dna == winner:
                        winner_strategy = (
                            getattr(mutants[i], "strategy", "unknown")
                            if i < len(mutants)
                            else "unknown"
                        )
                        break

                improvement_pct = (
                    (improvements["fitness_after"] - improvements["fitness_before"])
                    / max(abs(improvements["fitness_before"]), 0.001)
                ) * 100

                await manager.send(
                    session_id,
                    {
                        "stage": "winner_selected",
                        "function": entity,
                        "winner": {
                            "strategy": winner_strategy,
                            "improvement": f"+{improvement_pct:.1f}%",
                            "improvement_pct": round(improvement_pct, 1),
                            "fitness_before": round(improvements["fitness_before"], 2),
                            "fitness_after": round(improvements["fitness_after"], 2),
                            "speed_before": (
                                round(improvements["speed_before"], 4)
                                if improvements["speed_before"] != float("inf")
                                else -1.0
                            ),
                            "speed_after": (
                                round(improvements["speed_after"], 4)
                                if improvements["speed_after"] != float("inf")
                                else -1.0
                            ),
                            "memory_before": improvements["memory_before"],
                            "memory_after": improvements["memory_after"],
                            "evolved_source": winner_source,
                        },
                        "original_source": dna.source_code,
                    },
                )

                # Deploy if requested
                if apply:
                    await manager.send(
                        session_id,
                        {
                            "stage": "deploying",
                            "function": entity,
                            "message": f"Deploying winner to {file_path}...",
                        },
                    )
                    await asyncio.sleep(0.3)

                    try:
                        await asyncio.to_thread(deployer.deploy, target, winner)
                        await asyncio.to_thread(tracker.record_evolution, target, dna, winner)
                        await manager.send(
                            session_id,
                            {
                                "stage": "deployed",
                                "function": entity,
                                "message": f"Successfully deployed evolved {entity}",
                            },
                        )
                    except Exception as e:
                        await manager.send(
                            session_id,
                            {
                                "stage": "deploy_failed",
                                "function": entity,
                                "message": f"Deployment failed: {str(e)}",
                            },
                        )
                else:
                    # Write to sandbox
                    sandbox_dir = Path(project_root) / ".hezgene" / "sandbox"
                    sandbox_dir.mkdir(parents=True, exist_ok=True)
                    safe_name = (
                        target.replace("/", "_")
                        .replace("\\", "_")
                        .replace(":", "__")
                        .replace(".", "_")
                    )
                    (sandbox_dir / f"{safe_name}_evolved.py").write_text(
                        f"# EVOLVED: {target}\n\n{winner_source}\n", encoding="utf-8"
                    )

                func_result = {
                    "status": "evolved",
                    "function": entity,
                    "improvements": improvements,
                    "battle_results": ranked,
                    "total_mutants": len(mutants),
                    "applied": apply,
                }
            else:
                await manager.send(
                    session_id,
                    {
                        "stage": "no_improvement",
                        "function": entity,
                        "message": f"No mutant beat the original for {entity}",
                        "baseline_score": round(dna.fitness_score, 2),
                    },
                )

                func_result = {
                    "status": "unchanged",
                    "function": entity,
                    "reason": "No mutant beat the original",
                    "battle_results": ranked,
                    "total_mutants": len(mutants),
                }

            all_results.append(func_result)
            
            # Memory Cleanup
            gc.collect()
            process = psutil.Process(os.getpid())
            mem_mb = process.memory_info().rss / 1024 / 1024
            if mem_mb > 1000:
                print(f"[HezGene] WARNING: High memory usage ({mem_mb:.0f}MB). Forcing cleanup.")
                gc.collect()

        # ── Stage: Complete ──
        evolved_count = sum(1 for r in all_results if r["status"] == "evolved")
        await manager.send(
            session_id,
            {
                "stage": "complete",
                "message": f"Evolution complete! {evolved_count}/{len(all_results)} functions improved.",
                "results": all_results,
            },
        )

        sessions[session_id]["status"] = "complete"
        sessions[session_id]["result"] = all_results

    except Exception as e:
        tb = traceback.format_exc()
        await manager.send(
            session_id,
            {
                "stage": "error",
                "message": f"Evolution error: {str(e)}",
                "traceback": tb,
            },
        )
        sessions[session_id]["status"] = "error"
        sessions[session_id]["result"] = {"error": str(e)}


async def run_project_evolution(
    session_id: str,
    project_path: str,
    file_path: str | None,
    use_llm: bool,
    apply: bool,
    generations: int,
    project_root: str = ".",
):
    """
    Run evolution on an entire project or file, emitting project-level WS events
    for live progress tracking.
    """
    sessions[session_id] = {
        "status": "running",
        "project_path": project_path,
        "file_path": file_path,
        "started_at": time.time(),
        "result": None,
    }
    project_evolution_state[session_id] = "running"

    await asyncio.sleep(0.8)

    try:
        from hezgene.project.project_manager import ProjectManager
        pm = ProjectManager(project_root)
        
        # Determine actual root
        if project_path == ".":
            actual_root = Path(project_root)
        else:
            projects_dir = pm.projects_dir / project_path
            if projects_dir.exists():
                actual_root = projects_dir
            else:
                actual_root = Path(project_root) / project_path

        # Build tree to get all files
        tree = pm.build_tree(actual_root)
        
        all_files = pm._collect_files(tree.root)
        if file_path:
            # Filter to specific file if requested
            all_files = [f for f in all_files if f.rel_path == file_path]

        # Flatten all evolvable functions into a queue
        functions_queue = []
        for fnode in all_files:
            for func in fnode.functions:
                if func.evolvable and not func.frozen:
                    functions_queue.append((fnode, func))

        total_functions = len(functions_queue)
        completed_functions = 0
        
        await manager.send(
            session_id,
            {
                "stage": "project_started",
                "project_name": tree.project_name,
                "total_functions": total_functions,
            }
        )

        all_results = []
        
        for fnode, func in functions_queue:
            # Check state
            while project_evolution_state.get(session_id) == "paused":
                await asyncio.sleep(1.0)
            
            if project_evolution_state.get(session_id) == "cancelled":
                await manager.send(
                    session_id,
                    {"stage": "project_cancelled", "message": "Evolution cancelled by user."}
                )
                sessions[session_id]["status"] = "cancelled"
                return

            entity = f"{func.class_name}.{func.name}" if func.class_name else func.name
            target = f"{fnode.rel_path}:{entity}"
            
            await manager.send(
                session_id,
                {
                    "stage": "function_started",
                    "file_path": fnode.rel_path,
                    "function": entity,
                    "message": f"Evolving {entity}...",
                    "progress": completed_functions,
                    "total": total_functions,
                }
            )

            # We reuse the single evolution logic but just run it inline, stripped down for project mode
            # For simplicity, we just call run_evolution in a sub-task but intercept the WS messages?
            # Actually, it's better to just instantiate engines here and evolve.
            
            tracker = DNATracker(project_root)
            mutation_engine = MutationEngine()
            gauntlet = FitnessGauntlet()
            tournament = TournamentManager()
            deployer = AutoDeployer(project_root)
            
            try:
                dna = await asyncio.to_thread(tracker.extract, target, override_source=func.source_code)
                baseline_result = await asyncio.to_thread(gauntlet._evaluate_single, dna, dna)
                dna.avg_execution_time_ms = baseline_result.avg_speed_ms
                dna.peak_memory_bytes = baseline_result.peak_memory_bytes
                
                await manager.send(session_id, {"stage": "spawning_mutants", "function": entity})
                mutants = await asyncio.to_thread(mutation_engine.spawn, dna, count=generations)
                
                if use_llm:
                    try:
                        from ..core.config import HezGeneConfig
                        from hezgene.mutation.llm import get_provider
                        from hezgene.mutation.llm_mutator import LLMMutator

                        cfg = HezGeneConfig(project_root)
                        provider_name = cfg.get_llm_provider_name()
                        llm_kwargs = cfg.get_llm_config()
                        provider = get_provider(provider_name, **llm_kwargs)
                        llm_mut = LLMMutator(provider)
                        llm_mutants = await asyncio.to_thread(llm_mut.spawn, dna, generations)
                        mutants.extend(llm_mutants)
                    except Exception as e:
                        pass
                
                await manager.send(session_id, {"stage": "arena_fight", "function": entity})
                results = await asyncio.to_thread(gauntlet.evaluate, original=dna, mutants=mutants)
                winner = await asyncio.to_thread(tournament.select_winner, dna, results)
                
                if winner and winner != dna:
                    improvements = tournament.compare(dna, winner)
                    if apply:
                        await asyncio.to_thread(deployer.deploy, target, winner)
                        await asyncio.to_thread(tracker.record_evolution, target, dna, winner)
                    else:
                        sandbox_dir = Path(project_root) / ".hezgene" / "sandbox"
                        sandbox_dir.mkdir(parents=True, exist_ok=True)
                        safe_name = target.replace("/", "_").replace("\\", "_").replace(":", "__").replace(".", "_")
                        (sandbox_dir / f"{safe_name}_evolved.py").write_text(
                            f"# EVOLVED: {target}\n\n{winner.source_code}\n", encoding="utf-8"
                        )

                    func_result = {"status": "evolved", "improvements": improvements, "applied": apply}
                    await manager.send(
                        session_id,
                        {
                            "stage": "function_complete",
                            "file_path": fnode.rel_path,
                            "function": entity,
                            "status": "evolved",
                            "improvements": improvements,
                        }
                    )
                else:
                    func_result = {"status": "unchanged", "reason": "No improvement"}
                    await manager.send(
                        session_id,
                        {
                            "stage": "function_complete",
                            "file_path": fnode.rel_path,
                            "function": entity,
                            "status": "unchanged",
                        }
                    )
                all_results.append((target, func_result))
            except Exception as e:
                await manager.send(
                    session_id,
                    {
                        "stage": "function_error",
                        "file_path": fnode.rel_path,
                        "function": entity,
                        "error": str(e),
                    }
                )
                all_results.append((target, {"status": "error", "error": str(e)}))

            completed_functions += 1
            
            # GC
            gc.collect()
            process = psutil.Process(os.getpid())
            mem_mb = process.memory_info().rss / 1024 / 1024
            if mem_mb > 1000:
                gc.collect()

        await manager.send(
            session_id,
            {
                "stage": "project_complete",
                "message": f"Project evolution complete! Processed {completed_functions} functions.",
                "results": all_results,
            }
        )
        sessions[session_id]["status"] = "complete"
        sessions[session_id]["result"] = all_results

    except Exception as e:
        tb = traceback.format_exc()
        await manager.send(session_id, {"stage": "error", "message": f"Evolution error: {str(e)}", "traceback": tb})
        sessions[session_id]["status"] = "error"
        sessions[session_id]["result"] = {"error": str(e)}

