"""
🧬 HezGene Web API — Full FastAPI backend for the HezGene web interface.

Provides REST endpoints for file management, evolution control, DNA analysis,
configuration, and history. WebSocket support for real-time evolution streaming.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import uvicorn
from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    HTTPException,
    Query,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from hezgene.analysis.file_ingestor import FileIngestor
from hezgene.core.config import HezGeneConfig
from hezgene.core.dna_tracker import DNATracker
from hezgene.web.evolution_worker import run_evolution, run_project_evolution, sessions, project_evolution_state
from hezgene.web.models import ConfigUpdate, EvolutionRequest, LLMTestRequest, GitHubConnectRequest, ProjectEvolveRequest
from hezgene.project.project_manager import ProjectManager
from hezgene.web.websocket import manager

# ── App Setup ──────────────────────────────────────────────────────
app = FastAPI(
    title="HezGene API",
    description="The DNA of Software — Autonomous Genetic Evolution Platform",
    version="1.0.0",
)

import time
import psutil
from datetime import datetime

START_TIME = time.time()

@app.get("/api/health")
async def health_check():
    """Frontend pings this to verify server is alive."""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
        "uptime_seconds": time.time() - START_TIME
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Project root — defaults to current working directory but can be overridden
PROJECT_ROOT = os.environ.get("HEZGENE_PROJECT_ROOT", os.getcwd())


def get_tracker() -> DNATracker:
    return DNATracker(PROJECT_ROOT)


def get_config() -> HezGeneConfig:
    return HezGeneConfig(PROJECT_ROOT)


# ══════════════════════════════════════════════════════════════════
# FILE MANAGEMENT
# ══════════════════════════════════════════════════════════════════


@app.post("/api/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """Upload one or more Python files for evolution."""
    upload_dir = Path(PROJECT_ROOT) / ".hezgene" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for file in files:
        if not file.filename.endswith(".py"):
            results.append(
                {
                    "filename": file.filename,
                    "status": "error",
                    "message": "Only .py files are accepted",
                }
            )
            continue

        file_path = upload_dir / file.filename
        content = await file.read()
        file_path.write_bytes(content)

        # Scan the file for functions
        try:
            all_funcs = FileIngestor.extract(file_path, include_non_evolvable=True)
            evolvable = [f for f in all_funcs if f.evolvable]
            results.append(
                {
                    "filename": file.filename,
                    "status": "success",
                    "total_functions": len(all_funcs),
                    "evolvable_functions": len(evolvable),
                    "functions": [
                        {
                            "name": f.qualified_name,
                            "lines": f.lines_of_code,
                            "evolvable": f.evolvable,
                            "skip_reason": f.skip_reason,
                        }
                        for f in all_funcs
                    ],
                }
            )
        except Exception as e:
            results.append(
                {
                    "filename": file.filename,
                    "status": "error",
                    "message": str(e),
                }
            )

    return {"status": "success", "data": results}


# ══════════════════════════════════════════════════════════════════
# PROJECT MANAGEMENT
# ══════════════════════════════════════════════════════════════════

@app.post("/api/project/upload")
async def upload_project(file: UploadFile = File(...)):
    """Upload a full project as a ZIP file."""
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are allowed for project upload.")
    
    pm = ProjectManager(PROJECT_ROOT)
    content = await file.read()
    try:
        tree = pm.ingest_zip_bytes(content, filename=file.filename)
        return {"status": "success", "data": pm.tree_to_dict(tree)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/project/github")
async def connect_github(req: GitHubConnectRequest):
    """Connect and clone a GitHub repository."""
    pm = ProjectManager(PROJECT_ROOT)
    try:
        tree = pm.ingest_github(req.url)
        return {"status": "success", "data": pm.tree_to_dict(tree)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/project/tree")
async def get_project_tree(path: str = "."):
    """Get the full project tree for a given path."""
    pm = ProjectManager(PROJECT_ROOT)
    try:
        # If it's a specific project ID from the projects dir
        projects_dir = pm.projects_dir / path
        if projects_dir.exists():
            tree = pm.build_tree(projects_dir)
        else:
            # Fall back to workspace directory
            target_path = Path(PROJECT_ROOT) / path
            if not target_path.exists():
                raise HTTPException(status_code=404, detail="Path not found")
            tree = pm.build_tree(target_path)
        
        return {"status": "success", "data": pm.tree_to_dict(tree)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/project/evolve")
async def evolve_project(req: ProjectEvolveRequest, background_tasks: BackgroundTasks):
    """Start a full project or specific file/function evolution."""
    session_id = str(uuid.uuid4())
    
    # If they passed a function_name, we use the single-function worker
    if req.function_name and req.file_path:
        background_tasks.add_task(
            run_evolution,
            session_id=session_id,
            file_path=req.file_path,
            function_name=req.function_name,
            use_llm=req.use_llm,
            apply=req.apply,
            generations=req.generations,
            project_root=PROJECT_ROOT,
        )
    else:
        # We need a new worker for multi-file/project evolution
        background_tasks.add_task(
            run_project_evolution,
            session_id=session_id,
            project_path=req.project_path or ".",
            file_path=req.file_path,
            use_llm=req.use_llm,
            apply=req.apply,
            generations=req.generations,
            project_root=PROJECT_ROOT,
        )

    return {
        "status": "success",
        "session_id": session_id,
        "message": "Project evolution started. Connect to WebSocket for live updates.",
    }

@app.post("/api/project/evolve/{session_id}/pause")
async def pause_project_evolution(session_id: str):
    if session_id in project_evolution_state:
        project_evolution_state[session_id] = "paused"
        return {"status": "success", "message": "Paused"}
    raise HTTPException(status_code=404, detail="Session not found")

@app.post("/api/project/evolve/{session_id}/resume")
async def resume_project_evolution(session_id: str):
    if session_id in project_evolution_state:
        project_evolution_state[session_id] = "running"
        return {"status": "success", "message": "Resumed"}
    raise HTTPException(status_code=404, detail="Session not found")

@app.post("/api/project/evolve/{session_id}/cancel")
async def cancel_project_evolution(session_id: str):
    if session_id in project_evolution_state:
        project_evolution_state[session_id] = "cancelled"
        return {"status": "success", "message": "Cancelled"}
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/api/files")
async def list_files():
    """List all uploaded and tracked files with function counts."""
    tracker = get_tracker()
    files_map: dict[str, dict] = {}

    # Identify and prune stale targets
    stale_targets = []

    # From DNA registry
    for target in list(tracker._registry.keys()):
        file_path = target.split(":")[0] if ":" in target else target

        # Check if the file exists on the filesystem
        full_path = Path(PROJECT_ROOT) / file_path
        upload_path = Path(PROJECT_ROOT) / ".hezgene" / "uploads" / file_path

        if not full_path.exists() and not upload_path.exists():
            stale_targets.append(target)
            continue

        if file_path not in files_map:
            files_map[file_path] = {
                "id": file_path,
                "name": Path(file_path).name,
                "path": file_path,
                "functions": 0,
                "evolved": 0,
                "frozen": 0,
                "source": "tracked",
            }
        files_map[file_path]["functions"] += 1
        dna = tracker.get_dna(target)
        if dna and dna.evolution_count > 0:
            files_map[file_path]["evolved"] += 1
        if dna and dna.frozen:
            files_map[file_path]["frozen"] += 1

    if stale_targets:
        for t in stale_targets:
            tracker._registry.pop(t, None)
        tracker._save()

    # From uploads dir
    upload_dir = Path(PROJECT_ROOT) / ".hezgene" / "uploads"
    if upload_dir.exists():
        for py_file in upload_dir.glob("*.py"):
            fname = py_file.name
            if fname not in files_map:
                try:
                    funcs = FileIngestor.extract(py_file)
                    files_map[fname] = {
                        "id": fname,
                        "name": fname,
                        "path": str(py_file),
                        "functions": len(funcs),
                        "evolved": 0,
                        "frozen": 0,
                        "source": "uploaded",
                    }
                except Exception:
                    files_map[fname] = {
                        "id": fname,
                        "name": fname,
                        "path": str(py_file),
                        "functions": 0,
                        "evolved": 0,
                        "frozen": 0,
                        "source": "uploaded",
                    }

    # From workspace
    workspace_dir = Path(PROJECT_ROOT)
    for py_file in workspace_dir.rglob("*.py"):
        parts = py_file.parts
        if any(part.startswith(".") for part in parts) or "venv" in parts or "__pycache__" in parts or "node_modules" in parts:
            continue
            
        try:
            rel_path = py_file.relative_to(PROJECT_ROOT)
        except ValueError:
            rel_path = py_file
            
        fname = str(rel_path).replace("\\", "/")
        if fname not in files_map:
            try:
                funcs = FileIngestor.extract(py_file)
                files_map[fname] = {
                    "id": fname,
                    "name": fname,
                    "path": str(py_file),
                    "functions": len(funcs),
                    "evolved": 0,
                    "frozen": 0,
                    "source": "workspace",
                }
            except Exception:
                files_map[fname] = {
                    "id": fname,
                    "name": fname,
                    "path": str(py_file),
                    "functions": 0,
                    "evolved": 0,
                    "frozen": 0,
                    "source": "workspace",
                }

    return {"status": "success", "data": list(files_map.values())}


@app.get("/api/files/{file_id:path}")
async def get_file_details(file_id: str):
    """Get file details including all functions and their evolvable status."""
    tracker = get_tracker()
    
    if file_id == "__PROJECT__":
        file_id = "."

    if file_id == ".":
        from hezgene.analysis.project_scanner import ProjectScanner
        targets = ProjectScanner(PROJECT_ROOT).scan_directory(Path(PROJECT_ROOT))
        files_to_scan = list(set(Path(PROJECT_ROOT) / t.split(":")[0] for t in targets))
        
        functions = []
        total_funcs, evolvable_count, skipped_count = 0, 0, 0
        classes = set()
        
        for file_path in files_to_scan:
            try:
                analysis = FileIngestor.analyze_file(file_path)
                total_funcs += analysis["total_functions"]
                evolvable_count += analysis["evolvable_count"]
                skipped_count += analysis["skipped_count"]
                classes.update(analysis["classes"])
                
                rel_path = str(file_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
                
                for f in analysis["evolvable"] + analysis["skipped"]:
                    entity = f"{f.class_name}.{f.name}" if f.class_name else f.name
                    target = f"{rel_path}:{entity}"
                    dna = tracker.get_dna(target)
                    
                    func_data = {
                        "name": f.name,
                        "qualified_name": f.qualified_name,
                        "lines": f.lines_of_code,
                        "evolvable": f.evolvable,
                        "skip_reason": f.skip_reason,
                        "is_method": f.is_method,
                        "class_name": f.class_name,
                        "start_line": f.start_line,
                        "end_line": f.end_line,
                        "source_code": f.source_code,
                        "file_path": rel_path,
                    }
                    if dna:
                        dna_dict = dna.to_dict()
                        dna_dict["fitness_score"] = round(dna.fitness_score, 2)
                        func_data.update(dna_dict)
                    else:
                        func_data.update({
                            "fitness_score": None,
                            "evolution_count": 0,
                            "frozen": False,
                        })
                    functions.append(func_data)
            except Exception:
                continue
                
        return {
            "status": "success",
            "data": {
                "file_id": ".",
                "total_functions": total_funcs,
                "evolvable_count": evolvable_count,
                "skipped_count": skipped_count,
                "classes": list(classes),
                "functions": functions,
            },
        }

    # Try uploads dir first
    file_path = Path(PROJECT_ROOT) / ".hezgene" / "uploads" / file_id
    if not file_path.exists():
        file_path = Path(PROJECT_ROOT) / file_id
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")

    try:
        analysis = FileIngestor.analyze_file(file_path)

        functions = []
        for f in analysis["evolvable"] + analysis["skipped"]:
            entity = f"{f.class_name}.{f.name}" if f.class_name else f.name
            target = f"{file_id}:{entity}"
            dna = tracker.get_dna(target)

            func_data = {
                "name": f.name,
                "qualified_name": f.qualified_name,
                "lines": f.lines_of_code,
                "evolvable": f.evolvable,
                "skip_reason": f.skip_reason,
                "is_method": f.is_method,
                "class_name": f.class_name,
                "start_line": f.start_line,
                "end_line": f.end_line,
                "source_code": f.source_code,
                "file_path": file_id,
            }
            if dna:
                dna_dict = dna.to_dict()
                dna_dict["fitness_score"] = round(dna.fitness_score, 2)
                func_data.update(dna_dict)
            else:
                func_data.update({
                    "fitness_score": None,
                    "evolution_count": 0,
                    "frozen": False,
                })
            functions.append(func_data)

        return {
            "status": "success",
            "data": {
                "file_id": file_id,
                "total_functions": analysis["total_functions"],
                "evolvable_count": analysis["evolvable_count"],
                "skipped_count": analysis["skipped_count"],
                "classes": analysis["classes"],
                "functions": functions,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/files/{file_id:path}")
async def delete_file(file_id: str):
    """Remove an uploaded file or untrack a project file."""
    tracker = get_tracker()

    # 1. Purge from DNA registry
    to_delete = [t for t in tracker._registry if t.startswith(f"{file_id}:") or t == file_id]
    for target in to_delete:
        tracker._registry.pop(target, None)
    if to_delete:
        tracker._save()

    # 2. If it is in uploads, delete the file
    upload_path = Path(PROJECT_ROOT) / ".hezgene" / "uploads" / file_id
    if upload_path.exists():
        upload_path.unlink()
        return {"status": "success", "message": f"Deleted and untracked {file_id}"}

    if to_delete:
        return {"status": "success", "message": f"Untracked {file_id}"}

    raise HTTPException(status_code=404, detail=f"File not found or untracked: {file_id}")


# ══════════════════════════════════════════════════════════════════
# EVOLUTION (Real-Time)
# ══════════════════════════════════════════════════════════════════


@app.post("/api/evolve")
async def start_evolution(req: EvolutionRequest, background_tasks: BackgroundTasks):
    """Start an evolution session. Returns a session_id for WebSocket connection."""
    session_id = str(uuid.uuid4())

    background_tasks.add_task(
        run_evolution,
        session_id=session_id,
        file_path=req.file_id,
        function_name=req.function_name,
        use_llm=req.use_llm,
        apply=req.apply,
        generations=req.generations,
        project_root=PROJECT_ROOT,
    )

    return {
        "status": "success",
        "session_id": session_id,
        "message": "Evolution started. Connect to WebSocket for live updates.",
    }


@app.get("/api/evolve/{session_id}")
async def get_evolution_status(session_id: str):
    """Get the current status of an evolution session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success", "data": sessions[session_id]}


@app.websocket("/ws/evolve/{session_id}")
async def evolve_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for live evolution streaming."""
    await manager.connect(session_id, websocket)
    try:
        while True:
            # Keep connection alive, listen for client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(session_id)


# ══════════════════════════════════════════════════════════════════
# DNA & ANALYSIS
# ══════════════════════════════════════════════════════════════════


@app.get("/api/functions")
async def list_functions():
    """List all tracked functions with DNA scores."""
    tracker = get_tracker()
    entries = []
    for target in tracker._registry:
        dna = tracker.get_dna(target)
        if dna:
            d = dna.to_dict()
            d["fitness_score"] = round(dna.fitness_score, 2)
            entries.append(d)
    return {"status": "success", "data": entries}


@app.get("/api/dna/{file_id}/{function_name}")
async def get_dna(file_id: str, function_name: str):
    """Get the DNA profile for a specific function."""
    tracker = get_tracker()
    target = f"{file_id}:{function_name}"
    dna = tracker.get_dna(target)
    if not dna:
        raise HTTPException(status_code=404, detail=f"DNA not found for {target}")
    data = dna.to_dict()
    data["fitness_score"] = round(dna.fitness_score, 2)
    return {"status": "success", "data": data}


@app.post("/api/scan/")
@app.post("/api/scan/{file_id:path}")
async def scan_file(file_id: str = ""):
    """Scan a file and register all evolvable functions in the DNA tracker."""
    tracker = get_tracker()
    registered = []

    if file_id == "__PROJECT__":
        file_id = "."

    if file_id == "" or file_id == ".":
        from hezgene.analysis.project_scanner import ProjectScanner
        targets = ProjectScanner(PROJECT_ROOT).scan_directory(Path(PROJECT_ROOT))
        files_to_scan = list(set(Path(PROJECT_ROOT) / t.split(":")[0] for t in targets))
        
        for file_path in files_to_scan:
            try:
                funcs = FileIngestor.extract(file_path)
                for f in funcs:
                    entity = f"{f.class_name}.{f.name}" if f.class_name else f.name
                    rel_path = str(file_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
                    target = f"{rel_path}:{entity}"
                    dna = tracker.extract(target, override_source=f.source_code)
                    registered.append(
                        {
                            "name": entity,
                            "target": target,
                            "fitness_score": round(dna.fitness_score, 2),
                            "lines": dna.lines_of_code,
                            "complexity": dna.cyclomatic_complexity,
                        }
                    )
            except Exception:
                continue

        return {
            "status": "success",
            "data": {
                "file": "Project Workspace",
                "registered": len(registered),
                "functions": registered,
            },
        }

    file_path = Path(PROJECT_ROOT) / ".hezgene" / "uploads" / file_id
    if not file_path.exists():
        file_path = Path(PROJECT_ROOT) / file_id
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")

    funcs = FileIngestor.extract(file_path)

    for f in funcs:
        entity = f"{f.class_name}.{f.name}" if f.class_name else f.name
        target = f"{file_id}:{entity}"
        dna = tracker.extract(target, override_source=f.source_code)
        registered.append(
            {
                "name": entity,
                "target": target,
                "fitness_score": round(dna.fitness_score, 2),
                "lines": dna.lines_of_code,
                "complexity": dna.cyclomatic_complexity,
            }
        )

    return {
        "status": "success",
        "data": {
            "file": file_id,
            "registered": len(registered),
            "functions": registered,
        },
    }


# ══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════


@app.get("/api/config")
async def get_config_endpoint():
    """Get current HezGene configuration."""
    try:
        cfg = get_config()
        return {"status": "success", "data": cfg.get_all()}
    except Exception:
        return {
            "status": "success",
            "data": {
                "llm": {"provider": "ollama", "model": "", "base_url": "", "api_key": ""},
                "evolution": {"generations": 5, "min_improvement": 0.001, "use_llm": False},
                "safety": {"auto_apply": False, "max_backups": 50, "verify_after_deploy": True},
            },
        }


@app.put("/api/config")
async def update_config(update: ConfigUpdate):
    """Update a configuration value."""
    cfg = get_config()
    cfg.set(update.key, update.value)
    return {"status": "success", "message": f"Set {update.key} = {update.value}"}


@app.post("/api/config/test-llm")
async def test_llm_connection(req: LLMTestRequest):
    """Test LLM connection with the given provider settings."""
    try:
        from hezgene.mutation.llm import get_provider

        kwargs = {"model": req.model}
        if req.base_url:
            kwargs["base_url"] = req.base_url
        if req.api_key:
            kwargs["api_key"] = req.api_key

        provider = get_provider(req.provider, **kwargs)
        # Try a simple completion
        result = provider.complete("def hello(): return 'world'", "Improve this function")
        return {
            "status": "success",
            "message": f"Connection to {req.provider}/{req.model} successful!",
            "response_preview": result[:200] if result else "(empty response)",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection failed: {str(e)}",
        }


# ══════════════════════════════════════════════════════════════════
# HISTORY
# ══════════════════════════════════════════════════════════════════


@app.get("/api/history")
async def get_history(
    limit: int = Query(50, ge=1, le=200),
    status: str | None = Query(None),
):
    """Get evolution history from the DNA registry."""
    tracker = get_tracker()
    log = tracker.get_evolution_log()

    if status:
        if status == "evolved":
            log = [e for e in log if e["evolutions"] > 0]
        elif status == "frozen":
            log = [e for e in log if e["frozen"]]

    return {"status": "success", "data": log[:limit]}


@app.get("/api/history/{target}")
async def get_history_detail(target: str):
    """Get detailed evolution history for a specific function."""
    tracker = get_tracker()
    # URL decode target (replace -- with :)
    decoded_target = target.replace("--", ":")
    dna = tracker.get_dna(decoded_target)
    if not dna:
        raise HTTPException(status_code=404, detail=f"No history for {decoded_target}")

    data = dna.to_dict()
    data["fitness_score"] = round(dna.fitness_score, 2)

    # Check for sandbox files
    sandbox_dir = Path(PROJECT_ROOT) / ".hezgene" / "sandbox"
    safe_name = (
        decoded_target.replace("/", "_").replace("\\", "_").replace(":", "__").replace(".", "_")
    )
    evolved_file = sandbox_dir / f"{safe_name}_evolved.py"
    original_file = sandbox_dir / f"{safe_name}_original.py"

    sandbox = {}
    if evolved_file.exists():
        sandbox["evolved"] = evolved_file.read_text(encoding="utf-8")
    if original_file.exists():
        sandbox["original"] = original_file.read_text(encoding="utf-8")

    data["sandbox"] = sandbox
    return {"status": "success", "data": data}


@app.delete("/api/history")
async def clear_history():
    """Clear all evolution history and registry tracking."""
    tracker = get_tracker()
    tracker._registry = {}
    tracker._save()
    return {"status": "success", "message": "Evolution history and registry cleared."}


@app.delete("/api/history/{target}")
async def delete_history_item(target: str):
    """Remove a single tracked target from the DNA registry."""
    tracker = get_tracker()
    decoded_target = target.replace("--", ":")
    if decoded_target in tracker._registry:
        del tracker._registry[decoded_target]
        tracker._save()
        return {"status": "success", "message": f"Removed {decoded_target} from history."}
    raise HTTPException(status_code=404, detail=f"Target {decoded_target} not found in history.")


@app.delete("/api/sandbox")
async def clear_sandbox():
    """Wipe all files from the sandbox directory."""
    sandbox_dir = Path(PROJECT_ROOT) / ".hezgene" / "sandbox"
    if sandbox_dir.exists():
        count = 0
        for file in sandbox_dir.glob("*"):
            if file.is_file():
                file.unlink()
                count += 1
        return {"status": "success", "message": f"Cleared {count} files from sandbox."}
    return {"status": "success", "message": "Sandbox directory is empty."}


@app.delete("/api/sandbox/{target}")
async def delete_sandbox_item(target: str):
    """Delete sandbox files for a specific target function."""
    decoded_target = target.replace("--", ":")
    sandbox_dir = Path(PROJECT_ROOT) / ".hezgene" / "sandbox"
    safe_name = (
        decoded_target.replace("/", "_").replace("\\", "_").replace(":", "__").replace(".", "_")
    )

    evolved_file = sandbox_dir / f"{safe_name}_evolved.py"
    original_file = sandbox_dir / f"{safe_name}_original.py"

    deleted = 0
    if evolved_file.exists():
        evolved_file.unlink()
        deleted += 1
    if original_file.exists():
        original_file.unlink()
        deleted += 1

    if deleted > 0:
        return {"status": "success", "message": f"Deleted sandbox files for {decoded_target}."}
    raise HTTPException(status_code=404, detail=f"No sandbox files found for {decoded_target}.")


@app.delete("/api/system/clean")
async def system_clean():
    """Completely wipe the DNA registry, uploads, backups, and sandbox."""
    tracker = get_tracker()
    tracker._registry = {}
    tracker._save()

    def wipe_dir(d_path: Path):
        count = 0
        if d_path.exists():
            for file in d_path.glob("*"):
                if file.is_file():
                    file.unlink()
                    count += 1
        return count

    hezgene_dir = Path(PROJECT_ROOT) / ".hezgene"
    sandbox_count = wipe_dir(hezgene_dir / "sandbox")
    uploads_count = wipe_dir(hezgene_dir / "uploads")
    backups_count = wipe_dir(hezgene_dir / "backups")

    return {
        "status": "success",
        "message": (
            f"System completely wiped. Deleted: {sandbox_count} sandbox files, "
            f"{uploads_count} uploaded files, {backups_count} backups. Registry cleared."
        ),
    }


# ══════════════════════════════════════════════════════════════════
# FREEZE / UNFREEZE
# ══════════════════════════════════════════════════════════════════


@app.post("/api/freeze/{file_id:path}/{function_name}")
async def freeze_function(file_id: str, function_name: str):
    """Freeze a function to prevent evolution."""
    tracker = get_tracker()
    target = f"{file_id}:{function_name}"
    tracker.freeze(target)
    return {"status": "success", "message": f"Frozen: {target}"}


@app.post("/api/unfreeze/{file_id:path}/{function_name}")
async def unfreeze_function(file_id: str, function_name: str):
    """Unfreeze a function to allow evolution."""
    tracker = get_tracker()
    target = f"{file_id}:{function_name}"
    tracker.unfreeze(target)
    return {"status": "success", "message": f"Unfrozen: {target}"}


@app.post("/api/deploy")
async def deploy_evolved_code(req: dict):
    """Surgically deploy evolved code for a function from the sandbox to the source file."""
    import copy

    target = req.get("target")
    if not target:
        raise HTTPException(status_code=400, detail="Missing target")

    # Check if evolved code exists in sandbox
    sandbox_dir = Path(PROJECT_ROOT) / ".hezgene" / "sandbox"
    safe_name = target.replace("/", "_").replace("\\", "_").replace(":", "__").replace(".", "_")
    evolved_file = sandbox_dir / f"{safe_name}_evolved.py"

    if not evolved_file.exists():
        raise HTTPException(
            status_code=404, detail=f"No evolved code found in sandbox for {target}"
        )

    evolved_source = evolved_file.read_text(encoding="utf-8")
    if evolved_source.startswith("# EVOLVED:"):
        lines = evolved_source.splitlines()
        evolved_source = "\n".join(lines[2:])

    tracker = get_tracker()
    dna = tracker.get_dna(target)
    if not dna:
        raise HTTPException(status_code=404, detail=f"DNA not tracked for {target}")

    winner = copy.deepcopy(dna)
    winner.source_code = evolved_source

    from hezgene.deployment.deployer import AutoDeployer

    deployer = AutoDeployer(PROJECT_ROOT)
    try:
        deployer.deploy(target, winner)
        tracker.record_evolution(target, dna, winner)
        return {"status": "success", "message": f"Successfully deployed evolved code for {target}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════
# STATS (Dashboard)
# ══════════════════════════════════════════════════════════════════


@app.get("/api/stats")
async def get_stats():
    """Get aggregate stats for the dashboard."""
    tracker = get_tracker()
    all_tracked = list(tracker._registry.keys())
    total = len(all_tracked)
    evolved = sum(1 for t in all_tracked if tracker._registry[t].evolution_count > 0)
    frozen = sum(1 for t in all_tracked if tracker._registry[t].frozen)
    total_evolutions = sum(tracker._registry[t].evolution_count for t in all_tracked)

    avg_fitness = 0.0
    if total > 0:
        avg_fitness = sum(tracker._registry[t].fitness_score for t in all_tracked) / total

    # Recent activity
    log = tracker.get_evolution_log()
    recent = log[:10]

    # Backups count
    backup_dir = Path(PROJECT_ROOT) / ".hezgene" / "backups"
    backups = len(list(backup_dir.glob("*"))) if backup_dir.exists() else 0

    return {
        "status": "success",
        "data": {
            "total_functions": total,
            "evolved_functions": evolved,
            "frozen_functions": frozen,
            "total_evolutions": total_evolutions,
            "avg_fitness": round(avg_fitness, 2),
            "backups": backups,
            "recent_activity": recent,
        },
    }


# ══════════════════════════════════════════════════════════════════
# FRONTEND SERVING
# ══════════════════════════════════════════════════════════════════

# Mount the React frontend build
frontend_dist = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve the React SPA for all non-API routes."""
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            raise HTTPException(status_code=404, detail="Not found")

        # Try to serve static files first
        static_file = frontend_dist / full_path
        if static_file.is_file():
            return FileResponse(static_file)

        # Fallback to index.html for SPA routing
        index_path = frontend_dist / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Frontend not built")


def start_server(host: str = "127.0.0.1", port: int = 8000):
    """Start the HezGene web server."""
    print("\n  🧬 HezGene Web Interface")
    print("  ────────────────────────────────")
    print(f"  🌐 App:  http://{host}:{port}")
    print(f"  📚 API:  http://{host}:{port}/docs")
    print(f"  🔌 WS:   ws://{host}:{port}/ws/evolve/{{session_id}}")
    print("  ────────────────────────────────\n")
    uvicorn.run("hezgene.web.api:app", host=host, port=port, reload=False)
