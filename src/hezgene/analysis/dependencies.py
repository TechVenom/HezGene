import ast
from pathlib import Path


class CallVisitor(ast.NodeVisitor):
    def __init__(self):
        self.calls = set()

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.calls.add(node.func.attr)
        self.generic_visit(node)


def analyze_project_dependencies(
    project_root: str,
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """
    Scans the project and maps function dependencies.
    Returns:
        calls_map: dict mapping function_name -> list of called functions
        called_by_map: dict mapping function_name -> list of caller functions
    """
    root = Path(project_root)
    calls_map = {}
    called_by_map = {}

    # Find all Python files
    for py_file in root.rglob("*.py"):
        if any(part.startswith(".") for part in py_file.parts) or "venv" in py_file.parts:
            continue

        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                caller_name = node.name
                if caller_name not in calls_map:
                    calls_map[caller_name] = []
                if caller_name not in called_by_map:
                    called_by_map[caller_name] = []

                visitor = CallVisitor()
                visitor.visit(node)

                for called in visitor.calls:
                    if called not in calls_map[caller_name]:
                        calls_map[caller_name].append(called)

                    if called not in called_by_map:
                        called_by_map[called] = []
                    if caller_name not in called_by_map[called]:
                        called_by_map[called].append(caller_name)

    return calls_map, called_by_map


def calculate_impact_score(dependents: list[str]) -> str:
    """Calculate impact score based on number of dependents."""
    count = len(dependents)
    if count == 0:
        return "Low"
    elif count <= 3:
        return f"Medium ({count} dependents)"
    elif count <= 10:
        return f"High ({count} dependents)"
    else:
        return f"Critical ({count} dependents)"
