"""
🏟️ Fitness Gauntlet — Tests mutants for correctness, speed, and memory.

Every mutant must pass through five rings:
  1. Correctness Gate — identical outputs to original
  2. Speed Ring — timed execution benchmarks
  3. Memory Ring — tracked allocation
  4. Edge Case Gauntlet — known failures and weird inputs
  5. Readability Score — structural complexity check

Phase 1: Real measurements with auto-generated test inputs.
"""

from __future__ import annotations

import ast
import copy
import math
import re
import textwrap
import time
import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from hezgene.core.dna_tracker import FunctionDNA


@dataclass
class GauntletResult:
    """Result of running a mutant through the gauntlet."""

    mutant_id: str
    passed_correctness: bool = False
    avg_speed_ms: float = float("inf")
    peak_memory_bytes: int = 0
    edge_case_failures: int = 0
    readability_score: float = 0.0
    overall_score: float = 0.0
    disqualified: bool = False
    disqualify_reason: str = ""
    dna: FunctionDNA | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mutant_id": self.mutant_id,
            "passed": self.passed_correctness and not self.disqualified,
            "speed_ms": self.avg_speed_ms,
            "memory_bytes": self.peak_memory_bytes,
            "edge_failures": self.edge_case_failures,
            "readability": self.readability_score,
            "score": self.overall_score,
        }


class FitnessGauntlet:
    """
    Evaluates mutants against the original function across
    multiple fitness dimensions.
    """

    # Number of timing iterations — enough for stable measurement
    SPEED_ITERATIONS = 200
    SPEED_WARMUP = 20
    # Number of memory samples to take
    MEMORY_SAMPLES = 5

    def __init__(
        self,
        test_inputs: list[tuple] | None = None,
        iterations: int = 200,
        module_source: str | None = None,
    ):
        self.test_inputs = test_inputs or []
        self.iterations = iterations
        self.module_source = module_source  # Full source of the original file for context injection

    def evaluate(self, original: FunctionDNA, mutants: list) -> list[GauntletResult]:
        """Run all mutants through the gauntlet."""
        # Auto-generate test inputs if none provided
        if not self.test_inputs:
            self.test_inputs = self._generate_test_inputs(original.source_code, original.name)

        results = []
        for mutant in mutants:
            result = self._evaluate_single(original, mutant)
            results.append(result)
        return results

    def _evaluate_single(self, original: FunctionDNA, mutant) -> GauntletResult:
        """Run a single mutant through all five rings."""
        if hasattr(mutant, "id"):
            mutant_id = mutant.id
            mutant_dna = mutant.dna
            mutant_source = mutant.source_code
        else:
            mutant_id = f"{mutant.name}_baseline"
            mutant_dna = mutant
            mutant_source = mutant.source_code

        result = GauntletResult(mutant_id=mutant_id, dna=mutant_dna)

        # Auto-generate test inputs if empty
        if not self.test_inputs:
            self.test_inputs = self._generate_test_inputs(original.source_code, original.name)

        try:
            orig_fn = self._compile_function(
                original.source_code, original.name, self.module_source
            )
            mut_fn = self._compile_function(mutant_source, original.name, self.module_source)
        except Exception as e:
            result.disqualified = True
            result.disqualify_reason = f"Compilation failed: {e}"
            return result

        # Ring 1: Correctness
        result.passed_correctness = self._ring_correctness(orig_fn, mut_fn)
        if not result.passed_correctness:
            result.disqualified = True
            result.disqualify_reason = "Failed correctness gate"
            return result

        # Ring 2: Speed — real benchmarks with warmup
        result.avg_speed_ms = self._ring_speed(mut_fn)

        # Ring 3: Memory — real peak allocation tracking
        result.peak_memory_bytes = self._ring_memory(mut_fn)

        # Ring 4: Edge Cases
        result.edge_case_failures = self._ring_edge_cases(orig_fn, mut_fn)

        # Ring 5: Readability
        result.readability_score = self._ring_readability(mutant_source)

        # Ring 6: Advanced Analysis (Big O, Coverage, Leaks)
        # We need this for both baseline and mutants to properly score O(n^2) penalties
        if mutant_dna:
            self._ring_advanced_analysis(mut_fn, mutant_dna, original.source_code, original.name)
            mutant_dna.avg_execution_time_ms = result.avg_speed_ms
            mutant_dna.peak_memory_bytes = result.peak_memory_bytes
            mutant_dna.readability_score = result.readability_score
            result.overall_score = mutant_dna.fitness_score
        else:
            result.overall_score = self._compute_score(result, original)

        return result

    # ── Ring Implementations ───────────────────────────────────

    def _safe_execute(self, fn: Callable, args: tuple | None = None, timeout: float = 2.0) -> Any:
        """Execute a function with a timeout using ThreadPoolExecutor."""
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            try:
                if args is not None:
                    future = executor.submit(fn, *args)
                else:
                    future = executor.submit(fn)
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                raise TimeoutError("Mutant execution timed out (possible infinite loop)")

    def _ring_correctness(self, orig_fn: Callable, mut_fn: Callable) -> bool:
        """Ring 1: Mutant must produce identical outputs or identical exceptions."""
        for args in self.test_inputs:
            orig_out = None
            mut_out = None
            orig_exc = None
            mut_exc = None

            try:
                args_orig = copy.deepcopy(args)
                orig_out = self._safe_execute(orig_fn, args_orig)
            except Exception as e:
                orig_exc = type(e)

            try:
                args_mut = copy.deepcopy(args)
                mut_out = self._safe_execute(mut_fn, args_mut)
            except Exception as e:
                mut_exc = type(e)

            if orig_exc != mut_exc:
                return False
            if orig_exc is None and orig_out != mut_out:
                return False

        # If no test inputs provided, do a basic smoke test
        if not self.test_inputs:
            try:
                self._safe_execute(orig_fn)
            except TypeError:
                pass  # Functions need args — can't test without inputs
            except Exception:
                pass

            try:
                self._safe_execute(mut_fn)
            except Exception:
                pass

        return True

    def _ring_speed(self, fn: Callable) -> float:
        """Ring 2: Benchmark execution speed with warmup and averaging.

        Uses time.perf_counter_ns() for nanosecond precision.
        Pre-generates deepcopied args outside the timing loop so
        copy overhead doesn't inflate the measurement.
        """
        test_args = self.test_inputs[0] if self.test_inputs else None

        # Warmup phase — let JIT/caches stabilize
        for _ in range(self.SPEED_WARMUP):
            try:
                args_copy = copy.deepcopy(test_args) if test_args is not None else None
                if args_copy is not None:
                    fn(*args_copy)
                else:
                    fn()
            except Exception:
                pass

        # Pre-generate all deepcopied argument sets BEFORE timing
        pre_args: list[tuple | None] = []
        for _ in range(self.iterations):
            if test_args is not None:
                pre_args.append(copy.deepcopy(test_args))
            else:
                pre_args.append(None)

        # Measurement phase — collect timing samples with ns precision
        times_ns: list[int] = []
        for i in range(self.iterations):
            a = pre_args[i]
            start = time.perf_counter_ns()
            try:
                if a is not None:
                    fn(*a)
                else:
                    fn()
            except Exception:
                pass
            elapsed = time.perf_counter_ns() - start
            times_ns.append(elapsed)

        if not times_ns:
            return 0.0001  # Never return inf

        # Trim outliers — remove top/bottom 10% for stable median
        times_ns.sort()
        trim = max(1, len(times_ns) // 10)
        trimmed = times_ns[trim:-trim] if len(times_ns) > trim * 2 else times_ns

        avg_ns = sum(trimmed) / len(trimmed)
        avg_ms = avg_ns / 1_000_000  # Convert nanoseconds → milliseconds

        # Clamp minimum to 0.0001 ms to prevent inf in fitness calculations
        return max(avg_ms, 0.0001)

    def _ring_memory(self, fn: Callable) -> int:
        """Ring 3: Track peak memory allocation with multiple samples."""
        test_args = self.test_inputs[0] if self.test_inputs else None
        peaks = []

        was_tracing = tracemalloc.is_tracing()
        if not was_tracing:
            tracemalloc.start()

        for _ in range(self.MEMORY_SAMPLES):
            args_copy = copy.deepcopy(test_args) if test_args is not None else None
            tracemalloc.reset_peak()
            try:
                if args_copy is not None:
                    fn(*args_copy)
                else:
                    fn()
            except Exception:
                pass
            _, peak = tracemalloc.get_traced_memory()
            peaks.append(peak)

        if not was_tracing:
            tracemalloc.stop()

        return min(peaks) if peaks else 0  # Use minimum to avoid noise

    def _ring_edge_cases(self, orig_fn: Callable, mut_fn: Callable) -> int:
        """Ring 4: Test with edge-case inputs."""
        edge_inputs = [(), (None,), (0,), ("",), ([],), (-1,), (0.0,), (False,)]
        failures = 0
        for args in edge_inputs:
            try:
                orig_out = self._safe_execute(orig_fn, copy.deepcopy(args), timeout=1.0)
            except Exception:
                continue  # Original also fails — not a valid test
            try:
                mut_out = self._safe_execute(mut_fn, copy.deepcopy(args), timeout=1.0)
                if mut_out != orig_out:
                    failures += 1
            except Exception:
                failures += 1
        return failures

    def _ring_advanced_analysis(
        self, fn: Callable, dna: FunctionDNA, source: str, func_name: str
    ) -> None:
        """Evaluate Coverage, Big O Time/Space Complexity, and Memory Leaks."""
        import sys

        # 1. Coverage Analysis
        lines_hit = set()

        def trace_calls(frame, event, arg):
            if event == "line":
                lines_hit.add(frame.f_lineno)
            return trace_calls

        old_trace = sys.gettrace()
        sys.settrace(trace_calls)
        for args in self.test_inputs:
            try:
                args_copy = copy.deepcopy(args)
                if args_copy is not None:
                    fn(*args_copy)
                else:
                    fn()
            except Exception:
                pass
        sys.settrace(old_trace)

        # Rough estimate based on lines hit vs total lines
        if dna.lines_of_code > 0:
            dna.test_coverage = min(1.0, len(lines_hit) / dna.lines_of_code)
        else:
            dna.test_coverage = 1.0

        # 2. Memory Leak Detection (run 1000 times)
        test_args = self.test_inputs[0] if self.test_inputs else None

        tracemalloc.start()
        for _ in range(10):  # Warmup
            try:
                fn(*(copy.deepcopy(test_args) if test_args else ()))
            except Exception:
                pass
        _, mem_before = tracemalloc.get_traced_memory()

        for _ in range(100):
            try:
                fn(*(copy.deepcopy(test_args) if test_args else ()))
            except Exception:
                pass

        _, mem_after = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # If memory grew by more than 1KB consistently over 100 iterations
        if (mem_after - mem_before) > 1024:
            dna.leak_detected = True

        # 3. Big O Complexity Analysis
        scales = [10, 100, 500, 1000]
        scaled_inputs = self._generate_scaled_inputs(source, func_name, scales)

        if not scaled_inputs:
            dna.time_complexity = "O(1)"
            dna.space_complexity = "O(1)"
            dna.scalability_score = "Constant"
            return

        times = []
        spaces = []
        for n in scales:
            args = scaled_inputs[n]
            # Time
            start = time.perf_counter_ns()
            try:
                fn(*args)
            except Exception:
                pass
            elapsed = time.perf_counter_ns() - start
            times.append(elapsed)

            # Space
            tracemalloc.start()
            try:
                fn(*args)
            except Exception:
                pass
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            spaces.append(peak)

        dna.time_complexity = self._fit_big_o(scales, times, "Time")
        dna.space_complexity = self._fit_big_o(scales, spaces, "Space")

        if "O(n²)" in dna.time_complexity or "O(2ⁿ)" in dna.time_complexity:
            dna.scalability_score = "Poor 🔴"
        elif "O(1)" in dna.time_complexity:
            dna.scalability_score = "Excellent 🟢"
        else:
            dna.scalability_score = "Linear 🟢"

    def _fit_big_o(self, ns: list[int], values: list[float], label="Metric") -> str:
        """Determine best Big O fit for N vs Values."""
        if not values or values[0] == 0:
            return "O(1)"

        # If values decrease as N increases (common with Python warmup), it's O(1)
        if values[-1] <= values[0] * 1.5:
            return "O(1)"

        # Normalize to prevent float overflow
        baseline = max(values[0], 1)
        norm_v = [max(1.0, v / baseline) for v in values]

        # Calculate variance for each model
        # The true model will have the most constant coefficient (Value / Model(N) ≈ C)
        models = {
            "O(1)": [1.0 for _ in ns],
            "O(log n)": [math.log(n) / math.log(ns[0]) if n > 1 else 1.0 for n in ns],
            "O(n)": [n / ns[0] for n in ns],
            "O(n log n)": [
                (n * math.log(n)) / (ns[0] * math.log(ns[0])) if n > 1 else 1.0 for n in ns
            ],
            "O(n²)": [(n**2) / (ns[0] ** 2) for n in ns],
        }

        best_fit = "O(n)"
        min_variance = float("inf")

        for name, expected in models.items():
            ratios = [v / e for v, e in zip(norm_v, expected)]
            mean = sum(ratios) / len(ratios)
            variance = sum((r - mean) ** 2 for r in ratios) / len(ratios)

            if variance < min_variance:
                min_variance = variance
                best_fit = name

        return best_fit

    def _ring_readability(self, source: str) -> float:
        """Ring 5: Structural readability score (0.0 - 1.0)."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return 0.0

        lines = len(source.strip().splitlines())
        nodes = sum(1 for _ in ast.walk(tree))

        # Short functions are inherently readable
        if nodes < 50:
            return 1.0

        # Heuristic: fewer nodes per line = more readable
        density = nodes / max(lines, 1)
        if density < 3:
            return 1.0
        elif density < 6:
            return 0.7
        elif density < 10:
            return 0.4
        return 0.2

    # ── Scoring ────────────────────────────────────────────────

    def _compute_score(self, result: GauntletResult, original: FunctionDNA) -> float:
        """Weighted composite fitness score."""
        # Relative speed score
        if original.avg_execution_time_ms > 0:
            ratio = original.avg_execution_time_ms / max(result.avg_speed_ms, 0.0001)
            speed_score = min(100, 50 * ratio)
        else:
            speed_score = 100 / (1.0 + (result.avg_speed_ms / 50.0))

        # Relative memory score
        if original.peak_memory_bytes > 0:
            ratio = original.peak_memory_bytes / max(result.peak_memory_bytes, 1)
            memory_score = min(100, 50 * ratio)
        else:
            memory_score = 100 / (1.0 + (result.peak_memory_bytes / (100 * 1024)))

        edge_score = max(0, 100 - result.edge_case_failures * 20)
        read_score = result.readability_score * 100

        return speed_score * 0.30 + memory_score * 0.20 + edge_score * 0.25 + read_score * 0.25

    @staticmethod
    def _compile_function(source: str, name: str, module_source: str | None = None) -> Callable:
        """Compile source code into a callable function.

        If module_source is provided, first injects all module-level context
        (imports, constants, and sibling function definitions) into the
        execution namespace so the target function can reference them.
        """
        namespace: dict[str, Any] = {}

        # Inject module context (imports, constants, other functions)
        if module_source:
            try:
                tree = ast.parse(module_source)
                # Collect every top-level node EXCEPT the target function
                context_nodes = []
                for node in tree.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node.name == name:
                            continue  # Skip — we'll use the mutant version
                    context_nodes.append(node)

                if context_nodes:
                    context_module = ast.Module(body=context_nodes, type_ignores=[])
                    ast.fix_missing_locations(context_module)
                    exec(compile(context_module, "<module_context>", "exec"), namespace)
            except Exception:
                pass  # Fall back to isolated compilation

        # Now compile and inject the target function (original or mutant)
        exec(compile(ast.parse(source), "<mutant>", "exec"), namespace)
        if name not in namespace:
            raise ValueError(f"Function '{name}' not found after compilation")
        return namespace[name]

    # ── Auto Test Input Generation (Phase 5) ───────────────────

    def _generate_test_inputs(self, source: str, func_name: str) -> list[tuple]:
        """
        Auto-generate test inputs from type hints and function body analysis.

        Strategies:
        1. Parse type hints → generate typed values
        2. Analyze function body → understand data shapes
        3. Generate edge cases → boundary values
        """
        try:
            tree = ast.parse(textwrap.dedent(source))
        except SyntaxError:
            return []

        # Find the function node
        func_node = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == func_name:
                    func_node = node
                    break

        if not func_node:
            return []

        # Extract parameters (skip 'self')
        params = []
        for arg in func_node.args.args:
            hint = ""
            if arg.annotation:
                try:
                    hint = ast.unparse(arg.annotation)
                except Exception:
                    pass
            params.append((arg.arg, hint))

        # Check for default values
        defaults = func_node.args.defaults
        num_required = len(params) - len(defaults)

        if not params:
            return [()]  # No-arg function

        # Generate inputs based on type hints
        inputs = []
        for combo in self._generate_typed_values(params, source):
            inputs.append(tuple(combo))

        # If we couldn't generate anything, try basic values
        if not inputs:
            basic = []
            for name, hint in params[:num_required]:
                basic.append(self._default_value_for_hint(hint))
            if basic:
                inputs.append(tuple(basic))

        return inputs[:10]  # Cap at 10 test cases

    def _generate_typed_values(self, params: list[tuple[str, str]], source: str) -> list[list]:
        """Generate multiple test value sets based on type hints."""
        combos = []

        # Generate one "normal" set and one "edge" set
        normal_values = []
        edge_values = []

        for param_name, hint in params:
            normal_values.append(self._normal_value_for_hint(hint, param_name, source))
            edge_values.append(self._edge_value_for_hint(hint, param_name))

        if normal_values:
            combos.append(normal_values)
        if edge_values and edge_values != normal_values:
            combos.append(edge_values)

        # Generate a large-data set for performance testing
        large_values = []
        for param_name, hint in params:
            large_values.append(self._large_value_for_hint(hint, param_name))
        if large_values:
            combos.append(large_values)

        return combos

    def _normal_value_for_hint(self, hint: str, param_name: str, source: str) -> Any:
        """Generate a typical value based on type hint."""
        h = hint.lower().replace(" ", "")

        # list[dict] — common pattern
        if "list[dict" in h or "list[dict]" in h:
            return self._infer_dict_shape(source, param_name)

        # list[float] or list[int]
        if "list[float]" in h:
            return [1.5, 2.7, 3.9, 4.1, 5.0]
        if "list[int]" in h:
            return [1, 2, 3, 4, 5]
        if "list" in h:
            return [1, 2, 3, 4, 5]

        # dict
        if "dict" in h:
            return {
                "id": 1,
                "name": "test",
                "status": "active",
                "amount": 10.0,
                "date": "2026-01-01",
            }

        # Numeric
        if "float" in h:
            return 10.5
        if "int" in h:
            return 10

        # String
        if "str" in h:
            return "test_value"

        # Bool
        if "bool" in h:
            return True

        # No hint — use param name to guess
        return self._guess_from_name(param_name)

    def _edge_value_for_hint(self, hint: str, param_name: str) -> Any:
        """Generate an edge-case value based on type hint."""
        h = hint.lower().replace(" ", "")
        if "list" in h:
            return []
        if "dict" in h:
            return {}
        if "float" in h:
            return 0.0
        if "int" in h:
            return 0
        if "str" in h:
            return ""
        if "bool" in h:
            return False
        return self._guess_from_name(param_name)

    def _large_value_for_hint(self, hint: str, param_name: str) -> Any:
        """Generate a large-data value for performance testing."""
        h = hint.lower().replace(" ", "")
        if "list[float]" in h:
            return [float(i) for i in range(100)]
        if "list[int]" in h:
            return list(range(100))
        if "list[dict" in h:
            return [
                {
                    "id": i,
                    "name": f"user_{i}",
                    "status": "active",
                    "amount": float(i * 10),
                    "date": f"2026-01-{i % 28 + 1:02d}",
                }
                for i in range(50)
            ]
        if "list" in h:
            return list(range(100))
        if "int" in h:
            return 20
        if "float" in h:
            return 999.99
        return self._guess_from_name(param_name)

    def _default_value_for_hint(self, hint: str) -> Any:
        """Fallback default value from hint."""
        h = hint.lower()
        if "list" in h:
            return [1, 2, 3]
        if "dict" in h:
            return {"key": "value"}
        if "float" in h:
            return 1.0
        if "int" in h:
            return 5
        if "str" in h:
            return "test"
        if "bool" in h:
            return True
        return 1

    def _guess_from_name(self, name: str) -> Any:
        """Guess a reasonable value from parameter name."""
        n = name.lower()
        if n == "self":

            class MockSelf:
                def __init__(self):
                    self.balance = 1000.0
                    self.transactions = []
                    self.owner = "Mock Owner"
                    self.name = "Mock Name"
                    self.id = 1
                    self.data = {}

                def deposit(self, *a, **k):
                    return True

                def withdraw(self, *a, **k):
                    return True

                def get_statement(self, *a, **k):
                    return {}

            return MockSelf()
        if n in ("n", "count", "num", "size", "length", "limit", "index", "age"):
            return 10
        if n in ("price", "cost", "amount", "total", "rate", "tax", "tax_rate", "weight"):
            return 10.5
        if n in ("name", "label", "title", "text", "message", "description"):
            return "test"
        if n in ("is_", "has_", "should_", "can_") or n.startswith("is_") or n.startswith("has_"):
            return True
        if n in ("items", "numbers", "values", "data", "elements", "prices"):
            return [1.0, 2.0, 3.0, 4.0, 5.0]
        if n in ("users", "records", "entries", "transactions"):
            return [
                {"id": 1, "name": "A", "status": "active", "amount": 10.0, "date": "2026-01-01"},
                {"id": 2, "name": "B", "status": "active", "amount": 20.0, "date": "2026-01-02"},
            ]
        if n in ("user", "record", "item", "entry"):
            return {"id": 1, "name": "test", "status": "active"}
        if "dict" in n or "map" in n:
            return {"key": "value"}
        if "list" in n or "arr" in n:
            return [1, 2, 3]

        # Generic mock fallback for complex object/interface arguments
        class MockGeneric:
            def __init__(self):
                self.balance = 1000.0
                self.transactions = []
                self.owner = "Mock Owner"
                self.name = "Mock Name"
                self.id = 1
                self.data = {}

            def __getattr__(self, name):
                def dummy_method(*args, **kwargs):
                    return True

                return dummy_method

            def __str__(self):
                return "MockGeneric"

            def __int__(self):
                return 1

            def __float__(self):
                return 1.0

        return MockGeneric()

    def _infer_dict_shape(self, source: str, param_name: str) -> list[dict]:
        """Try to infer dict key shapes from function body."""
        # Look for dict key accesses like item["key"] or item.get("key")
        keys_found = set()
        patterns = [
            rf'{param_name}\[(["\'])(\w+)\1\]',  # param["key"]
            r'(\w+)\[(["\'])(\w+)\2\]',  # var["key"]
            r'(\w+)\.get\((["\'])(\w+)\2',  # var.get("key")
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, source):
                groups = match.groups()
                key = groups[-1]
                keys_found.add(key)

        if keys_found:
            sample = {}
            for k in keys_found:
                if k in ("id", "count", "num", "age"):
                    sample[k] = 1
                elif k in ("amount", "price", "cost", "total", "weight"):
                    sample[k] = 10.0
                elif k in ("name", "title", "label", "status", "date", "type"):
                    sample[k] = "active" if k == "status" else "test"
                else:
                    sample[k] = "value"
            return [sample, {**sample, "id": 2, "name": "test2"}]

        # Fallback
        return [{"id": 1, "name": "test", "status": "active"}]

    def _generate_scaled_inputs(
        self, source: str, func_name: str, scales: list[int]
    ) -> dict[int, tuple]:
        """Generate inputs of varying sizes to measure Big O complexity."""
        try:
            tree = ast.parse(source)
            func_node = next(
                n
                for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == func_name
            )
        except Exception:
            return {}

        params = []
        for arg in func_node.args.args:
            hint = ""
            if arg.annotation:
                try:
                    hint = ast.unparse(arg.annotation)
                except Exception:
                    pass
            params.append((arg.arg, hint))

        if not params:
            return {}

        scaled_inputs = {}
        for n in scales:
            args = []
            valid_scale = False
            for name, hint in params:
                h = hint.lower().replace(" ", "")
                if "list[float]" in h:
                    args.append([float(i) for i in range(n)])
                    valid_scale = True
                elif "list[int]" in h or "list" in h:
                    args.append(list(range(n)))
                    valid_scale = True
                elif "list[dict" in h:
                    args.append(
                        [
                            {
                                "id": i,
                                "name": f"user_{i}",
                                "status": "active",
                                "amount": float(i * 10),
                                "date": f"2026-01-{i % 28 + 1:02d}",
                                "timestamp": "2026-05-20T10:00:00",
                            }
                            for i in range(n)
                        ]
                    )
                    valid_scale = True
                elif "str" in h:
                    args.append("a" * n)
                    valid_scale = True
                else:
                    args.append(self._normal_value_for_hint(hint, name, source))

            if not valid_scale:
                return {}  # If no parameters can be scaled (e.g. just ints), it's O(1) natively
            scaled_inputs[n] = tuple(args)

        return scaled_inputs
