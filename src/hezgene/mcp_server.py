"""
MCP Server — Model Context Protocol implementation for HezGene.

Exposes HezGene's intelligence to AI agents (like Claude, Cursor, or Windsurf)
via the standard JSON-RPC over stdio protocol.
"""

from __future__ import annotations

import json
import sys
import traceback
from typing import Any

from hezgene.analysis.health_score import HealthScanner
from hezgene.analysis.dead_code import DeadCodeScanner
from hezgene.analysis.duplication import DuplicationScanner
from hezgene.analysis.dependency_hygiene import DependencyScanner
from hezgene.guard import HealthGuard


class MCPServer:
    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.tools = [
            {
                "name": "hezgene_get_health",
                "description": "Get the overall project health score, dead code count, duplicate families, and top refactoring targets.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "hezgene_get_dead_code",
                "description": "Scan the project for dead/unreachable code and return a list of unused functions and classes.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "hezgene_get_dependencies",
                "description": "Scan the project for dependency hygiene issues (unused or missing dependencies).",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "hezgene_guard_snapshot",
                "description": "Save the current health score as a baseline. Call this BEFORE making code changes so the guard can detect regressions.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "hezgene_guard_check",
                "description": "Compare the current health score against the stored baseline. Returns pass/fail status with delta. Call this AFTER making code changes to verify no regression.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "threshold": {
                            "type": "integer",
                            "description": "Maximum allowed score drop (default: 10)",
                            "default": 10
                        },
                        "auto_revert": {
                            "type": "boolean",
                            "description": "If true, auto-revert HEAD commit on failure",
                            "default": false
                        }
                    },
                    "required": []
                }
            }
        ]

    def serve(self):
        """Run the JSON-RPC server loop over stdin/stdout."""
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
                self._handle_request(request)
            except Exception as e:
                # Log errors to stderr so we don't break JSON-RPC stdout stream
                sys.stderr.write(f"Error handling request: {e}\n{traceback.format_exc()}\n")
                sys.stderr.flush()

    def _send_response(self, response: dict[str, Any]):
        response["jsonrpc"] = "2.0"
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()

    def _handle_request(self, req: dict[str, Any]):
        req_id = req.get("id")
        method = req.get("method")
        
        if method == "initialize":
            self._send_response({
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "hezgene-mcp",
                        "version": "1.0.0"
                    }
                }
            })
        elif method == "notifications/initialized":
            pass # Client is ready
        elif method == "tools/list":
            self._send_response({
                "id": req_id,
                "result": {
                    "tools": self.tools
                }
            })
        elif method == "tools/call":
            params = req.get("params", {})
            name = params.get("name")
            
            try:
                if name == "hezgene_get_health":
                    scanner = HealthScanner(self.project_root)
                    report = scanner.scan()
                    import dataclasses
                    content = json.dumps(dataclasses.asdict(report), indent=2)
                    self._send_response({
                        "id": req_id,
                        "result": {"content": [{"type": "text", "text": content}], "isError": False}
                    })
                elif name == "hezgene_get_dead_code":
                    scanner = DeadCodeScanner(self.project_root)
                    findings = scanner.scan()
                    content = json.dumps([{"file": f.file_path, "line": f.line_number, "entity": f.entity_name} for f in findings], indent=2)
                    self._send_response({
                        "id": req_id,
                        "result": {"content": [{"type": "text", "text": content}], "isError": False}
                    })
                elif name == "hezgene_get_dependencies":
                    scanner = DependencyScanner(self.project_root)
                    issues = scanner.scan()
                    content = json.dumps([{"package": i.package_name, "issue": i.issue_type, "reason": i.reason} for i in issues], indent=2)
                    self._send_response({
                        "id": req_id,
                        "result": {"content": [{"type": "text", "text": content}], "isError": False}
                    })
                elif name == "hezgene_guard_snapshot":
                    guard = HealthGuard(self.project_root)
                    baseline = guard.snapshot()
                    content = json.dumps({"status": "success", "baseline": baseline}, indent=2)
                    self._send_response({
                        "id": req_id,
                        "result": {"content": [{"type": "text", "text": content}], "isError": False}
                    })
                elif name == "hezgene_guard_check":
                    from dataclasses import asdict
                    args = params.get("arguments", {})
                    threshold = args.get("threshold", 10)
                    auto_revert = args.get("auto_revert", False)
                    guard = HealthGuard(self.project_root)
                    result = guard.check(threshold=threshold, auto_revert=auto_revert)
                    content = json.dumps(asdict(result), indent=2)
                    is_error = result.status == "fail"
                    self._send_response({
                        "id": req_id,
                        "result": {"content": [{"type": "text", "text": content}], "isError": is_error}
                    })
                else:
                    self._send_response({
                        "id": req_id,
                        "result": {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True}
                    })
            except Exception as e:
                self._send_response({
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}
                })
        else:
            if req_id is not None:
                self._send_response({
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": "Method not found"
                    }
                })
