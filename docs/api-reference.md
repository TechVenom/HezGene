# HezGene Python API Reference

HezGene is engineered as a robust, programmable analysis and evolution platform. Beyond the command-line interface, HezGene provides a comprehensive Python API that can be seamlessly integrated into your CI/CD pipelines, test suites, or custom static analysis tools.

---

## 🧬 `FunctionDNA` Dataclass

The core of HezGene's analysis is the `FunctionDNA` object. Every function analyzed or evolved by the system is represented by this dataclass, which tracks extensive software engineering metrics.

### Key Attributes

#### Basic Metadata
- `name (str)`: The name of the function.
- `module (str)`: The module path.
- `qualified_name (str)`: The fully qualified name (e.g., `Class.method`).
- `source_code (str)`: The raw Python source code.

#### Advanced Software Engineering Metrics
HezGene empirically tests and statically analyzes your code to populate these metrics:
- `time_complexity (str)`: The Big O runtime complexity (e.g., `O(1)`, `O(n)`, `O(n²)`). Evaluated via dynamic input scaling.
- `space_complexity (str)`: The Big O space complexity based on peak memory allocation.
- `cyclomatic_complexity (int)`: The number of linearly independent paths through the function's source code.
- `halstead_effort (float)`: The mental effort required to develop or maintain the function, based on operators and operands.
- `maintainability_index (float)`: A standard metric (0-100) combining Halstead Volume, Cyclomatic Complexity, and Lines of Code.
- `test_coverage (float)`: The percentage of branches executed during empirical baseline testing.
- `leak_detected (bool)`: `True` if the function exhibits memory growth over 1,000 iterations.

#### Dependency Graph
- `dependencies (list[str])`: A list of functions called *by* this function.
- `dependents (list[str])`: A list of functions that *call* this function.
- `impact_score (str)`: Categorized impact level (e.g., `Low`, `Medium`, `High`, `Critical`) based on the number of dependents.

#### Performance & Evolution History
- `fitness_score (float)`: A composite score (0-100) evaluating speed, memory, maintainability, and algorithmic complexity.
- `avg_execution_time_ms (float)`: The empirical baseline execution speed.
- `peak_memory_bytes (int)`: The baseline memory allocation.
- `evolution_count (int)`: The number of times this function has been successfully evolved.

---

## ⚙️ `EvolutionEngine`

The `EvolutionEngine` is the primary orchestrator, connecting static analysis, mutation generation, the fitness gauntlet, and surgical deployment.

### Initialization

```python
from hezgene import EvolutionEngine

# Initialize the engine targeting the current working directory
engine = EvolutionEngine()

# Initialize the engine targeting a specific project path
engine = EvolutionEngine(project_root="/path/to/project")
```

### `evolve(target: str, generations: int = 5, apply: bool = False)`

Triggers the evolution cycle on a specified target.

**Parameters:**
- `target`: A string representing the target. Can be a directory (`src/`), a file (`src/utils.py`), a specific function (`src/utils.py:process_data`), or a priority heuristic (`slowest`, `buggiest`).
- `generations`: The number of mutant variants to spawn and evaluate.
- `apply`: If `True`, the engine will surgically inject the winning mutant into the source file. If `False`, the winner is safely written to the `.hezgene/sandbox/` directory.

**Returns:**
A dictionary containing the detailed battle report, including the original source, evolved source, improvement metrics, and sandbox paths.

```python
result = engine.evolve("src/utils.py:process_data", apply=False)

if result["status"] == "evolved":
    print(f"Original Time: {result['baseline']['speed_ms']}ms")
    print(f"Winner Sandbox: {result['sandbox_path']}")
```

### `evolve_all(apply: bool = False)`

Executes the evolution cycle across all functions currently tracked in the DNA registry.

---

## 🔬 `DNATracker`

The `DNATracker` manages the persistent genetic registry (`.hezgene/dna_registry.json`), tracking the historical evolution and metrics of your codebase.

Accessed via `engine.dna_tracker`.

### `get_dna(target: str) -> FunctionDNA | None`
Retrieves the `FunctionDNA` object for a specific target.
```python
dna = engine.dna_tracker.get_dna("src/utils.py:process_data")
if dna:
    print(f"Complexity: {dna.time_complexity}")
```

### `freeze(target: str)` / `unfreeze(target: str)`
Locks or unlocks a function, preventing it from being mutated during `evolve_all` or directory-wide runs.
```python
engine.dna_tracker.freeze("src/auth.py:hash_password")
```

---

## 🔍 `ProjectScanner`

The `ProjectScanner` traverses the codebase to extract functions, build dependency graphs, and rank targets for optimization.

### `get_ranked_targets(metric: str = "slowest", limit: int = 10) -> list[str]`
Returns a ranked list of function targets based on the specified metric (`slowest`, `buggiest`, `fitness`).

```python
from hezgene.analysis.project_scanner import ProjectScanner

scanner = ProjectScanner()
worst_offenders = scanner.get_ranked_targets(metric="fitness", limit=5)

for target in worst_offenders:
    print(f"Needs optimization: {target}")
```
