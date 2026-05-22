import ast
import math


class HalsteadVisitor(ast.NodeVisitor):
    def __init__(self):
        self.operators = set()
        self.operands = set()
        self.N1 = 0  # Total operators
        self.N2 = 0  # Total operands

    def _record_operator(self, op_type):
        self.operators.add(op_type)
        self.N1 += 1

    def _record_operand(self, val):
        self.operands.add(val)
        self.N2 += 1

    # Logic & Math Operators
    def visit_Add(self, node):
        self._record_operator("Add")
        self.generic_visit(node)

    def visit_Sub(self, node):
        self._record_operator("Sub")
        self.generic_visit(node)

    def visit_Mult(self, node):
        self._record_operator("Mult")
        self.generic_visit(node)

    def visit_Div(self, node):
        self._record_operator("Div")
        self.generic_visit(node)

    def visit_FloorDiv(self, node):
        self._record_operator("FloorDiv")
        self.generic_visit(node)

    def visit_Mod(self, node):
        self._record_operator("Mod")
        self.generic_visit(node)

    def visit_Pow(self, node):
        self._record_operator("Pow")
        self.generic_visit(node)

    def visit_Eq(self, node):
        self._record_operator("Eq")
        self.generic_visit(node)

    def visit_NotEq(self, node):
        self._record_operator("NotEq")
        self.generic_visit(node)

    def visit_Lt(self, node):
        self._record_operator("Lt")
        self.generic_visit(node)

    def visit_LtE(self, node):
        self._record_operator("LtE")
        self.generic_visit(node)

    def visit_Gt(self, node):
        self._record_operator("Gt")
        self.generic_visit(node)

    def visit_GtE(self, node):
        self._record_operator("GtE")
        self.generic_visit(node)

    def visit_Is(self, node):
        self._record_operator("Is")
        self.generic_visit(node)

    def visit_IsNot(self, node):
        self._record_operator("IsNot")
        self.generic_visit(node)

    def visit_In(self, node):
        self._record_operator("In")
        self.generic_visit(node)

    def visit_NotIn(self, node):
        self._record_operator("NotIn")
        self.generic_visit(node)

    def visit_And(self, node):
        self._record_operator("And")
        self.generic_visit(node)

    def visit_Or(self, node):
        self._record_operator("Or")
        self.generic_visit(node)

    # Keywords/Structure Operators
    def visit_If(self, node):
        self._record_operator("If")
        self.generic_visit(node)

    def visit_For(self, node):
        self._record_operator("For")
        self.generic_visit(node)

    def visit_While(self, node):
        self._record_operator("While")
        self.generic_visit(node)

    def visit_Return(self, node):
        self._record_operator("Return")
        self.generic_visit(node)

    def visit_Assign(self, node):
        self._record_operator("Assign")
        self.generic_visit(node)

    def visit_Call(self, node):
        self._record_operator("Call")
        self.generic_visit(node)

    # Operands
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self._record_operand(node.id)
        self.generic_visit(node)

    def visit_Constant(self, node):
        self._record_operand(str(node.value))
        self.generic_visit(node)


def calculate_halstead_metrics(func_ast: ast.AST) -> dict:
    """Calculate Halstead complexity measures."""
    visitor = HalsteadVisitor()
    visitor.visit(func_ast)

    n1 = len(visitor.operators)  # distinct operators
    n2 = len(visitor.operands)  # distinct operands
    n1_total = visitor.N1  # total operators
    n2_total = visitor.N2  # total operands

    n = n1 + n2  # vocabulary
    n_total = n1_total + n2_total  # length

    volume = 0.0
    if n > 0:
        volume = n_total * math.log2(n)

    difficulty = 0.0
    if n2 > 0:
        difficulty = (n1 / 2) * (n2_total / n2)

    effort = volume * difficulty

    return {
        "volume": volume,
        "difficulty": difficulty,
        "effort": effort,
    }


def calculate_maintainability_index(loc: int, cyclomatic: int, halstead_volume: float) -> float:
    """
    Standard formula used by Visual Studio and other tools.
    MI = MAX(0, (171 - 5.2 * ln(V) - 0.23 * G - 16.2 * ln(LOC)) * 100 / 171)
    """
    if loc <= 0:
        loc = 1
    if halstead_volume <= 0:
        halstead_volume = 1

    mi_raw = 171 - 5.2 * math.log(halstead_volume) - 0.23 * cyclomatic - 16.2 * math.log(loc)
    mi = (mi_raw * 100) / 171
    return max(0.0, min(100.0, mi))
