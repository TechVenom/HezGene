"""
LLM Mutator — Generates intelligent code mutations using LLM providers.

This is the Phase 2 mutation engine. It works alongside the existing
AST-based MutationEngine, adding creative, semantic-level mutations
that no rule-based system could produce.

The LLM mutator sends functions + their DNA profile to an LLM and
asks for optimized versions targeting specific improvement axes:
  - Speed optimization
  - Memory optimization
  - Code simplification
  - Algorithmic improvement
  - Robustness hardening
"""

from __future__ import annotations

import ast
import copy
import re
import textwrap

from ..core.dna_tracker import DNATracker, FunctionDNA
from hezgene.mutation.ast_mutator import Mutant
from hezgene.mutation.llm.base import LLMProvider
from hezgene.mutation.llm.prompts import (
    LLM_STRATEGIES,
    SYSTEM_PROMPT,
    build_dna_context,
)


class LLMMutator:
    """
    Generates mutant functions using an LLM provider.

    Works with any LLMProvider implementation (Ollama, OpenAI, etc.).
    Mutations go through the same Fitness Gauntlet as AST mutations.
    """

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    def spawn(self, dna: FunctionDNA, count: int = 5) -> list[Mutant]:
        """
        Generate up to `count` LLM-powered mutant versions of the function.

        Each mutant targets a different optimization strategy.
        Invalid or identical mutations are filtered out.
        """
        mutants = []
        source = dna.source_code
        if not source.strip():
            return mutants

        # Normalize original for comparison
        try:
            original_normalized = ast.unparse(ast.parse(textwrap.dedent(source)))
        except SyntaxError:
            return mutants

        dna_context = build_dna_context(dna)
        strategies = list(LLM_STRATEGIES.items())[:count]

        for i, (strategy_name, prompt_builder) in enumerate(strategies):
            try:
                prompt = prompt_builder(source, dna_context)
                response = self.provider.generate_timed(prompt, system_prompt=SYSTEM_PROMPT)

                if not response.success or not response.text.strip():
                    continue

                # Extract clean Python from the LLM response
                mutated = self._extract_function(response.text, dna.name)
                if not mutated:
                    continue

                # Validate it's actually different and valid Python
                try:
                    mutated_normalized = ast.unparse(ast.parse(textwrap.dedent(mutated)))
                except SyntaxError:
                    continue

                if mutated_normalized.strip() == original_normalized.strip():
                    continue

                # Build the mutant DNA
                mutant_dna = copy.deepcopy(dna)
                mutant_dna.source_code = mutated
                mutant_dna.source_hash = ""
                mutant_dna.lines_of_code = len(mutated.strip().splitlines())
                mutant_dna.cyclomatic_complexity = DNATracker._calc_complexity(mutated)

                mutants.append(
                    Mutant(
                        id=f"{dna.qualified_name}::llm_{i}_{strategy_name}",
                        strategy=strategy_name,
                        source_code=mutated,
                        dna=mutant_dna,
                        metadata={
                            "provider": self.provider.provider_name,
                            "model": self.provider.model,
                            "latency_ms": response.latency_ms,
                            "tokens": response.total_tokens,
                        },
                    )
                )

            except Exception:
                continue

        return mutants

    def _extract_function(self, raw_text: str, func_name: str) -> str | None:
        """
        Extract a valid Python function from LLM output.

        Handles common LLM output issues:
        - Markdown code blocks (```python ... ```)
        - Extra explanation text before/after the function
        - Multiple functions (takes the right one)
        """
        text = raw_text.strip()

        # Strip markdown code blocks
        text = re.sub(r"^```(?:python)?\s*\n?", "", text, flags=re.MULTILINE)
        text = re.sub(r"\n?```\s*$", "", text, flags=re.MULTILINE)
        text = text.strip()

        # Try parsing the whole thing
        try:
            tree = ast.parse(text)
            # Find the target function
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name == func_name:
                        return ast.get_source_segment(text, node) or text
            # If no matching name, return the whole thing if it's a single function
            funcs = [
                n
                for n in ast.iter_child_nodes(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            if len(funcs) == 1:
                return ast.get_source_segment(text, funcs[0]) or text
        except SyntaxError:
            pass

        # Extract function definition block, supporting empty lines in body
        pattern = rf"(def\s+{re.escape(func_name)}\s*\(.*?\n(?:[ \t].*\n|\s*\n)*)"
        match = re.search(pattern, text)
        if match:
            extracted = match.group(1).rstrip()
            try:
                ast.parse(extracted)
                return extracted
            except SyntaxError:
                pass

        return None
