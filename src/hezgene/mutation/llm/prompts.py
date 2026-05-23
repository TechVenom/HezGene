# ruff: noqa: E501
"""
Prompt Templates — Carefully crafted prompts for LLM-powered mutations. # ruff: noqa: E501

Each prompt is designed to produce a single, complete, valid Python function
that preserves the original's behavior while improving specific aspects.
"""

from __future__ import annotations

from typing import Any

# ── System Prompt ──────────────────────────────────────────────

SYSTEM_PROMPT = """You are HezGene, an expert Python code optimizer. Your ONLY job is to produce an improved version of a given Python function.

CRITICAL RULES:
1. You must preserve the EXACT same behavior. Same inputs must produce identical outputs. Change only the implementation, not the result.
2. Output ONLY the complete Python function — no explanation, no markdown, no comments before/after.
3. The improved function MUST have the EXACT same name and signature as the original.
4. The improved function MUST produce IDENTICAL outputs for ALL possible inputs, including edge cases and exceptions.
5. The improved function MUST be valid, runnable Python code.
6. Do NOT add imports — only use what the original uses.
7. Do NOT change the function name or parameters. Preserve the original function's docstring and type hints.
8. Do NOT wrap in markdown code blocks — output raw Python only.
9. If you cannot improve the function without breaking correctness, output it exactly as-is.
10. VERIFY your own output before returning: mentally run example inputs and ensure the expected outputs match the original EXACTLY."""


# ── Mutation Strategy Prompts ──────────────────────────────────


def build_optimize_speed_prompt(source: str, dna_context: str) -> str:
    """Prompt: Make the function faster."""
    return f"""Optimize this Python function for SPEED. Make it execute faster while keeping identical behavior.

Techniques to consider:
- Replace loops with list comprehensions or generator expressions
- Use built-in functions (sum, min, max, map, filter) instead of manual loops
- Add early returns for common cases
- Reduce unnecessary allocations
- Use local variable lookups instead of repeated attribute access

FUNCTION DNA (context):
{dna_context}

ORIGINAL FUNCTION:
{source}

Output ONLY the improved function. No explanation."""


def build_optimize_memory_prompt(source: str, dna_context: str) -> str:
    """Prompt: Reduce memory usage."""
    return f"""Optimize this Python function for MEMORY EFFICIENCY. Reduce allocations while keeping identical behavior.

Techniques to consider:
- Use generators instead of lists where possible
- Avoid creating intermediate data structures
- Use in-place operations
- Remove unused variables
- Use itertools for memory-efficient iteration

FUNCTION DNA (context):
{dna_context}

ORIGINAL FUNCTION:
{source}

Output ONLY the improved function. No explanation."""


def build_simplify_prompt(source: str, dna_context: str) -> str:
    """Prompt: Simplify and clean up the code."""
    return f"""Simplify this Python function. Make it shorter and more readable while keeping identical behavior.

Techniques to consider:
- Flatten nested conditionals with guard clauses
- Use ternary expressions for simple if/else
- Remove dead code and unnecessary variables
- Combine related operations
- Use Pythonic idioms (enumerate, zip, unpacking)

FUNCTION DNA (context):
{dna_context}

ORIGINAL FUNCTION:
{source}

Output ONLY the improved function. No explanation."""


def build_algorithmic_prompt(source: str, dna_context: str) -> str:
    """Prompt: Improve the algorithm itself."""
    return f"""Improve the ALGORITHM of this Python function. Find a better algorithmic approach while keeping identical behavior.

Techniques to consider:
- Reduce time complexity (O(n²) → O(n log n) or O(n))
- Use appropriate data structures (set for lookups, dict for mapping)
- Add memoization for recursive functions
- Use divide-and-conquer or dynamic programming
- Eliminate redundant computations

FUNCTION DNA (context):
{dna_context}

ORIGINAL FUNCTION:
{source}

Output ONLY the improved function. No explanation."""


def build_robust_prompt(source: str, dna_context: str) -> str:
    """Prompt: Make the function more robust."""
    return f"""Make this Python function MORE ROBUST. Add defensive coding while keeping identical behavior for valid inputs.

Techniques to consider:
- Add early returns for edge cases (empty input, None, zero)
- Add type checking for critical parameters
- Use .get() for dict access instead of direct key access
- Handle potential exceptions gracefully
- Add bounds checking for sequences

FUNCTION DNA (context):
{dna_context}

ORIGINAL FUNCTION:
{source}

Output ONLY the improved function. No explanation."""


# ── DNA Context Builder ───────────────────────────────────────


def build_dna_context(dna: Any) -> str:
    """Build a human-readable DNA summary for prompt context."""
    lines = []
    if hasattr(dna, "lines_of_code"):
        lines.append(f"- Lines of code: {dna.lines_of_code}")
    if hasattr(dna, "cyclomatic_complexity"):
        lines.append(f"- Cyclomatic complexity: {dna.cyclomatic_complexity}")
    if hasattr(dna, "avg_execution_time_ms") and dna.avg_execution_time_ms > 0:
        lines.append(f"- Avg execution time: {dna.avg_execution_time_ms:.3f} ms")
    if hasattr(dna, "peak_memory_bytes") and dna.peak_memory_bytes > 0:
        lines.append(f"- Peak memory: {dna.peak_memory_bytes:,} bytes")
    if hasattr(dna, "bug_count") and dna.bug_count > 0:
        lines.append(f"- Known bugs: {dna.bug_count}")
    if hasattr(dna, "readability_score"):
        lines.append(f"- Readability score: {dna.readability_score:.2f}")
    return "\n".join(lines) if lines else "No DNA data available."


# ── Strategy Registry ─────────────────────────────────────────

LLM_STRATEGIES = {
    "llm_speed": build_optimize_speed_prompt,
    "llm_memory": build_optimize_memory_prompt,
    "llm_simplify": build_simplify_prompt,
    "llm_algorithm": build_algorithmic_prompt,
    "llm_robust": build_robust_prompt,
}
