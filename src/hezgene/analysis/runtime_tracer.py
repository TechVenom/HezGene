"""
Runtime Tracer — Profiles Python execution to track 'hot paths'.
Updates FunctionDNA with real call counts to inform evolution priority.
"""

from __future__ import annotations

import sys
import atexit
from collections import defaultdict
from pathlib import Path

from hezgene.core.dna_tracker import DNATracker

class RuntimeTracer:
    """Hooks into Python's profiler to track function call counts."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.dna_tracker = DNATracker(str(self.project_root))
        self.call_counts = defaultdict(int)
        self._is_tracing = False

    def start(self):
        """Start tracing function calls."""
        if self._is_tracing:
            return
        
        self.call_counts.clear()
        self._is_tracing = True
        sys.setprofile(self._profile_callback)
        atexit.register(self.stop_and_save)

    def _profile_callback(self, frame, event, arg):
        """Callback for sys.setprofile."""
        if event == "call":
            # Extract file path and function name
            code = frame.f_code
            filename = code.co_filename
            
            # Fast path: ignore built-ins and standard library
            if not filename.startswith(str(self.project_root)) or "venv" in filename or "site-packages" in filename:
                return

            func_name = code.co_name
            # Dunder methods and comprehensions skip
            if func_name.startswith("<") or (func_name.startswith("__") and func_name.endswith("__")):
                return

            try:
                rel_path = str(Path(filename).relative_to(self.project_root))
                # For methods we can't easily get class name from frame without inspecting self, 
                # but we can try to find it in locals if we really needed.
                # For V1, we'll just use the file:func_name format
                target_key = f"{rel_path}:{func_name}"
                self.call_counts[target_key] += 1
            except ValueError:
                pass

    def stop_and_save(self):
        """Stop tracing and persist the data to DNA Tracker."""
        if not self._is_tracing:
            return
        
        sys.setprofile(None)
        self._is_tracing = False
        atexit.unregister(self.stop_and_save)

        self._save_results()

    def _save_results(self):
        """Update FunctionDNA records with new call counts."""
        if not self.call_counts:
            return
            
        print(f"\n[HezGene Tracer] Processing execution profile for {len(self.call_counts)} functions...")
        
        updated = 0
        for target, calls in self.call_counts.items():
            dna = self.dna_tracker.get_dna(target)
            if dna:
                dna.call_count += calls
                self.dna_tracker.save_dna(dna)
                updated += 1
            else:
                # Some functions might not be tracked yet (e.g. non-evolvable or dynamically created)
                # If we want we could track them here, but typically we only evolve what's extracted by ProjectScanner
                pass
                
        print(f"[HezGene Tracer] Updated DNA for {updated} tracked functions.")
