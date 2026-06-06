# ruff: noqa: E402, E501

"""
HezGene CLI — Command-line interface for genetic software evolution.

Default behavior: sandbox mode (original code is NEVER modified).
Use --apply to actually deploy changes to the original file.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys


def _ensure_dependencies():
    """Automatically verify and install core dependencies."""
    required = {
        "click": "click",
        "rich_click": "rich-click",
        "rich": "rich",
        "psutil": "psutil",
        "git": "gitpython",
        "ast_comments": "ast-comments",
    }
    missing = []
    for module_name, pip_name in required.items():
        if importlib.util.find_spec(module_name) is None:
            missing.append(pip_name)

    if missing:
        print(f"🧬 HezGene is missing required dependencies: {', '.join(missing)}")
        print("Installing them automatically now...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            print("✅ Dependencies installed successfully!\n")
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies automatically.")
            print(f"Please run: pip install {' '.join(missing)}")
            sys.exit(1)


# Run dependency check immediately
_ensure_dependencies()

# Force UTF-8 for Windows consoles
if sys.stdout and sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import rich_click as click

click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.SHOW_EPILOG = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "magenta italic"

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table

import os
import json
import sys

def autonomous_options(f):
    import rich_click as click
    f = click.option("--non-interactive", is_flag=True, help="Skip all prompts, use defaults")(f)
    f = click.option("--output", type=click.Choice(["text", "json"]), default="text", help="Return machine-parseable JSON")(f)
    f = click.option("--yes", is_flag=True, help="Auto-confirm all actions")(f)
    return f

def is_autonomous(non_interactive):
    import os
    return non_interactive or os.environ.get("HEZGENE_NON_INTERACTIVE") == "1"

def print_json_and_exit(data, exit_code=0):
    import json
    import sys
    print(json.dumps(data, indent=2))
    sys.exit(exit_code)


from hezgene import __version__ as HEZGENE_VERSION
from hezgene.analysis.file_ingestor import FileIngestor
from hezgene.engine import EvolutionEngine

console = Console()


def _parse_target(target_args: tuple[str, ...]) -> str:
    """Helper to merge optional space-separated targets into colon-separated."""
    if not target_args:
        return ""
    if len(target_args) == 1:
        return target_args[0]
    return f"{target_args[0]}:{target_args[1]}"


@click.version_option(version=HEZGENE_VERSION)
@click.group(help="""
# 🧬 HezGene — The DNA of Software

HezGene is an autonomous genetic software evolution platform. It scans your code,
spawns mutants (AST & LLM-driven), pits them against each other in a fitness gauntlet,
and safely deploys the winner—all while guaranteeing strict functional correctness.

## 🚀 Core Workflow

1. **Initialize**:
   `hezgene init`
2. **Measure Baseline**:
   `hezgene dna file.py`
3. **Evolve** (Safely in `.hezgene/sandbox/`):
   `hezgene run file.py --llm --verbose`
4. **Verify Integrity**:
   `hezgene verify file.py`
5. **Deploy**:
   `hezgene run file.py --apply --llm`

## 🤖 Model Selection (LLM Evolution)

HezGene supports powerful LLM mutations via **Ollama**, **OpenAI**, **Anthropic**, **Gemini**, and **VENOMX**.

Use the config command to set your intelligence engine:
```bash
hezgene config --set llm.provider ollama
hezgene config --set llm.model gemma2:2b

hezgene config --set llm.provider openai
hezgene config --set llm.model gpt-4o
```
Once configured, simply pass the `--llm` flag to the `run` command.

---
Run `hezgene COMMAND --help` for detailed instructions on any command.
""")
def main():
    """HezGene -- The DNA of Software"""
    pass


@main.command(help="""
Initialize HezGene in the current project.

This creates the .hezgene directory which houses the DNA registry
and the Sandbox. Run this once per project before evolving any code.

Example:
  hezgene init
""")
@autonomous_options
def init(non_interactive, output, yes):
    """Initialize HezGene in the current project."""
    from pathlib import Path

    hezgene_dir = Path(".hezgene")
    hezgene_dir.mkdir(exist_ok=True)
    (hezgene_dir / "dna_registry.json").write_text("{}", encoding="utf-8")
    (hezgene_dir / "history.json").write_text("[]", encoding="utf-8")
    (hezgene_dir / "backups").mkdir(exist_ok=True)

    (hezgene_dir / "sandbox").mkdir(exist_ok=True)
    if output == "json":
        print_json_and_exit({"status": "success", "message": "HezGene initialized!"}, 0)
    console.print(

        Panel(
            "[bold green]HezGene initialized![/]\n\n"
            "Your project now has genetic evolution.\n"
            "Run [cyan]hezgene run <file.py>[/] to start.\n"
            "Results go to [cyan].hezgene/sandbox/[/] (original code is never modified).",
            title="HezGene",
            border_style="green",
        )
    )


@main.command(help="""
Show the current system status and settings.

This displays whether HezGene is initialized, tracks the total
evolved functions, shows your active configuration, and tests
the connection to your configured LLM provider.

Example:
  hezgene status
""")
@autonomous_options
def status(non_interactive, output, yes):
    """Show the current system status and test LLM connection."""
    from pathlib import Path

    from rich.table import Table


    from .core.config import HezGeneConfig
    from .core.dna_tracker import DNATracker

    hezgene_dir = Path(".hezgene")
    is_init = hezgene_dir.exists()

    cfg = HezGeneConfig()
    provider_name = cfg.get_llm_provider_name()
    model_name = cfg.get("llm.model", "(default)")

    evolved_count = 0
    if is_init:
        tracker = DNATracker(project_root=".")
        registry = tracker._registry
        evolved_count = sum(
            1 for dna in registry.values() if getattr(dna, "evolution_count", 0) > 0
        )

    table = Table(title="HezGene System Status", border_style="green", show_header=False)
    table.add_column("Key", style="bold cyan")
    table.add_column("Value", style="white")

    table.add_row("Initialized", "[green]Yes[/]" if is_init else "[red]No (Run 'hezgene init')[/]")
    table.add_row("Evolved Functions", str(evolved_count))
    table.add_row("LLM Provider", provider_name)
    table.add_row("LLM Model", model_name)


    console.print()
    console.print(table)

    # Test LLM Connection
    console.print("\n[dim]Testing LLM Connection...[/]")
    try:
        from hezgene.mutation.llm import get_provider
        provider = get_provider(provider_name, **cfg.get_llm_config())
        model_name = cfg.get("llm.model") or provider.model
        console.print(f"[dim]Pinging {provider_name} ({model_name})...[/]")
        res = provider.generate("Respond with exactly: 'Hello HezGene! I am connected.'")

        if not res.success:
            console.print(f"[bold red]❌ Connection failed:[/] {res.error}")
        else:
            response_text = res.text.strip()
            if response_text:
                console.print(f"[bold green]✅ Connected to {provider_name} successfully![/]")
                console.print(f"[cyan]🤖 Model replied:[/] {response_text}")
            else:
                console.print(
                    f"[bold yellow]⚠️ Connected, but received an empty response from {provider_name}.[/]"
                )
    except Exception as e:
        console.print(f"[bold red]❌ Failed to connect to {provider_name}: {str(e)}[/]")
    console.print()


@main.command(help="""
Clear the sandbox and optionally the DNA registry.

If your .hezgene/sandbox directory is getting full of old tests,
you can wipe it clean. Use --all to start completely fresh.

Example:
  hezgene clean
  hezgene clean --all
""")
@click.option("--all", "clear_dna", is_flag=True, help="Clear DNA registry as well as sandbox")
@autonomous_options
def clean(clear_dna, non_interactive, output, yes):
    """Clear the sandbox and optionally the DNA registry."""
    from pathlib import Path

    hezgene_dir = Path(".hezgene")
    sandbox_dir = hezgene_dir / "sandbox"
    dna_file = hezgene_dir / "dna_registry.json"

    if sandbox_dir.exists():
        for file in sandbox_dir.glob("*"):
            file.unlink()
        console.print("[green]Sandbox cleared.[/]")
    else:
        console.print("[yellow]Sandbox directory not found.[/]")

    if clear_dna:
        if dna_file.exists():
            dna_file.write_text("{}", encoding="utf-8")
            console.print("[green]DNA registry cleared.[/]")
        else:
            console.print("[yellow]DNA registry not found.[/]")


@main.command(help="""
Start the HezGene Web Dashboard.

This launches both the frontend and backend servers concurrently, allowing
you to manage code evolution, view the DNA explorer, and watch live battles.

Example:
  hezgene web
""")
@click.option("--host", default="127.0.0.1", show_default=True, help="Host to bind the server")
@click.option("--port", default=8000, show_default=True, type=int, help="Port to bind the server")
@autonomous_options
def web(host, port, non_interactive, output, yes):
    """Start the HezGene Web Interface."""
    from hezgene.web.launcher import launch_dashboard
    launch_dashboard(host=host, port=port)


@main.command(help="""
Verify evolved code produces identical outputs to originals.

Scans the sandbox for evolved functions, auto-generates test inputs
from type hints, runs both versions side-by-side, and reports any
mismatches.

If given a file path, verifies that specific file's evolutions.
If given a file path and function name, verifies that specific function.

Example:
  hezgene verify
  hezgene verify examples/test_filter.py
  hezgene verify examples/test_filter.py filter_active_users
""")
@click.argument("target_args", nargs=-1)
@autonomous_options
def verify(target_args, non_interactive, output, yes):
    """Verify evolved code produces identical outputs to originals."""
    import ast
    from pathlib import Path

    from hezgene.evaluation.gauntlet import FitnessGauntlet

    parsed_target = _parse_target(target_args)
    sandbox_dir = Path(".hezgene") / "sandbox"


    if not sandbox_dir.exists():
        if output == "json":
            print_json_and_exit({"status": "error", "message": "No sandbox found."}, 2)
        console.print("[yellow]No sandbox found. Run 'hezgene run' first.[/]")
        return


    console.print(Rule("HezGene -- Verification"))
    console.print()

    # If a specific target is given, verify only that
    if parsed_target and Path(parsed_target.split(":")[0]).is_file():
        file_path = parsed_target.split(":")[0]
        func_name = parsed_target.split(":")[1] if ":" in parsed_target else None
        funcs = FileIngestor.extract(file_path)
        if func_name:
            funcs = [f for f in funcs if f.name == func_name or f.qualified_name == func_name]
        _verify_functions(funcs, sandbox_dir, console)
        return

    # Otherwise scan all sandbox files
    orig_files = sorted(sandbox_dir.glob("*_original.py"))
    if not orig_files:
        console.print("[yellow]No evolved functions in sandbox.[/]")
        return

    gauntlet = FitnessGauntlet()
    total_pass = 0
    total_fail = 0

    for orig_file in orig_files:
        evol_file = orig_file.parent / orig_file.name.replace("_original.py", "_evolved.py")
        if not evol_file.exists():
            continue

        orig_src = orig_file.read_text(encoding="utf-8")
        evol_src = evol_file.read_text(encoding="utf-8")

        # Strip the header comment
        orig_lines = orig_src.splitlines()
        evol_lines = evol_src.splitlines()

        orig_path = None
        for line in orig_lines:
            if line.startswith("# ORIGINAL:"):
                orig_path = line.replace("# ORIGINAL:", "").strip().split(":")[0]
                break

        orig_code = "\n".join(
            line for line in orig_lines if not line.startswith("# ORIGINAL:")
        ).strip()
        evol_code = "\n".join(
            line for line in evol_lines if not line.startswith("# EVOLVED:")
        ).strip()

        if not orig_code or not evol_code:
            continue

        # Extract function name
        try:
            tree = ast.parse(orig_code)
            func_nodes = [
                n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            if not func_nodes:
                continue
            fname = func_nodes[0].name
        except SyntaxError:
            continue

        # Generate test inputs and verify
        test_inputs = gauntlet._generate_test_inputs(orig_code, fname)
        if not test_inputs:
            test_inputs = [()]

        module_source = None
        if orig_path:
            try:
                module_source = Path(orig_path).read_text(encoding="utf-8")
            except Exception:
                pass

        try:
            orig_fn = gauntlet._compile_function(orig_code, fname, module_source)
            evol_fn = gauntlet._compile_function(evol_code, fname, module_source)
        except Exception as e:
            console.print(f"  [red]✗[/] {fname} — Compilation error: {e}")
            total_fail += 1
            continue

        passed = True
        fail_input = None
        for args in test_inputs:
            try:
                orig_out = orig_fn(*args)
            except Exception:
                continue
            try:
                evol_out = evol_fn(*args)
                if orig_out != evol_out:
                    passed = False
                    fail_input = args
                    break
            except Exception:
                passed = False
                fail_input = args
                break

        if passed:
            console.print(
                f"  [green]✓[/] {fname} — [green]PASS[/] ({len(test_inputs)} inputs tested)"
            )
            total_pass += 1
        else:
            console.print(f"  [red]✗[/] {fname} — [red]FAIL[/] on input: {fail_input}")
            total_fail += 1


    if output == "json":
        if total_fail > 0:
            print_json_and_exit({"status": "error", "passed": total_pass, "failed": total_fail}, 4)
        else:
            print_json_and_exit({"status": "success", "passed": total_pass, "failed": total_fail}, 0)

    console.print()
    if total_fail == 0 and total_pass > 0:

        console.print(
            Panel(f"[bold green]All {total_pass} verifications passed![/]", border_style="green")
        )
    elif total_fail > 0:
        console.print(
            Panel(
                f"[bold red]{total_fail} failed[/], [green]{total_pass} passed[/]",
                border_style="red",
            )
        )
    else:
        console.print("[yellow]No functions to verify.[/]")


def _verify_functions(funcs, sandbox_dir, console):
    """Verify specific functions against their sandbox versions."""
    from hezgene.evaluation.gauntlet import FitnessGauntlet

    gauntlet = FitnessGauntlet()
    for f in funcs:
        test_inputs = gauntlet._generate_test_inputs(f.source_code, f.name)
        if not test_inputs:
            test_inputs = [()]
        console.print(f"  [dim]Verifying {f.name} with {len(test_inputs)} inputs...[/]")

        # Read full module source for context injection
        try:
            from pathlib import Path

            module_source = Path(f.file_path).read_text(encoding="utf-8")
        except Exception:
            module_source = None

        try:
            fn = gauntlet._compile_function(f.source_code, f.name, module_source)
            for args in test_inputs:
                fn(*args)
            console.print(f"  [green]✓[/] {f.name} — [green]Original runs correctly[/]")
        except Exception as e:
            console.print(f"  [red]✗[/] {f.name} — [red]Error: {e}[/]")


@main.command(help="""
Run evolution on a target.

Generates mutants, runs them through the fitness gauntlet, and outputs
the winner to the sandbox. Your original code is never modified unless
you pass the --apply flag.

Targets can be:
  - A directory (e.g. 'src/')
  - A file (e.g. 'src/utils.py')
  - A specific function/method (e.g. 'src/utils.py:func')

Priority targets:
  - 'slowest': Automatically pick and evolve the slowest function.
  - 'buggiest': Automatically pick and evolve the buggiest function.

LLM Mutations (Phase 2):
  Use --llm to add LLM-powered mutations alongside AST mutations.
  Use --llm-only to skip AST mutations and use only LLM.

Example:
  hezgene run src/utils.py
  hezgene run src/utils.py -v
  hezgene run src/utils.py --llm -v
  hezgene run src/utils.py --llm --provider ollama --model codellama
  hezgene run src/utils.py:calculate_stats --apply -g 10
  hezgene run --target slowest --llm-only
""")
@click.argument("target_args", nargs=-1)
@click.option("--all", "evolve_all", is_flag=True, help="Evolve all tracked functions")
@click.option(
    "--target",
    "priority_target",
    type=click.Choice(["slowest", "buggiest"]),
    help="Evolve priority target",
)
@click.option(
    "--apply", is_flag=True, help="Actually modify the original files (default: sandbox only)"
)
@click.option("--generations", "-g", default=5, help="Number of mutations")
@click.option("--llm", "use_llm", is_flag=True, help="Enable LLM-powered mutations (Phase 2)")
@click.option("--llm-only", "llm_only", is_flag=True, help="Use ONLY LLM mutations (skip AST)")
@click.option(
    "--provider",
    "llm_provider",
    default="",
    help="LLM provider (ollama, openai, anthropic, gemini)",
)
@click.option(
    "--model", "llm_model", default="", help="LLM model name (e.g. codellama, gpt-4o-mini)"
)
@autonomous_options
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show the full battle arena with mutant fights and rankings",
)
def run(
    target_args,
    evolve_all,
    priority_target,
    apply,
    generations,
    use_llm,
    llm_only,
    llm_provider,
    llm_model,
    verbose,
    non_interactive,
    output,
    yes
):
    """Run evolution. Results go to sandbox by default. Use --apply to modify originals."""
    engine = EvolutionEngine(
        use_llm=use_llm or llm_only,
        llm_only=llm_only,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )

    # Show LLM status if enabled
    if use_llm or llm_only:
        provider_name = llm_provider or engine._llm_provider_name or "ollama"
        model_name = llm_model or engine._llm_model or "(default)"
        mode = "LLM-only" if llm_only else "AST + LLM"
        console.print(
            f"  [magenta]LLM Mode:[/] {mode} | Provider: [cyan]{provider_name}[/] | Model: [cyan]{model_name}[/]"
        )
        console.print()

    path = _parse_target(target_args)
    target_to_run = path
    if priority_target:
        target_to_run = priority_target

    if evolve_all:
        results = engine.evolve_all(apply=apply)
        _print_summary(results, apply, verbose)
    elif target_to_run:
        # Show file analysis first
        from pathlib import Path

        target_path = Path(target_to_run.split(":")[0])
        if target_path.is_file():
            _print_analysis(target_path)


        try:
            result = engine.evolve(target_to_run, generations=generations, apply=apply, use_llm=use_llm or llm_only)
            
            if output == "json":
                results_list = result if isinstance(result, list) else [result]
                evolved = []
                unchanged = 0
                errors = 0
                for r in results_list:
                    if r.get("status") == "evolved":
                        impr = r.get("improvements", {})
                        evolved.append({
                            "function": r.get("target", "").split(":")[-1],
                            "file": r.get("target", "").split(":")[0],
                            "strategy": r.get("battle_results", [{}])[0].get("strategy", ""),
                            "fitness_before": impr.get("fitness_before", 0),
                            "fitness_after": impr.get("fitness_after", 0),
                            "speed_change": f"{impr.get('speed_change_ms', 0)}ms",
                            "memory_change": f"{impr.get('memory_change_bytes', 0)}B",
                            "lines_before": 0,
                            "lines_after": 0
                        })
                    elif r.get("status") == "error":
                        errors += 1
                    else:
                        unchanged += 1
                
                final_json = {
                    "status": "success" if evolved else ("no_improvement" if unchanged else "error"),
                    "evolved": evolved,
                    "unchanged": unchanged,
                    "errors": errors,
                    "sandbox_path": ".hezgene/sandbox/" if not apply else None,
                    "duration_seconds": 0.0
                }
                if not evolved and not unchanged and errors > 0:
                    print_json_and_exit(final_json, 1)
                if not evolved and unchanged == 0 and errors == 0:
                    print_json_and_exit(final_json, 3)
                if not evolved and unchanged > 0:
                    print_json_and_exit(final_json, 4)
                print_json_and_exit(final_json, 0)
                
            if isinstance(result, list):
                _print_summary(result, apply, verbose)
            else:
                _print_result(result, apply, verbose=True)
        except Exception as e:
            if output == "json":
                print_json_and_exit({"status": "error", "error": str(e)}, 1)
            raise
    else:
        console.print("[red]Specify a path (file/dir) or use --all / --target[/]")


@main.command(help="""
Analyze a file and show what's evolvable.

Displays a breakdown of which functions and classes are evolvable,
and which are skipped (e.g. __init__ or frozen functions).

Example:
  hezgene scan src/main.py
""")
@click.argument("target_args", nargs=-1)
@autonomous_options
def scan(target_args, non_interactive, output, yes):
    """Analyze a file and show what's evolvable."""
    path = _parse_target(target_args)
    if not path:
        if output == "json":
            print_json_and_exit({"status": "error", "message": "Please provide a file to scan."}, 1)
        console.print("[red]Please provide a file to scan.[/]")
        return
    from pathlib import Path
    
    target_path = Path(path)
    if target_path.is_dir():
        from hezgene.engine import EvolutionEngine
        engine = EvolutionEngine()
        targets = engine.scanner.scan_directory(target_path)
        
        if output == "json":
            if not targets:
                print_json_and_exit({"status": "error", "message": "No evolvable Python files found"}, 3)
            print_json_and_exit({"status": "success", "targets": targets}, 0)
            
        files = set(Path(engine.project_root) / t.split(":")[0] for t in targets)
        if not files:
            console.print(f"[yellow]No evolvable Python files found in {target_path}.[/]")
            return
            
        for f in sorted(files):
            _print_analysis(f)
    else:
        if output == "json":
            from hezgene.analysis.file_ingestor import FileIngestor
            try:
                info = FileIngestor.analyze_file(str(target_path))
                print_json_and_exit({"status": "success", "info": {
                    "total_functions": info["total_functions"],
                    "evolvable": [f.name for f in info["evolvable"]]
                }}, 0)
            except Exception as e:
                print_json_and_exit({"status": "error", "message": str(e)}, 1)
        _print_analysis(target_path)


@main.command(help="""
Show the DNA profile for a function.

Displays the exact DNA profile (Memory, Speed, Complexity, LOC)
for a specific function.

Example:
  hezgene dna src/utils.py:process_data
""")
@click.argument("target_args", nargs=-1)
@autonomous_options
def dna(target_args, non_interactive, output, yes):
    """Show the DNA profile for a function or file."""
    target = _parse_target(target_args)
    if not target:
        if output == "json":
            print_json_and_exit({"status": "error", "message": "Please provide a target."}, 1)
        console.print("[red]Please provide a target.[/]")
        return

    engine = EvolutionEngine()

    file_path = target.split(":")[0]
    func_name = target.split(":")[1] if ":" in target else None

    from pathlib import Path

    if not Path(file_path).exists():
        console.print(f"[red]File {file_path} not found.[/]")
        return

    from hezgene.analysis.file_ingestor import FileIngestor

    funcs = FileIngestor.extract(file_path)

    if func_name:
        funcs = [f for f in funcs if f.name == func_name or f.qualified_name == func_name]
        if not funcs:
            console.print(f"[yellow]Function {func_name} not found in {file_path}.[/]")
            return
    else:
        funcs = [f for f in funcs if f.evolvable]
        if not funcs:
            console.print(f"[yellow]No evolvable functions found in {file_path}.[/]")
            return

    from .core.dna_tracker import FunctionDNA
    from hezgene.evaluation.gauntlet import FitnessGauntlet

    gauntlet = FitnessGauntlet()

    if output == "json":
        res = []
        for func in funcs:
            func_target = f"{file_path}:{func.qualified_name or func.name}"
            func_dna = engine.dna_tracker.get_dna(func_target)
            if not func_dna:
                func_dna = FunctionDNA(
                    name=func.name,
                    module=file_path.replace("/", ".").replace(".py", ""),
                    qualified_name=func.qualified_name or func.name,
                    source_code=func.source_code,
                    lines_of_code=func.lines_of_code,
                    cyclomatic_complexity=func.cyclomatic_complexity,
                    halstead_effort=func.halstead_effort,
                    halstead_volume=func.halstead_volume,
                    maintainability_index=func.maintainability_index,
                )
                baseline = gauntlet._evaluate_single(func_dna, func_dna)
                func_dna.avg_execution_time_ms = baseline.avg_speed_ms
                func_dna.peak_memory_bytes = baseline.peak_memory_bytes
                func_dna.readability_score = baseline.readability_score
            res.append({
                "function": func.qualified_name or func.name,
                "file": file_path,
                "loc": func_dna.lines_of_code,
                "complexity": func_dna.cyclomatic_complexity,
                "speed_ms": getattr(func_dna, 'avg_execution_time_ms', 0),
                "memory_bytes": getattr(func_dna, 'peak_memory_bytes', 0),
                "fitness": getattr(func_dna, 'fitness_score', 0)
            })
        print_json_and_exit({"status": "success", "dna": res}, 0)

    for func in funcs:
        func_target = f"{file_path}:{func.qualified_name or func.name}"
        func_dna = engine.dna_tracker.get_dna(func_target)

        if not func_dna:
            console.print(f"[dim]Measuring baseline DNA for {func_target}...[/]")
            func_dna = FunctionDNA(
                name=func.name,
                module=file_path.replace("/", ".").replace(".py", ""),
                qualified_name=func.qualified_name or func.name,
                source_code=func.source_code,
                lines_of_code=func.lines_of_code,
                cyclomatic_complexity=func.cyclomatic_complexity,
                halstead_effort=func.halstead_effort,
                halstead_volume=func.halstead_volume,
                maintainability_index=func.maintainability_index,
            )
            baseline = gauntlet._evaluate_single(func_dna, func_dna)
            func_dna.avg_execution_time_ms = baseline.avg_speed_ms
            func_dna.peak_memory_bytes = baseline.peak_memory_bytes
            func_dna.readability_score = baseline.readability_score

        # Format Helpers
        def c_color(score, thresholds, inverse=False):
            if score == "Unknown":
                return ""
            if inverse:
                if score <= thresholds[0]:
                    return "🟢"
                if score <= thresholds[1]:
                    return "🟡"
                return "🔴"
            else:
                if score >= thresholds[0]:
                    return "🟢"
                if score >= thresholds[1]:
                    return "🟡"
                return "🔴"

        def big_o_color(c):
            if c in ("O(1)", "O(log n)"):
                return "🟢"
            if c in ("O(n)", "O(n log n)"):
                return "🟡"
            return "🔴"

        # Construct Layout
        console.print(f"\n🧬 [bold cyan]Function DNA:[/] {func_target.split(':')[-1]}")
        console.print("━" * 50)

        console.print("\n📊 [bold]Complexity Analysis:[/]")
        console.print(
            f"   Time Complexity:     {func_dna.time_complexity} {big_o_color(func_dna.time_complexity)}"
        )
        console.print(
            f"   Space Complexity:    {func_dna.space_complexity} {big_o_color(func_dna.space_complexity)}"
        )
        c_emoji = c_color(func_dna.cyclomatic_complexity, (5, 10), True)
        console.print(f"   Cyclomatic:          {func_dna.cyclomatic_complexity} {c_emoji}")
        h_emoji = c_color(func_dna.halstead_effort, (500, 2000), True)
        console.print(f"   Halstead Effort:     {func_dna.halstead_effort:,.0f} {h_emoji}")
        m_emoji = c_color(func_dna.maintainability_index, (85, 65))
        console.print(f"   Maintainability:     {func_dna.maintainability_index:.0f}/100 {m_emoji}")

        console.print("\n⚡ [bold]Performance:[/]")
        console.print(f"   Avg Speed:           {func_dna.avg_execution_time_ms:.4f} ms")
        console.print(f"   Peak Memory:         {func_dna.peak_memory_bytes:,} bytes")
        console.print(f"   Scalability:         {func_dna.scalability_score}")

        console.print("\n🛡️ [bold]Reliability:[/]")
        console.print(f"   Bug Count:           {func_dna.bug_count}")
        console.print(f"   Test Coverage:       {func_dna.test_coverage * 100:.0f}%")
        uncov = ", ".join(func_dna.uncovered_branches) if func_dna.uncovered_branches else "None"
        console.print(f"   Uncovered:           {uncov}")

        console.print("\n🔗 [bold]Dependencies:[/]")
        calls = ", ".join(func_dna.dependencies) if func_dna.dependencies else "None"
        called_by = ", ".join(func_dna.dependents) if func_dna.dependents else "None"
        console.print(f"   Called by:           {called_by}")
        console.print(f"   Calls:               {calls}")
        console.print(f"   Impact Score:        {func_dna.impact_score}")

        console.print("\n📈 [bold]Evolution History:[/]")
        console.print(f"   Evolved:             {func_dna.evolution_count} times")
        from datetime import datetime

        last_ev = (
            datetime.fromtimestamp(func_dna.last_evolved_at).strftime("%Y-%m-%d")
            if func_dna.last_evolved_at
            else "Never"
        )
        console.print(f"   Last Evolved:        {last_ev}")

        f_emoji = c_color(func_dna.fitness_score, (85, 65))
        console.print(
            f"\n🧬 [bold magenta]Genetic Score: {func_dna.fitness_score:.1f}/100[/] {f_emoji}\n"
        )


@main.command(help="""
Show evolution history.

Displays a tabular history of all evolutions that have occurred
across your project.

Example:
  hezgene log
""")
@autonomous_options
def log(non_interactive, output, yes):
    """Show evolution history."""
    engine = EvolutionEngine()
    entries = engine.dna_tracker.get_evolution_log()

    if not entries:
        if output == "json":
            print_json_and_exit({"status": "success", "history": []}, 0)
        console.print("[yellow]No evolution history yet.[/]")
        return
        
    if output == "json":
        print_json_and_exit({"status": "success", "history": entries}, 0)

    table = Table(title="Evolution Log", border_style="magenta")
    table.add_column("Function", style="bold")
    table.add_column("Evolutions", justify="center")
    table.add_column("Fitness", justify="center", style="green")
    table.add_column("Frozen", justify="center")

    for e in entries:
        table.add_row(
            e["target"],
            str(e["evolutions"]),
            f"{e['fitness']:.1f}",
            "Frozen" if e["frozen"] else "",
        )
    console.print(table)


@main.command(help="""
Freeze a function -- stop it from evolving.

Locks a function so that it can never be mutated or evolved
by the run command. Useful for cryptographic hashing or compliance logic.

Example:
  hezgene freeze src/auth.py:verify_token
""")
@click.argument("target_args", nargs=-1)
@autonomous_options
def freeze(target_args, non_interactive, output, yes):
    """Freeze a function -- stop it from evolving."""
    target = _parse_target(target_args)
    if not target:
        console.print("[red]Please provide a target.[/]")
        return
    engine = EvolutionEngine()
    engine.dna_tracker.freeze(target)
    console.print(f"[cyan]Frozen:[/] {target}")


@main.command(help="""
Unfreeze a function -- resume evolution.

Unlocks a previously frozen function, allowing it to evolve again.

Example:
  hezgene unfreeze src/auth.py:verify_token
""")
@click.argument("target_args", nargs=-1)
@autonomous_options
def unfreeze(target_args, non_interactive, output, yes):
    """Unfreeze a function -- resume evolution."""
    target = _parse_target(target_args)
    if not target:
        console.print("[red]Please provide a target.[/]")
        return
    engine = EvolutionEngine()
    engine.dna_tracker.unfreeze(target)
    console.print(f"[green]Unfrozen:[/] {target}")


@main.command(help="""
Revert a deployed evolution back to the previous version.

Restores the previous DNA state of a function. Only applicable
if the function was previously evolved using the --apply flag.

Example:
  hezgene rollback src/utils.py:process_data
""")
@click.argument("target_args", nargs=-1)
@autonomous_options
def rollback(target_args, non_interactive, output, yes):
    """Revert a deployed evolution back to the previous version."""
    target = _parse_target(target_args)
    if not target:
        console.print("[red]Please provide a target.[/]")
        return
    file_path = target.split(":")[0]
    try:
        from .deployment.deployer import AutoDeployer

        deployer = AutoDeployer(".")
        res = deployer.rollback_latest(file_path)
        if output == "json":
            print_json_and_exit({"status": "success", "data": res}, 0)
        console.print(
            f"[bold green]✅ Rolled back[/] {file_path}\n"
            f"[dim]Restored from:[/] {res.get('backup')}"
        )
    except Exception as e:
        if output == "json":
            print_json_and_exit({"status": "error", "error": str(e)}, 1)
        console.print(f"[bold red]❌ Rollback failed:[/] {e}")


@main.command(help="""
Configure global HezGene settings.

Manage LLM provider settings, evolution parameters, and safety options.
Settings are stored in .hezgene/config.json.

Key format uses dot notation:
  llm.provider      — LLM provider (ollama, openai, anthropic, gemini)
  llm.model         — Model name (e.g. codellama, gpt-4o-mini)
  llm.api_key       — API key for paid providers
  llm.base_url      — Custom endpoint URL
  llm.temperature   — Generation temperature (0.0-1.0)
  evolution.use_llm  — Enable LLM mutations by default (true/false)
  evolution.generations — Default mutation count
  evolution.min_improvement — Minimum improvement threshold

Example:
  hezgene config --list
  hezgene config --set llm.provider ollama
  hezgene config --set llm.model codellama
  hezgene config --set evolution.use_llm true
  hezgene config --get llm.provider
""")
@click.option("--set", "set_var", nargs=2, help="Set a config value (key value)")
@click.option("--get", "get_var", default="", help="Get a config value by key")
@click.option("--list", "list_vars", is_flag=True, help="List all configurations")
@autonomous_options
def config(set_var, get_var, list_vars, non_interactive, output, yes):
    """Configure global HezGene settings."""
    from .core.config import HezGeneConfig

    cfg = HezGeneConfig()

    if set_var:
        key, value = set_var
        cfg.set(key, value)
        console.print(f"  [green]Set[/] {key} = [cyan]{cfg.get(key)}[/]")

    elif get_var:
        value = cfg.get(get_var)
        if value is not None:
            console.print(f"  {get_var} = [cyan]{value}[/]")
        else:
            console.print(f"  [yellow]{get_var} not found[/]")

    elif list_vars:
        all_config = cfg.get_all()
        if output == "json":
            print_json_and_exit({"status": "success", "config": all_config}, 0)
        table = Table(title="HezGene Configuration", border_style="cyan")
        table.add_column("Key", style="bold")
        table.add_column("Value", style="green")

        def _flatten(d: dict, prefix: str = "") -> list:
            items = []
            for k, v in d.items():
                full_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    items.extend(_flatten(v, full_key))
                else:
                    items.append((full_key, v))
            return items

        for key, val in _flatten(all_config):
            display_val = str(val)
            if "api_key" in key and val:
                display_val = val[:8] + "..." if len(str(val)) > 8 else "***"
            table.add_row(key, display_val)

        console.print(table)

    else:
        console.print("[dim]Use --list, --get <key>, or --set <key> <value>[/]")


@main.command(help="""
Manage LLM providers for intelligent mutations.

Test connectivity, list models, and check provider status.

Example:
  hezgene llm --status
  hezgene llm --models
  hezgene llm --test "Optimize this: def f(x): return x*2"
""")
@click.option("--status", is_flag=True, help="Check LLM provider status")
@click.option("--models", "list_models", is_flag=True, help="List available models")
@click.option("--test", "test_prompt", default="", help="Send a test prompt")
@click.option("--provider", default="", help="Override provider")
@click.option("--model", default="", help="Override model")
@autonomous_options
def llm(status, list_models, test_prompt, provider, model, non_interactive, output, yes):
    """Manage LLM providers for intelligent mutations."""
    from .core.config import HezGeneConfig
    from hezgene.mutation.llm import get_provider, list_providers

    cfg = HezGeneConfig()
    provider_name = provider or cfg.get_llm_provider_name()
    llm_config = cfg.get_llm_config()
    if model:
        llm_config["model"] = model

    if status:
        console.print(Rule("LLM Provider Status"))
        console.print(f"  Provider: [cyan]{provider_name}[/]")
        console.print(f"  Model: [cyan]{llm_config.get('model', '(default)')}[/]")
        console.print(f"  Available providers: {', '.join(list_providers())}")
        console.print()

        try:
            p = get_provider(provider_name, **llm_config)
            available = p.is_available()
            if available:
                console.print("  Status: [bold green]CONNECTED[/]")
            else:
                console.print("  Status: [bold red]NOT AVAILABLE[/]")
                if provider_name == "ollama":
                    console.print("  [dim]Ensure Ollama is running: ollama serve[/]")
                else:
                    console.print("  [dim]Check API key and network connection.[/]")
        except Exception as e:
            console.print(f"  Status: [bold red]ERROR[/] — {e}")

    elif list_models:
        try:
            p = get_provider(provider_name, **llm_config)
            if hasattr(p, "list_models"):
                models = p.list_models()
                if models:
                    console.print(f"  [cyan]{provider_name}[/] models:")
                    for m in models:
                        console.print(f"    • {m}")
                else:
                    console.print(f"  [yellow]No models found for {provider_name}[/]")
            else:
                console.print(f"  [yellow]Model listing not supported for {provider_name}[/]")
        except Exception as e:
            console.print(f"  [red]Error: {e}[/]")

    elif test_prompt:
        console.print(f"  Sending to [cyan]{provider_name}[/]...")
        try:
            p = get_provider(provider_name, **llm_config)
            response = p.generate_timed(test_prompt)
            if response.success:
                console.print(
                    Panel(
                        response.text[:2000],
                        title=f"{provider_name} ({p.model})",
                        subtitle=f"{response.latency_ms:.0f}ms | {response.total_tokens} tokens",
                        border_style="green",
                    )
                )
            else:
                console.print(f"  [red]Error:[/] {response.error}")
        except Exception as e:
            console.print(f"  [red]Error: {e}[/]")

    else:
        console.print("[dim]Use --status, --models, or --test <prompt>[/]")


# ── Display Helpers ────────────────────────────────────────────


def _print_analysis(file_path):
    """Show file analysis."""
    try:
        info = FileIngestor.analyze_file(file_path)
    except Exception as e:
        console.print(f"[red]Error analyzing {file_path}: {e}[/]")
        return

    console.print(Rule(f"HezGene -- Analyzing {file_path}"))
    console.print(f"\n  Found: [bold]{info['total_functions']}[/] functions/methods")
    if info["classes"]:
        console.print(f"  Classes: {', '.join(info['classes'])}")
    console.print()

    if info["evolvable"]:
        console.print("  [green]Evolvable:[/]")
        for f in info["evolvable"]:
            label = f"{f.class_name}.{f.name}" if f.class_name else f.name
            console.print(
                f"    [green]>[/] {label:<30} (line {f.start_line}, {f.lines_of_code} LOC)"
            )

    if info["skipped"]:
        console.print("  [dim]Skipped:[/]")
        for f in info["skipped"]:
            label = f"{f.class_name}.{f.name}" if f.class_name else f.name
            console.print(f"    [dim]x {label:<30} ({f.skip_reason})[/]")

    console.print()


def _print_battle_arena(result: dict):
    """Print the full battle arena showing all mutants, their scores, and the fight."""
    from rich.table import Table


    target = result.get("target", "?")
    short_target = target.split(":")[-1] if ":" in target else target
    baseline = result.get("baseline", {})
    spawn_log = result.get("spawn_log", [])
    battle = result.get("battle_results", [])
    total = result.get("total_mutants", 0)

    # ── Spawn Report ──
    console.print()
    console.print(Rule(f"[bold magenta]⚗️  Mutation Lab — {short_target}[/]"))
    console.print()

    for entry in spawn_log:
        mtype = entry.get("type", "?")
        count = entry.get("count", 0)
        if mtype == "AST":
            console.print(f"  [magenta]🧬 AST Mutations:[/]  {count} mutants spawned")
        elif mtype == "LLM":
            provider = entry.get("provider", "?")
            if entry.get("error"):
                console.print(f"  [red]🤖 LLM Mutations:[/]  Failed — {entry['error']}")
            else:
                console.print(
                    f"  [blue]🤖 LLM Mutations:[/]  {count} mutants from [cyan]{provider}[/]"
                )

    console.print(f"  [dim]Total Combatants: {total}[/]")

    # ── Baseline ──
    console.print()
    console.print("  [bold]📊 Original Baseline:[/]")
    console.print(
        f"     Fitness: [cyan]{baseline.get('fitness', 0):.1f}[/]  |  "
        f"Speed: [cyan]{baseline.get('speed_ms', 0):.4f} ms[/]  |  "
        f"Memory: [cyan]{baseline.get('memory_bytes', 0):,} B[/]"
    )

    # ── Battle Table ──
    if battle:
        console.print()
        console.print(Rule(f"[bold yellow]⚔️  Fitness Gauntlet — {len(battle)} Fighters[/]"))
        console.print()

        table = Table(border_style="yellow", show_lines=False, padding=(0, 1))
        table.add_column("#", style="bold dim", justify="center", width=3)
        table.add_column("Mutant", style="bold", max_width=40)
        table.add_column("Strategy", style="magenta", justify="center")
        table.add_column("Score", justify="right")
        table.add_column("Speed", justify="right")
        table.add_column("Memory", justify="right")
        table.add_column("Status", justify="center")

        for entry in battle:
            rank = entry["rank"]
            mid = entry["mutant_id"]
            # Shorten the mutant ID for display
            short_id = mid.split("::")[-1] if "::" in mid else mid
            strategy = entry.get("strategy", "?")
            score = entry["score"]
            speed = entry["speed_ms"]
            mem = entry["memory_bytes"]
            passed = entry["passed"]
            dq = entry["disqualified"]

            # Color the rank
            if rank == 1 and passed:
                rank_str = "[bold green]🥇[/]"
                score_str = f"[bold green]{score:.1f}[/]"
            elif rank == 2 and passed:
                rank_str = "[bold yellow]🥈[/]"
                score_str = f"[yellow]{score:.1f}[/]"
            elif rank == 3 and passed:
                rank_str = "[bold white]🥉[/]"
                score_str = f"[white]{score:.1f}[/]"
            elif passed:
                rank_str = f"[dim]{rank}[/]"
                score_str = f"[dim]{score:.1f}[/]"
            else:
                rank_str = f"[dim]{rank}[/]"
                score_str = f"[dim]{score:.1f}[/]"

            if dq:
                reason = entry.get("disqualify_reason", "Failed")
                status_str = f"[red]☠️  {reason[:20]}[/]"
            elif passed:
                status_str = "[green]✅ Passed[/]"
            else:
                status_str = "[red]❌ Failed[/]"

            speed_str = f"{speed:.4f}" if speed < float("inf") else "∞"
            mem_str = f"{mem:,}" if mem > 0 else "—"

            table.add_row(rank_str, short_id, strategy, score_str, speed_str, mem_str, status_str)

        console.print(table)


def _print_result(result: dict, applied: bool = False, verbose: bool = False):
    """Print single evolution result with optional battle arena."""
    from rich.table import Table


    status = result.get("status", "unknown")
    target = result.get("target", "?")
    short_target = target.split(":")[-1] if ":" in target else target

    # Show the battle arena if verbose or battle data exists
    if verbose and result.get("battle_results"):
        _print_battle_arena(result)

    if status == "evolved":
        improvements = result.get("improvements", {})
        delta = improvements.get("fitness_delta", 0)
        was_applied = result.get("applied", False)

        # ── Winner Announcement ──
        console.print()
        console.print(Rule(f"[bold green]🏆 Champion — {short_target}[/]"))
        console.print()

        if was_applied:
            tag = "[green]APPLIED TO SOURCE[/]"
        else:
            tag = "[cyan]SAVED TO SANDBOX[/]"

        console.print(f"  {tag}")
        console.print()

        if improvements:
            perf_table = Table(
                show_header=True, header_style="bold magenta", padding=(0, 2), border_style="green"
            )
            perf_table.add_column("Metric")
            perf_table.add_column("Before", justify="right")
            perf_table.add_column("After", justify="right")
            perf_table.add_column("Change", justify="right")

            # Fitness
            fb = improvements.get("fitness_before", 0)
            fa = improvements.get("fitness_after", 0)
            perf_table.add_row(
                "Fitness",
                f"{fb:.1f}",
                f"{fa:.1f}",
                f"[green]+{delta:.1f}[/]" if delta > 0 else f"[dim]{delta:.1f}[/]",
            )

            # Speed
            sb = improvements.get("speed_before", 0)
            sa = improvements.get("speed_after", 0)
            speed_delta = improvements.get("speed_change_ms", 0)
            speed_pct = (speed_delta / sb * 100) if sb > 0 else 0
            if speed_delta > 0:
                speed_label = f"[green]-{abs(speed_delta):.4f} ({speed_pct:.0f}% faster)[/]"
            elif speed_delta < 0:
                speed_label = f"[red]+{abs(speed_delta):.4f} ({abs(speed_pct):.0f}% slower)[/]"
            else:
                speed_label = "[dim]—[/]"
            perf_table.add_row("Speed (ms)", f"{sb:.4f}", f"{sa:.4f}", speed_label)

            # Memory
            mb = improvements.get("memory_before", 0)
            ma = improvements.get("memory_after", 0)
            mem_delta = improvements.get("memory_change_bytes", 0)
            if mem_delta > 0:
                mem_label = f"[green]-{abs(mem_delta):,} B[/]"
            elif mem_delta < 0:
                mem_label = f"[red]+{abs(mem_delta):,} B[/]"
            else:
                mem_label = "[dim]—[/]"
            perf_table.add_row("Memory", f"{mb:,} B", f"{ma:,} B", mem_label)

            # LOC
            loc_delta = improvements.get("loc_change", 0)
            if loc_delta != 0:
                loc_label = (
                    f"[green]-{abs(loc_delta)} lines[/]"
                    if loc_delta > 0
                    else f"[red]+{abs(loc_delta)} lines[/]"
                )
                perf_table.add_row("Lines of Code", "", "", loc_label)

            # Complexity
            cx_delta = improvements.get("complexity_change", 0)
            if cx_delta != 0:
                cx_label = (
                    f"[green]-{abs(cx_delta)}[/]" if cx_delta > 0 else f"[red]+{abs(cx_delta)}[/]"
                )
                perf_table.add_row("Complexity", "", "", cx_label)

            console.print(perf_table)

        # Show original vs evolved comparison if verbose
        if verbose and result.get("original_source") and result.get("evolved_source"):
            orig = result["original_source"]
            evol = result["evolved_source"]
            if orig.strip() != evol.strip():
                _print_diff(short_target, orig, evol)

        # Show sandbox path
        if not was_applied and result.get("sandbox_path"):
            console.print(f"    [dim]Sandbox: {result['sandbox_path']}[/]")

    elif status == "error":
        console.print(f"  [red]x[/] {short_target:<30} [red]Error: {result.get('reason', '?')}[/]")
    else:
        # Unchanged — still show the battle if verbose
        console.print()
        console.print(Rule(f"[bold dim]🛡️  No Evolution — {short_target}[/]"))
        console.print(f"  [dim]{result.get('reason', 'No mutant beat the original.')}[/]")


def _print_diff(name: str, original: str, evolved: str):
    """Show original vs evolved side-by-side."""
    console.print()
    console.print("    [bold]--- ORIGINAL ---[/]")
    console.print(
        Syntax(original.strip(), "python", theme="monokai", line_numbers=True, padding=(0, 2))
    )
    console.print("    [bold green]+++ EVOLVED +++[/]")
    console.print(
        Syntax(evolved.strip(), "python", theme="monokai", line_numbers=True, padding=(0, 2))
    )
    console.print()


def _print_summary(results: list[dict], applied: bool = False, verbose: bool = False):
    """Print a summary of all evolution results."""
    if not results:
        console.print("[dim]No functions to evolve.[/]")
        return

    evolved = sum(1 for r in results if r.get("status") == "evolved")
    unchanged = sum(1 for r in results if r.get("status") == "unchanged")
    errors = sum(1 for r in results if r.get("status") == "error")

    console.print()
    for r in results:
        _print_result(r, applied, verbose=verbose)

    console.print()
    console.print(Rule())

    mode = (
        "[green]APPLIED to source[/]" if applied else "[cyan]SANDBOX only[/] (original untouched)"
    )
    console.print(f"  Mode: {mode}")
    console.print(
        f"  Evolved: [green]{evolved}[/] | "
        f"Unchanged: [dim]{unchanged}[/] | "
        f"Errors: [red]{errors}[/]"
    )

    if not applied and evolved > 0:
        sandbox_paths = set()
        for r in results:
            if r.get("sandbox_path"):
                sandbox_paths.add(r["sandbox_path"])
        if sandbox_paths:
            console.print(f"  Sandbox: [cyan]{', '.join(sandbox_paths)}[/]")
        console.print("\n  [dim]Use --apply to deploy changes to the original files.[/]")

    console.print()





@main.command(name="dead-code", help="""
Scan the project for dead code (unused functions and classes) using graph reachability.

Example:
  hezgene dead-code
  hezgene dead-code --apply
""")
@click.option("--apply", is_flag=True, help="Automatically delete the dead code from source files")
@autonomous_options
def dead_code(apply, non_interactive, output, yes):
    """Scan the project for dead code."""
    from hezgene.analysis.dead_code import DeadCodeScanner
    
    console.print(Rule("[bold yellow]🔎 Scanning for Dead Code[/]"))
    try:
        scanner = DeadCodeScanner()
        findings = scanner.scan()
        
        if output == "json":
            data = [
                {
                    "file": f.file_path,
                    "line": f.line_number,
                    "entity": f.entity_name,
                    "reason": f.reason
                }
                for f in findings
            ]
            print_json_and_exit({"dead_code": data}, 0 if not findings else 1)
            
        if not findings:
            console.print("[bold green]✅ No dead code found! Your codebase is lean.[/]")
            return
            
        console.print(f"\n[bold red]Found {len(findings)} unused entities:[/]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("File")
        table.add_column("Line", justify="right")
        table.add_column("Entity")
        table.add_column("Reason")
        
        for f in findings:
            table.add_row(f.file_path, str(f.line_number), f.entity_name, f.reason)
            
        console.print(table)
        console.print("\n[dim]Note: Dynamically called code or framework entry points may be flagged as unused.[/]")
        
        if apply:
            console.print("\n[bold yellow]⚡ Applying fixes (deleting dead code)...[/]")
            deleted = scanner.apply_fixes(findings)
            console.print(f"[bold green]✅ Successfully deleted {deleted} unused entities![/]")
        else:
            console.print("\n[dim]Run with [bold]--apply[/] to automatically delete these entities.[/]")
            
        sys.exit(1 if not apply else 0)
        
    except Exception as e:
        if output == "json":
            print_json_and_exit({"error": str(e)}, 1)
        console.print(f"[bold red]❌ Error scanning for dead code: {e}[/]")
        sys.exit(1)


@main.command(name="dupes", help="""
Identify duplicated or structurally identical code.

This command parses the AST of your functions, normalizes variables and constants,
and detects functions that share the exact same structural topology.

Example:
  hezgene dupes
""")
@autonomous_options
def dupes(non_interactive, output, yes):
    """Identify duplicated code across the project."""
    from hezgene.analysis.duplication import DuplicationScanner
    
    console.print(Rule("[bold yellow]👯 Scanning for Duplicated Code[/]"))
    try:
        scanner = DuplicationScanner()
        findings = scanner.scan()
        
        if output == "json":
            data = [
                {
                    "hash_id": g.hash_id,
                    "count": len(g.functions),
                    "functions": g.functions
                }
                for g in findings
            ]
            print_json_and_exit({"duplicates": data}, 0)
            
        if not findings:
            console.print("[bold green]✅ No duplicated code found! Your abstractions are solid.[/]")
            return

        total_dupes = sum(len(g.functions) for g in findings)
        console.print(f"\n[bold red]Found {len(findings)} duplicate families ({total_dupes} total functions):[/]\n")
        
        for group in findings:
            console.print(f"  [bold cyan]Family {group.hash_id}[/] ({len(group.functions)} clones)")
            table = Table(show_header=True, header_style="bold magenta", padding=(0, 2))
            table.add_column("File")
            table.add_column("Line", justify="right")
            table.add_column("Function")
            table.add_column("Lines of Code", justify="right")
            
            for f in group.functions:
                table.add_row(f["file_path"], str(f["line"]), f["qualified_name"], str(f["loc"]))
            
            console.print(table)
            console.print()
            
    except Exception as e:
        if output == "json":
            print_json_and_exit({"error": str(e)}, 1)
        console.print(f"[bold red]❌ Error scanning for duplicates: {e}[/]")
        sys.exit(1)


@main.command(name="boundaries", help="""
Enforce architectural boundaries.

This command checks if modules in your project violate the import rules
defined in your .hezgene/config.json file.

Example:
  hezgene boundaries
""")
@autonomous_options
def boundaries(non_interactive, output, yes):
    """Enforce architectural boundary rules based on imports."""
    from hezgene.analysis.boundaries import BoundaryScanner
    from hezgene.core.config import HezGeneConfig
    
    console.print(Rule("[bold yellow]🧱 Scanning Architectural Boundaries[/]"))
    
    config = HezGeneConfig()
    bounds = config.get("boundaries", {})
    if not bounds.get("zones") or not bounds.get("rules"):
        console.print("[dim]No boundary rules configured in .hezgene/config.json.[/]")
        console.print("Add a 'boundaries' block to your config to enforce architecture rules.")
        if output == "json":
            print_json_and_exit({"boundaries": []}, 0)
        return
        
    try:
        scanner = BoundaryScanner(config=config)
        violations = scanner.scan()
        
        if output == "json":
            data = [
                {
                    "file": v.file_path,
                    "line": v.line_number,
                    "source_zone": v.source_zone,
                    "target_zone": v.target_zone,
                    "imported_module": v.imported_module
                }
                for v in violations
            ]
            print_json_and_exit({"violations": data}, 0 if not violations else 1)
            
        if not violations:
            console.print("[bold green]✅ No boundary violations found! Your architecture is pristine.[/]")
            return

        console.print(f"\n[bold red]Found {len(violations)} boundary violations:[/]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("File")
        table.add_column("Line", justify="right")
        table.add_column("Imported Module")
        table.add_column("Violation")
        
        for v in violations:
            violation_str = f"[red]{v.source_zone}[/] -> [red]{v.target_zone}[/]"
            table.add_row(v.file_path, str(v.line_number), v.imported_module, violation_str)
            
        console.print(table)
        sys.exit(1)
        
    except Exception as e:
        if output == "json":
            print_json_and_exit({"error": str(e)}, 1)
        console.print(f"[bold red]❌ Error scanning boundaries: {e}[/]")
        sys.exit(1)


@main.command(name="trace", context_settings={"ignore_unknown_options": True}, help="""
Run a python script under the HezGene Runtime Tracer.

This will monitor function execution and update the call_count in the
FunctionDNA registry. This data is used to identify hot paths.

Example:
  hezgene trace my_script.py --arg1 --arg2
""")
@click.argument("script", required=True)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def trace(script, args):
    """Run a script under the HezGene tracer."""
    import sys
    from pathlib import Path
    from hezgene.analysis.runtime_tracer import RuntimeTracer

    script_path = Path(script)
    if not script_path.exists():
        console.print(f"[bold red]❌ Script not found: {script}[/]")
        sys.exit(1)

    console.print(Rule(f"[bold yellow]🔥 Tracing Hot Paths: {script}[/]"))
    
    # Initialize and start tracer
    tracer = RuntimeTracer()
    tracer.start()

    # Rewrite sys.argv for the target script
    sys.argv = [script] + list(args)

    # Execute the script in the __main__ namespace
    import runpy
    try:
        runpy.run_path(str(script_path), run_name="__main__")
    except SystemExit as e:
        # Stop tracing explicitly before exiting so we save the data
        tracer.stop_and_save()
        sys.exit(e.code)
    except Exception as e:
        tracer.stop_and_save()
        console.print(f"\n[bold red]Script exited with error: {e}[/]")
        sys.exit(1)
        
    # Normal exit will trigger atexit hook to save data, but we can do it explicitly
    tracer.stop_and_save()


@main.command(name="health", help="""
Generate a Project Health Score and identify refactoring targets.

This command aggregates complexity, maintainability, dead code, and duplication
into a single 0-100 score, similar to Fallow.

Example:
  hezgene health
""")
@autonomous_options
def health(non_interactive, output, yes):
    """Generate a 0-100 Project Health Score."""
    from hezgene.analysis.health_score import HealthScanner
    
    console.print(Rule("[bold yellow]🏥 Calculating Project Health Score[/]"))
    try:
        scanner = HealthScanner()
        report = scanner.scan()
        
        if output == "json":
            import dataclasses
            print_json_and_exit(dataclasses.asdict(report), 0)
            
        color = "green" if report.score >= 80 else ("yellow" if report.score >= 60 else "red")
        
        console.print(f"\n  [bold]Overall Score:[/] [{color} bold]{report.score}/100[/] (Grade: {report.grade})")
        console.print(f"  [dim]Functions Analyzed:[/] {report.total_functions}")
        console.print(f"  [dim]Dead Code Entities:[/] {report.dead_code_count}")
        console.print(f"  [dim]Duplicate Families:[/] {report.duplicate_groups}")
        console.print(f"  [dim]Average Complexity:[/] {report.avg_complexity}")
        console.print(f"  [dim]Avg Maintainability:[/] {report.avg_maintainability}\n")
        
        if report.refactor_targets:
            console.print("[bold red]Top Refactoring Targets:[/]")
            table = Table(show_header=True, header_style="bold magenta", padding=(0, 2))
            table.add_column("Function")
            table.add_column("Complexity", justify="right")
            table.add_column("Maintainability", justify="right")
            table.add_column("Reason")
            
            for t in report.refactor_targets:
                table.add_row(t.qualified_name, str(t.complexity), f"{t.maintainability_index:.1f}", t.reason)
            
            console.print(table)
            
    except Exception as e:
        if output == "json":
            print_json_and_exit({"error": str(e)}, 1)
        console.print(f"[bold red]❌ Error calculating health score: {e}[/]")
        sys.exit(1)


@main.command(name="audit", help="""
Unified Codebase Intelligence Audit.

Runs a master suite of checks across your project (dead code, dependencies,
duplication, boundaries, and health score). Optionally applies auto-fixes.

Example:
  hezgene audit
  hezgene audit --apply
  hezgene audit --no-dupes --only deps
""")
@click.option("--apply", is_flag=True, help="Automatically fix all fixable issues (dead code, unused deps)")
@click.option("--min-score", default=70, type=int, help="Fail if health score is below this threshold")
@click.option("--base", default=None, type=str, help="Base branch for git-aware health scoping")
@click.option("--full-project", is_flag=True, help="Audit the entire project instead of scoping to changed files")
@autonomous_options
def audit(apply, min_score, base, full_project, non_interactive, output, yes):
    """Unified master audit for codebase intelligence."""
    from hezgene.analysis.health_score import HealthScanner
    from hezgene.analysis.dead_code import DeadCodeScanner
    from hezgene.analysis.dependency_hygiene import DependencyScanner
    import dataclasses
    
    # ── Collect all audit data into a structured dict ──────────────
    audit_data = {
        "status": "pass",
        "health_score": 0,
        "health_grade": "?",
        "min_score_threshold": min_score,
        "scope": "Full Project",
        "dependencies": {"unused": 0, "missing": 0, "details": [], "error": None},
        "dead_code": {"count": 0, "details": [], "error": None},
        "refactor_targets": [],
    }

    issues_found = False

    # 1. Dependency Hygiene
    try:
        dep_scanner = DependencyScanner()
        issues = dep_scanner.scan()
        if issues:
            issues_found = True
            unused = sum(1 for i in issues if i.issue_type == "unused")
            missing_count = sum(1 for i in issues if i.issue_type == "missing")
            audit_data["dependencies"]["unused"] = unused
            audit_data["dependencies"]["missing"] = missing_count
            audit_data["dependencies"]["details"] = [
                {"package": i.package_name, "issue": i.issue_type, "reason": getattr(i, "reason", "")}
                for i in issues
            ]
            if apply and unused > 0:
                deleted = dep_scanner.apply_fixes(issues)
                audit_data["dependencies"]["fixed"] = deleted
    except Exception as e:
        audit_data["dependencies"]["error"] = str(e)

    # 2. Dead Code
    try:
        dead_scanner = DeadCodeScanner()
        dead_findings = dead_scanner.scan()
        if dead_findings:
            issues_found = True
            audit_data["dead_code"]["count"] = len(dead_findings)
            audit_data["dead_code"]["details"] = [
                {"entity": f.entity_name, "file": f.file_path, "line": f.line_number}
                for f in dead_findings
            ]
            if apply:
                deleted = dead_scanner.apply_fixes(dead_findings)
                audit_data["dead_code"]["fixed"] = deleted
    except Exception as e:
        audit_data["dead_code"]["error"] = str(e)

    # 3. Overall Health Score (Git-aware)
    try:
        changed_files = None
        scope_label = "Full Project"
        if not full_project:
            try:
                import git
                repo = git.Repo(".", search_parent_directories=True)
                if base is None:
                    for c in ["main", "master", "develop"]:
                        if c in [ref.name for ref in repo.refs]: base = c; break
                if base and base in [ref.name for ref in repo.refs]:
                    changed_files = list(set([d.a_path for d in repo.head.commit.diff(base) if d.a_path.endswith(".py")] + [d.b_path for d in repo.head.commit.diff(base) if d.b_path.endswith(".py")]))
                    scope_label = f"PR Delta vs {base}"
            except Exception: pass
            
        health_scanner = HealthScanner()
        report = health_scanner.scan(changed_files=changed_files)
        
        audit_data["health_score"] = report.score
        audit_data["health_grade"] = report.grade
        audit_data["scope"] = scope_label
        audit_data["refactor_targets"] = [
            {"function": t.qualified_name, "complexity": t.complexity,
             "maintainability": t.maintainability_index, "reason": t.reason}
            for t in report.refactor_targets
        ]

        if report.score < min_score:
            audit_data["status"] = "fail"
        elif issues_found and not apply:
            audit_data["status"] = "warn"
        else:
            audit_data["status"] = "pass"

    except Exception as e:
        audit_data["status"] = "error"
        audit_data["error"] = str(e)

    # ── JSON output path ──────────────────────────────────────────
    if output == "json":
        exit_code = 1 if audit_data["status"] == "fail" else 0
        print_json_and_exit(audit_data, exit_code)

    # ── Rich text output (original behavior) ──────────────────────
    console.print(Rule("[bold yellow]📋 Master Project Audit[/]"))

    # Dependencies
    dep = audit_data["dependencies"]
    if dep.get("error"):
        console.print(f"[bold red]📦 Dependencies:[/] Error: {dep['error']}")
    elif dep["unused"] or dep["missing"]:
        console.print(f"\n[bold red]📦 Dependencies:[/] Found {dep['unused']} unused, {dep['missing']} missing.")
        for i in dep["details"][:5]:
            console.print(f"  - [cyan]{i['package']}[/] ({i['issue']})")
        if len(dep["details"]) > 5: console.print(f"  ...and {len(dep['details'])-5} more.")
        if dep.get("fixed"):
            console.print(f"  [bold green]⚡ Fixed:[/] Removed {dep['fixed']} unused dependencies.")
    else:
        console.print("[bold green]📦 Dependencies:[/] Perfect hygiene.")

    # Dead Code
    dc = audit_data["dead_code"]
    if dc.get("error"):
        console.print(f"[bold red]🔎 Dead Code:[/] Error: {dc['error']}")
    elif dc["count"]:
        console.print(f"\n[bold red]🔎 Dead Code:[/] Found {dc['count']} unreachable entities.")
        for f in dc["details"][:5]:
            console.print(f"  - [cyan]{f['entity']}[/] in {f['file']}:{f['line']}")
        if dc["count"] > 5: console.print(f"  ...and {dc['count']-5} more.")
        if dc.get("fixed"):
            console.print(f"  [bold green]⚡ Fixed:[/] Deleted {dc['fixed']} unreachable entities.")
    else:
        console.print("[bold green]🔎 Dead Code:[/] Zero unreachable entities.")

    # Health Score
    score = audit_data["health_score"]
    color = "green" if score >= min_score else "red"
    console.print(f"\n[bold {color}]🏥 Health Score:[/] {score}/100 ({audit_data['scope']})")

    if audit_data["status"] == "fail":
        console.print(f"\n[bold red]❌ Audit Failed![/] Health below threshold ({min_score}).")
        sys.exit(1)
    elif audit_data["status"] == "warn":
        console.print(f"\n[bold yellow]⚠️ Audit Passed with Warnings![/] Score is ok, but issues exist. Run with [bold]--apply[/] to fix them.")
        sys.exit(0)
    elif audit_data["status"] == "error":
        console.print(f"\n[bold red]❌ Audit Error:[/] {audit_data.get('error', 'Unknown')}")
        sys.exit(1)
    else:
        console.print(f"\n[bold green]✅ Audit Passed Perfectly![/]")
        sys.exit(0)

@main.command(name="deps", help="""
Analyze dependency hygiene.

Scans the project for unused dependencies (listed in requirements but never imported)
and missing dependencies (imported but not listed in requirements).

Example:
  hezgene deps
  hezgene deps --apply
""")
@click.option("--apply", is_flag=True, help="Automatically remove unused dependencies from requirements.txt")
@autonomous_options
def deps(apply, non_interactive, output, yes):
    """Scan the project for dependency hygiene issues."""
    from hezgene.analysis.dependency_hygiene import DependencyScanner
    
    console.print(Rule("[bold yellow]📦 Scanning Dependency Hygiene[/]"))
    try:
        scanner = DependencyScanner()
        issues = scanner.scan()
        
        if output == "json":
            data = [
                {
                    "package": i.package_name,
                    "type": i.issue_type,
                    "reason": i.reason
                }
                for i in issues
            ]
            print_json_and_exit({"hygiene_issues": data}, 0 if not issues else 1)
            
        if not issues:
            console.print("[bold green]✅ No dependency hygiene issues found! Your requirements are perfectly synced.[/]")
            return

        unused = sum(1 for i in issues if i.issue_type == "unused")
        missing = sum(1 for i in issues if i.issue_type == "missing")
        
        console.print(f"\n[bold red]Found {len(issues)} dependency issues[/] ({unused} unused, {missing} missing):\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Package")
        table.add_column("Issue")
        table.add_column("Details")
        
        for i in issues:
            issue_str = f"[yellow]{i.issue_type}[/]" if i.issue_type == "unused" else f"[red]{i.issue_type}[/]"
            table.add_row(f"[bold]{i.package_name}[/]", issue_str, i.reason)
            
        console.print(table)
        
        if apply and unused > 0:
            console.print("\n[bold yellow]⚡ Applying fixes (removing unused dependencies)...[/]")
            deleted = scanner.apply_fixes(issues)
            console.print(f"[bold green]✅ Successfully removed {deleted} unused dependencies from requirements.txt![/]")
            if missing > 0:
                console.print(f"[dim]Note: {missing} missing dependencies could not be auto-fixed. Please pip install them manually.[/]")
        elif unused > 0:
            console.print("\n[dim]Run with [bold]--apply[/] to automatically remove unused dependencies from requirements.txt.[/]")
            
        sys.exit(1 if not apply else 0)
        
    except Exception as e:
        if output == "json":
            print_json_and_exit({"error": str(e)}, 1)
        console.print(f"[bold red]❌ Error scanning dependencies: {e}[/]")
        sys.exit(1)


@main.command(name="mcp", help="""
Start the HezGene Model Context Protocol (MCP) Server.

This allows AI agents (like Claude, Cursor, Windsurf) to natively query
the codebase intelligence using standard JSON-RPC over stdio.

Example:
  hezgene mcp
""")
def mcp():
    """Start the HezGene MCP Server."""
    from hezgene.mcp_server import MCPServer
    
    server = MCPServer()
    # MCP servers must only output JSON-RPC to stdout.
    # Any other print statements will break the protocol.
    server.serve()


@main.command(name="ci", help="""
Set up CI/CD integration for automated code evolution.

Automatically evolve your code on every pull request.
HezGene reviews your code and suggests improvements.

Supports GitHub Actions and GitLab CI.

Example:
  hezgene ci setup --github
  hezgene ci setup --gitlab
""")
@click.option("--github", "use_github", is_flag=True, help="Set up GitHub Actions")
@click.option("--gitlab", "use_gitlab", is_flag=True, help="Set up GitLab CI")
def ci(use_github, use_gitlab):
    """Set up CI/CD integration."""
    try:
        if use_github:
            from hezgene.ci_cd.github_actions import GitHubActionsIntegration
            gh = GitHubActionsIntegration()
            path = gh.setup()
            console.print(f"[bold green]✅ GitHub Actions workflow created at {path}[/]")
        elif use_gitlab:
            from hezgene.ci_cd.gitlab_ci import GitLabCIIntegration
            gl = GitLabCIIntegration()
            path = gl.setup()
            console.print(f"[bold green]✅ GitLab CI pipeline created at {path}[/]")
        else:
            console.print("[yellow]Specify --github or --gitlab[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to set up CI/CD: {e}[/]")


@main.command(name="ui", help="""
Alias for 'hezgene web'. Launches the Battle Arena Web Dashboard.

Example:
  hezgene ui
""")
@click.option("--host", default="127.0.0.1", show_default=True, help="Host to bind the server")
@click.option("--port", default=8000, show_default=True, type=int, help="Port to bind the server")
@autonomous_options
def ui(host, port, non_interactive, output, yes):
    """Alias for the web dashboard."""
    from hezgene.web.launcher import launch_dashboard

    launch_dashboard(host=host, port=port)


# ═══════════════════════════════════════════════════════════════════
# GUARD — Auto-Revert Health Guard
# ═══════════════════════════════════════════════════════════════════

@main.group(name="guard", help="""
Health Guard — Auto-revert safety net for AI-driven code evolution.

Monitors your project's health score across changes. If the score drops
by more than a configurable threshold, the guard can auto-revert the
commit and fire a webhook to alert your team.

Usage:
  hezgene guard snapshot          # Save current score as baseline
  hezgene guard check             # Compare current vs baseline
  hezgene guard check --auto-revert --threshold 10
  hezgene guard check --webhook https://hooks.slack.com/...
  hezgene guard install           # Install as git pre-push hook
""")
def guard():
    """Health Guard — safety net for AI-driven code changes."""
    pass


@guard.command(name="snapshot", help="""
Save the current health score as the baseline for future comparisons.

This creates/overwrites `.hezgene/guard_baseline.json`. Run this before
making changes so the guard knows what "healthy" looks like.

Example:
  hezgene guard snapshot
  hezgene guard snapshot --output json
""")
@autonomous_options
def guard_snapshot(non_interactive, output, yes):
    """Snapshot the current health score as baseline."""
    from hezgene.guard import HealthGuard

    g = HealthGuard(".")
    baseline = g.snapshot()

    if output == "json":
        print_json_and_exit({"status": "success", "baseline": baseline}, 0)

    console.print(Rule("[bold yellow]🛡️ Health Guard — Baseline Snapshot[/]"))
    color = "green" if baseline["score"] >= 80 else ("yellow" if baseline["score"] >= 60 else "red")
    console.print(f"\n  [bold]Score:[/] [{color} bold]{baseline['score']}/100[/] (Grade: {baseline['grade']})")
    console.print(f"  [dim]Functions:[/] {baseline['total_functions']}")
    console.print(f"  [dim]Dead Code:[/] {baseline['dead_code_count']}")
    console.print(f"  [dim]Duplicates:[/] {baseline['duplicate_groups']}")
    console.print(f"\n  [bold green]✅ Baseline saved to .hezgene/guard_baseline.json[/]")


@guard.command(name="check", help="""
Compare the current health score against the stored baseline.

If the score has dropped by more than --threshold points, the check fails.
Optionally auto-reverts the last commit or fires a webhook.

Example:
  hezgene guard check
  hezgene guard check --threshold 5
  hezgene guard check --auto-revert
  hezgene guard check --webhook https://hooks.slack.com/services/...
""")
@click.option("--threshold", default=10, type=int, show_default=True, help="Maximum allowed score drop before failing")
@click.option("--auto-revert", is_flag=True, help="Automatically `git revert HEAD` if the score drops")
@click.option("--webhook", default=None, type=str, help="URL to POST a JSON alert on failure")
@autonomous_options
def guard_check(threshold, auto_revert, webhook, non_interactive, output, yes):
    """Check health against baseline and react to regressions."""
    from hezgene.guard import HealthGuard
    from dataclasses import asdict

    g = HealthGuard(".")
    result = g.check(threshold=threshold, auto_revert=auto_revert, webhook_url=webhook)

    if output == "json":
        exit_code = 1 if result.status == "fail" else 0
        print_json_and_exit(asdict(result), exit_code)

    console.print(Rule("[bold yellow]🛡️ Health Guard — Check[/]"))

    if result.status == "no_baseline":
        console.print("\n  [bold yellow]⚠️ No baseline found.[/] Run [bold]hezgene guard snapshot[/] first.")
        return

    # Score comparison
    delta_str = f"+{result.delta}" if result.delta >= 0 else str(result.delta)
    b_color = "green" if result.baseline_score >= 80 else ("yellow" if result.baseline_score >= 60 else "red")
    c_color = "green" if result.current_score >= 80 else ("yellow" if result.current_score >= 60 else "red")

    console.print(f"\n  [dim]Baseline:[/] [{b_color}]{result.baseline_score}/100[/] ({result.baseline_grade})")
    console.print(f"  [dim]Current: [/] [{c_color}]{result.current_score}/100[/] ({result.current_grade})")
    console.print(f"  [dim]Delta:   [/] {delta_str} points (threshold: ±{result.threshold})")

    if result.status == "fail":
        console.print(f"\n  [bold red]❌ GUARD FAILED:[/] {result.message}")
        if result.auto_reverted:
            console.print("  [bold green]↩️ Auto-reverted HEAD commit.[/]")
        if result.webhook_fired:
            console.print("  [dim]📡 Webhook fired.[/]")
        sys.exit(1)
    else:
        console.print(f"\n  [bold green]✅ GUARD PASSED:[/] {result.message}")


@guard.command(name="install", help="""
Install the Health Guard as a git pre-push hook.

After installing, every `git push` will automatically check the health score
against the baseline. If it regresses beyond the threshold, the push is blocked.

Example:
  hezgene guard install
""")
@autonomous_options
def guard_install(non_interactive, output, yes):
    """Install the guard as a git pre-push hook."""
    from hezgene.guard import HealthGuard

    g = HealthGuard(".")
    try:
        hook_path = g.install_hook("pre-push")
        if output == "json":
            print_json_and_exit({"status": "success", "hook_path": hook_path}, 0)
        console.print(Rule("[bold yellow]🛡️ Health Guard — Install Hook[/]"))
        console.print(f"\n  [bold green]✅ Pre-push hook installed at:[/] {hook_path}")
        console.print("  [dim]Every `git push` will now check the health score against the baseline.[/]")
        console.print("  [dim]Use `git push --no-verify` to bypass if needed.[/]")
    except Exception as e:
        if output == "json":
            print_json_and_exit({"status": "error", "error": str(e)}, 1)
        console.print(f"[bold red]❌ Failed to install hook: {e}[/]")


if __name__ == "__main__":
    main()
