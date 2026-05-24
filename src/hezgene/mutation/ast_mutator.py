"""
Mutation Engine — Spawns mutant versions of functions.

Strategies (Phase 1 — AST-based):
  - loop_to_comprehension: Replace for+append with list comprehension
  - combine_operations: Merge multi-step operations into single expressions
  - guard_clause: Convert nested if/else to early returns
  - dead_code_remove: Strip unreachable code after returns
  - constant_fold: Pre-compute constant expressions
  - early_return: Add early return for empty/None inputs
"""

from __future__ import annotations

import ast
import copy
import textwrap
from dataclasses import dataclass, field
from typing import Any

from ..core.dna_tracker import FunctionDNA


@dataclass
class Mutant:
    """A candidate mutation of a function."""

    id: str
    strategy: str
    source_code: str
    dna: FunctionDNA
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "strategy": self.strategy,
            "source_code": self.source_code,
            "dna": self.dna.to_dict(),
            "metadata": self.metadata,
        }


class MutationEngine:
    """Spawns mutant versions of a function using AST transformations."""

    STRATEGIES = [
        "loop_to_comprehension",
        "combine_operations",
        "guard_clause",
        "dead_code_remove",
        "constant_fold",
        "early_return",
        "augmented_assign",
    ]

    def spawn(self, dna: FunctionDNA, count: int = 5) -> list[Mutant]:
        """Generate up to `count` mutant versions of the function."""
        mutants = []
        source = dna.source_code
        if not source.strip():
            return mutants

        # Normalize original through ast.unparse for fair comparison
        try:
            original_normalized = ast.unparse(ast.parse(textwrap.dedent(source)))
        except SyntaxError:
            return mutants

        for i, strategy in enumerate(self.STRATEGIES):
            try:
                mutated = self._apply_strategy(strategy, source)
                if mutated and mutated.strip() != original_normalized.strip():
                    mutant_dna = copy.deepcopy(dna)
                    mutant_dna.source_code = mutated
                    mutant_dna.source_hash = ""
                    from ..core.dna_tracker import DNATracker

                    mutant_dna.lines_of_code = len(mutated.strip().splitlines())
                    mutant_dna.cyclomatic_complexity = DNATracker._calc_complexity(mutated)
                    mutants.append(
                        Mutant(
                            id=f"{dna.qualified_name}::mutant_{i}_{strategy}",
                            strategy=strategy,
                            source_code=mutated,
                            dna=mutant_dna,
                        )
                    )
                    if len(mutants) >= count:
                        break
            except Exception:
                continue
        return mutants

    def _apply_strategy(self, strategy: str, source: str) -> str | None:
        handler = getattr(self, f"_mutate_{strategy}", None)
        if handler is None:
            return None
        try:
            tree = ast.parse(textwrap.dedent(source))
            mutated_tree = handler(tree)
            if mutated_tree:
                ast.fix_missing_locations(mutated_tree)
                return ast.unparse(mutated_tree)
        except (SyntaxError, TypeError, ValueError):
            pass
        return None

    # ── Strategies ─────────────────────────────────────────────

    def _mutate_loop_to_comprehension(self, tree: ast.Module) -> ast.Module | None:
        """Convert for-loop with .append() to list comprehension."""

        class Transformer(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                self.generic_visit(node)
                new_body = []
                i = 0
                while i < len(node.body):
                    # Look for pattern: result = []; for x in iter: result.append(expr)
                    if (
                        i + 1 < len(node.body)
                        and isinstance(node.body[i], ast.Assign)
                        and isinstance(node.body[i].value, ast.List)
                        and len(node.body[i].value.elts) == 0
                        and isinstance(node.body[i + 1], ast.For)
                    ):

                        assign = node.body[i]
                        for_node = node.body[i + 1]
                        target_name = None

                        if isinstance(assign.targets[0], ast.Name):
                            target_name = assign.targets[0].id

                        # Check if for body is a single append or if/append
                        append_info = self._extract_append(for_node, target_name)
                        if append_info:
                            elt, ifs = append_info
                            comp = ast.ListComp(
                                elt=elt,
                                generators=[
                                    ast.comprehension(
                                        target=for_node.target,
                                        iter=for_node.iter,
                                        ifs=ifs,
                                        is_async=0,
                                    )
                                ],
                            )
                            new_assign = ast.Assign(
                                targets=assign.targets,
                                value=comp,
                                lineno=assign.lineno,
                            )
                            new_body.append(new_assign)
                            i += 2
                            continue

                    new_body.append(node.body[i])
                    i += 1
                node.body = new_body
                return node

            def _extract_append(self, for_node, target_name):
                """Extract append pattern from for loop body."""
                body = for_node.body
                if len(body) == 1:
                    stmt = body[0]
                    # Direct: target.append(expr)
                    if (
                        isinstance(stmt, ast.Expr)
                        and isinstance(stmt.value, ast.Call)
                        and isinstance(stmt.value.func, ast.Attribute)
                        and stmt.value.func.attr == "append"
                        and isinstance(stmt.value.func.value, ast.Name)
                        and stmt.value.func.value.id == target_name
                        and len(stmt.value.args) == 1
                    ):
                        return stmt.value.args[0], []

                    # Conditional: if cond: target.append(expr)
                    if isinstance(stmt, ast.If) and len(stmt.body) == 1 and not stmt.orelse:
                        inner = stmt.body[0]
                        if (
                            isinstance(inner, ast.Expr)
                            and isinstance(inner.value, ast.Call)
                            and isinstance(inner.value.func, ast.Attribute)
                            and inner.value.func.attr == "append"
                            and isinstance(inner.value.func.value, ast.Name)
                            and inner.value.func.value.id == target_name
                            and len(inner.value.args) == 1
                        ):
                            return inner.value.args[0], [stmt.test]

                return None

        return Transformer().visit(copy.deepcopy(tree))

    def _mutate_combine_operations(self, tree: ast.Module) -> ast.Module | None:
        """Combine multi-line variable assignments into single expressions."""

        class Combiner(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                self.generic_visit(node)
                new_body = []
                i = 0
                while i < len(node.body):
                    # Pattern: x = expr; x = x + something → x = expr + something
                    # Support both ast.Name and ast.Attribute (like self.x)
                    if (
                        i + 1 < len(node.body)
                        and isinstance(node.body[i], ast.Assign)
                        and isinstance(node.body[i + 1], ast.Assign)
                        and len(node.body[i].targets) == 1
                        and len(node.body[i + 1].targets) == 1
                    ):

                        target1 = node.body[i].targets[0]
                        target2 = node.body[i + 1].targets[0]

                        def get_target_id(t):
                            if isinstance(t, ast.Name):
                                return t.id
                            elif isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name):
                                return f"{t.value.id}.{t.attr}"
                            return None

                        id1 = get_target_id(target1)
                        id2 = get_target_id(target2)

                        if id1 and id1 == id2:
                            val2 = node.body[i + 1].value

                            def is_matching_left(left, id_str):
                                if isinstance(left, ast.Name) and left.id == id_str:
                                    return True
                                if isinstance(left, ast.Attribute) and isinstance(
                                    left.value, ast.Name
                                ):
                                    return f"{left.value.id}.{left.attr}" == id_str
                                return False

                            if isinstance(val2, ast.BinOp) and is_matching_left(val2.left, id1):
                                combined = ast.Assign(
                                    targets=node.body[i].targets,
                                    value=ast.BinOp(
                                        left=node.body[i].value,
                                        op=val2.op,
                                        right=val2.right,
                                    ),
                                    lineno=node.body[i].lineno,
                                )
                                new_body.append(combined)
                                i += 2
                                continue
                    new_body.append(node.body[i])
                    i += 1
                node.body = new_body
                return node

        return Combiner().visit(copy.deepcopy(tree))

    def _mutate_guard_clause(self, tree: ast.Module) -> ast.Module | None:
        """Convert if/else with single-branch returns to guard clauses."""

        class GuardTransformer(ast.NodeTransformer):
            def visit_If(self, node):
                self.generic_visit(node)
                # Case 1: Body is a single return, orelse has stuff
                if node.orelse and len(node.body) == 1 and isinstance(node.body[0], ast.Return):
                    guard = ast.If(test=node.test, body=node.body, orelse=[])
                    return [guard] + node.orelse
                # Case 2: Orelse is a single return, body has stuff -> Invert test!
                elif (
                    node.orelse and len(node.orelse) == 1 and isinstance(node.orelse[0], ast.Return)
                ):
                    inverted_test = ast.UnaryOp(op=ast.Not(), operand=node.test)
                    if isinstance(node.test, ast.Compare) and len(node.test.ops) == 1:
                        # Try to cleanly invert the comparison instead of wrapping in Not()
                        op_map = {
                            ast.Eq: ast.NotEq,
                            ast.NotEq: ast.Eq,
                            ast.Lt: ast.GtE,
                            ast.LtE: ast.Gt,
                            ast.Gt: ast.LtE,
                            ast.GtE: ast.Lt,
                        }
                        if type(node.test.ops[0]) in op_map:
                            inverted_test = ast.Compare(
                                left=node.test.left,
                                ops=[op_map[type(node.test.ops[0])]()],
                                comparators=node.test.comparators,
                            )
                    guard = ast.If(test=inverted_test, body=node.orelse, orelse=[])
                    return [guard] + node.body
                return node

        return GuardTransformer().visit(copy.deepcopy(tree))

    def _mutate_dead_code_remove(self, tree: ast.Module) -> ast.Module | None:
        """Remove statements after unconditional return/raise."""

        class Remover(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                self.generic_visit(node)
                node.body = self._trim(node.body)
                return node

            def _trim(self, body):
                trimmed = []
                for stmt in body:
                    trimmed.append(stmt)
                    if isinstance(stmt, (ast.Return, ast.Raise)):
                        break
                return trimmed

        return Remover().visit(copy.deepcopy(tree))

    def _mutate_constant_fold(self, tree: ast.Module) -> ast.Module | None:
        """Pre-compute constant binary operations."""
        ops = {
            ast.Add: lambda a, b: a + b,
            ast.Sub: lambda a, b: a - b,
            ast.Mult: lambda a, b: a * b,
            ast.FloorDiv: lambda a, b: a // b if b != 0 else None,
            ast.Mod: lambda a, b: a % b if b != 0 else None,
        }

        class Folder(ast.NodeTransformer):
            def visit_BinOp(self, node):
                self.generic_visit(node)
                if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
                    op_type = type(node.op)
                    if op_type in ops:
                        result = ops[op_type](node.left.value, node.right.value)
                        if result is not None:
                            return ast.Constant(value=result)
                return node

        return Folder().visit(copy.deepcopy(tree))

    def _mutate_early_return(self, tree: ast.Module) -> ast.Module | None:
        """Add early return for empty/None input parameters."""

        class EarlyReturn(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                self.generic_visit(node)
                # Only add if function has parameters and no existing early return
                if not node.args.args:
                    return node
                first = node.body[0] if node.body else None
                # Skip if docstring
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                    first = node.body[1] if len(node.body) > 1 else None
                # Skip if already has an early return guard
                if (
                    isinstance(first, ast.If)
                    and len(first.body) == 1
                    and isinstance(first.body[0], ast.Return)
                ):
                    return node
                # Add: if not <first_param>: return <default>
                first_param = node.args.args[0]
                if first_param.arg == "self":
                    if len(node.args.args) > 1:
                        first_param = node.args.args[1]
                    else:
                        return node
                # Determine return default based on return annotation
                default = ast.Constant(value=None)
                if node.returns:
                    ret_str = ast.unparse(node.returns) if hasattr(ast, "unparse") else ""
                    if "list" in ret_str.lower() or "List" in ret_str:
                        default = ast.List(elts=[], ctx=ast.Load())
                    elif "dict" in ret_str.lower() or "Dict" in ret_str:
                        default = ast.Dict(keys=[], values=[])
                    elif "bool" in ret_str.lower():
                        default = ast.Constant(value=False)
                    elif "float" in ret_str.lower():
                        default = ast.Constant(value=0.0)
                    elif "int" in ret_str.lower():
                        default = ast.Constant(value=0)

                guard = ast.If(
                    test=ast.UnaryOp(
                        op=ast.Not(), operand=ast.Name(id=first_param.arg, ctx=ast.Load())
                    ),
                    body=[ast.Return(value=default)],
                    orelse=[],
                )
                # Insert after docstring if present
                insert_idx = 0
                if (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                ):
                    insert_idx = 1
                node.body.insert(insert_idx, guard)
                return node

        return EarlyReturn().visit(copy.deepcopy(tree))

    def _mutate_augmented_assign(self, tree: ast.Module) -> ast.Module | None:
        """Convert assignment with binary operation to augmented assignment
        (e.g., x = x + y -> x += y)."""

        class AugmentTransformer(ast.NodeTransformer):
            def visit_Assign(self, node):
                self.generic_visit(node)
                if len(node.targets) != 1:
                    return node
                target = node.targets[0]
                value = node.value

                if not isinstance(value, ast.BinOp):
                    return node

                match = False
                if (
                    isinstance(target, ast.Name)
                    and isinstance(value.left, ast.Name)
                    and target.id == value.left.id
                ):
                    match = True
                elif isinstance(target, ast.Attribute) and isinstance(value.left, ast.Attribute):
                    if (
                        target.attr == value.left.attr
                        and isinstance(target.value, ast.Name)
                        and isinstance(value.left.value, ast.Name)
                        and target.value.id == value.left.value.id
                    ):
                        match = True

                if match:
                    return ast.AugAssign(
                        target=target,
                        op=value.op,
                        value=value.right,
                        lineno=node.lineno,
                    )
                return node

        return AugmentTransformer().visit(copy.deepcopy(tree))
