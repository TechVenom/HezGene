"""
Health Guard — Auto-revert safety net for AI-driven code evolution.

Monitors the project health score across code changes. If the score drops
by more than a configurable threshold after a commit/push, the guard can:
  1. Fire a webhook (Slack, Discord, CI, or custom)
  2. Auto-revert the offending commit via `git revert HEAD`
  3. Return structured JSON for agent consumption

Usage (CLI):
  hezgene guard snapshot          # Save current score as baseline
  hezgene guard check             # Compare current vs baseline
  hezgene guard check --auto-revert --threshold 10
  hezgene guard install           # Install as git pre-push hook

Usage (MCP / Agent):
  Call hezgene_guard_snapshot, then hezgene_guard_check after edits.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from hezgene.analysis.health_score import HealthScanner


BASELINE_FILE = ".hezgene/guard_baseline.json"


@dataclass
class GuardResult:
    """Result of a guard check comparing current health to baseline."""
    status: str            # "pass", "fail", "no_baseline"
    baseline_score: int
    current_score: int
    delta: int             # current - baseline (negative = regression)
    threshold: int
    baseline_grade: str
    current_grade: str
    auto_reverted: bool
    webhook_fired: bool
    message: str


class HealthGuard:
    """Watches the project health score and reacts to regressions."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.baseline_path = self.project_root / BASELINE_FILE
        self.scanner = HealthScanner(project_root)

    # ── Snapshot ─────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        """
        Capture the current health score and persist it as the baseline.

        Returns a dict with the baseline data for JSON output.
        """
        report = self.scanner.scan()
        baseline = {
            "score": report.score,
            "grade": report.grade,
            "total_functions": report.total_functions,
            "dead_code_count": report.dead_code_count,
            "duplicate_groups": report.duplicate_groups,
            "avg_complexity": report.avg_complexity,
            "avg_maintainability": report.avg_maintainability,
            "timestamp": time.time(),
        }

        self.baseline_path.parent.mkdir(parents=True, exist_ok=True)
        self.baseline_path.write_text(json.dumps(baseline, indent=2), encoding="utf-8")

        return baseline

    def _load_baseline(self) -> Optional[dict]:
        """Load the stored baseline, or None if it doesn't exist."""
        if not self.baseline_path.exists():
            return None
        try:
            return json.loads(self.baseline_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    # ── Check ────────────────────────────────────────────────────────

    def check(
        self,
        threshold: int = 10,
        auto_revert: bool = False,
        webhook_url: Optional[str] = None,
    ) -> GuardResult:
        """
        Compare the current health score against the stored baseline.

        Args:
            threshold: Maximum allowed score drop before triggering a failure.
            auto_revert: If True, run `git revert HEAD --no-edit` on failure.
            webhook_url: If set, POST a JSON payload to this URL on failure.

        Returns:
            A GuardResult dataclass with full details.
        """
        baseline = self._load_baseline()
        if baseline is None:
            return GuardResult(
                status="no_baseline",
                baseline_score=0,
                current_score=0,
                delta=0,
                threshold=threshold,
                baseline_grade="?",
                current_grade="?",
                auto_reverted=False,
                webhook_fired=False,
                message="No baseline found. Run `hezgene guard snapshot` first.",
            )

        report = self.scanner.scan()
        delta = report.score - baseline["score"]
        regression = delta <= -threshold

        auto_reverted = False
        webhook_fired = False

        if regression:
            status = "fail"
            message = (
                f"Health score dropped by {abs(delta)} points "
                f"({baseline['score']} → {report.score}), "
                f"exceeding threshold of {threshold}."
            )

            # Auto-revert
            if auto_revert:
                try:
                    self._git_revert()
                    auto_reverted = True
                    message += " Auto-reverted HEAD commit."
                except Exception as e:
                    message += f" Auto-revert failed: {e}"

            # Webhook
            if webhook_url:
                try:
                    self._fire_webhook(webhook_url, {
                        "event": "health_regression",
                        "baseline_score": baseline["score"],
                        "current_score": report.score,
                        "delta": delta,
                        "threshold": threshold,
                        "auto_reverted": auto_reverted,
                        "project": str(self.project_root.resolve()),
                        "timestamp": time.time(),
                    })
                    webhook_fired = True
                except Exception:
                    pass  # Don't fail the guard because the webhook failed
        else:
            status = "pass"
            if delta >= 0:
                message = f"Health score stable or improved ({baseline['score']} → {report.score}, +{delta})."
            else:
                message = (
                    f"Health score dipped by {abs(delta)} points "
                    f"({baseline['score']} → {report.score}), "
                    f"within threshold of {threshold}."
                )

        return GuardResult(
            status=status,
            baseline_score=baseline["score"],
            current_score=report.score,
            delta=delta,
            threshold=threshold,
            baseline_grade=baseline.get("grade", "?"),
            current_grade=report.grade,
            auto_reverted=auto_reverted,
            webhook_fired=webhook_fired,
            message=message,
        )

    # ── Git Hook Install ─────────────────────────────────────────────

    def install_hook(self, hook_type: str = "pre-push") -> str:
        """
        Install a git hook that runs `hezgene guard check` before push.

        Returns the path to the created hook file.
        """
        git_dir = self.project_root / ".git"
        if not git_dir.is_dir():
            raise FileNotFoundError("Not a git repository (no .git directory).")

        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        hook_path = hooks_dir / hook_type

        hook_script = f"""#!/bin/sh
# HezGene Health Guard — auto-installed by `hezgene guard install`
# Checks health score regression before pushing.

echo "🧬 HezGene Guard: Checking health score..."
result=$(hezgene guard check --output json --threshold 10 2>/dev/null)
status=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null)

if [ "$status" = "fail" ]; then
    echo "❌ HezGene Guard BLOCKED push: Health score regression detected!"
    echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'   Score: {{d[\"baseline_score\"]}} → {{d[\"current_score\"]}} ({{d[\"delta\"]:+d}})')"
    echo "   Run 'hezgene guard check' for details, or 'git push --no-verify' to force."
    exit 1
fi

echo "✅ HezGene Guard: Health check passed."
exit 0
"""
        hook_path.write_text(hook_script, encoding="utf-8")

        # Make executable (Unix)
        try:
            hook_path.chmod(0o755)
        except Exception:
            pass  # Windows doesn't need chmod

        return str(hook_path)

    # ── Internal Helpers ─────────────────────────────────────────────

    @staticmethod
    def _git_revert():
        """Revert the last commit using git."""
        subprocess.check_call(
            ["git", "revert", "HEAD", "--no-edit"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

    @staticmethod
    def _fire_webhook(url: str, payload: dict):
        """POST a JSON payload to a webhook URL using urllib (no dependencies)."""
        import urllib.request

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)

    def to_dict(self, result: GuardResult) -> dict:
        """Convert a GuardResult to a plain dict for JSON serialization."""
        return asdict(result)
