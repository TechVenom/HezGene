import os
import sys
from pathlib import Path
from rich.console import Console

console = Console()

def launch_dashboard():
    """Launch the HezGene Web Dashboard using the robust production server."""
    pkg_root = Path(__file__).parent.parent.parent.parent
    frontend_dir = pkg_root / "frontend"
    frontend_dist = frontend_dir / "dist"
    
    # Ensure the backend knows where the user originally launched from
    os.environ["HEZGENE_PROJECT_ROOT"] = str(Path.cwd().resolve())
    
    if not frontend_dist.exists():
        console.print("[yellow]Frontend build not found. Compiling now...[/]")
        import subprocess
        try:
            subprocess.run("npm install && npm run build", shell=True, cwd=str(frontend_dir), check=True)
            console.print("[green]Frontend built successfully![/]")
        except Exception as e:
            console.print(f"[bold red]Failed to build frontend: {e}[/]")
            return

    console.print("[bold cyan]Starting robust HezGene Server on port 8000...[/]")
    
    # Auto-restart loop to keep the web app alive if it crashes (OOM, unhandled exception, etc.)
    import time
    import subprocess
    import sys
    
    while True:
        try:
            # We spawn it in a subprocess so we can catch crashes.
            # If we just called start_server(), a hard crash would kill this launcher too.
            process = subprocess.Popen(
                [sys.executable, "-c", "from hezgene.web.api import start_server; start_server(host='127.0.0.1', port=8000)"],
                env=os.environ
            )
            process.wait()
            
            # If we get here, the server stopped.
            if process.returncode != 0:
                console.print(f"[bold red]Web server terminated unexpectedly (Exit code: {process.returncode}). Restarting in 3 seconds...[/]")
                time.sleep(3)
            else:
                # Clean exit
                break
        except KeyboardInterrupt:
            console.print("[yellow]Server stopped by user.[/]")
            break
        except Exception as e:
            console.print(f"[bold red]Process manager error: {e}. Restarting...[/]")
            time.sleep(3)
