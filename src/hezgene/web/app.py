from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from hezgene.core.dna_tracker import DNATracker

app = FastAPI(title="HezGene Web", description="Battle Arena UI")

# Setup paths
WEB_DIR = Path(__file__).parent
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"

# Create directories if they don't exist
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Load DNA Tracker
tracker = DNATracker()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main dashboard."""
    dna_entries = []
    for target in tracker.get_all_tracked():
        dna = tracker.get_dna(target)
        if dna:
            dna_entries.append(dna.to_dict())

    # Sort by fitness score descending
    dna_entries.sort(key=lambda x: x.get("fitness_score", 0), reverse=True)

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "dna_entries": dna_entries, "total_tracked": len(dna_entries)},
    )


@app.get("/api/dna")
async def get_dna():
    """API endpoint to get all tracked DNA data."""
    dna_entries = []
    for target in tracker.get_all_tracked():
        dna = tracker.get_dna(target)
        if dna:
            dna_entries.append(dna.to_dict())
    return {"status": "success", "data": dna_entries}


def start_server(host="127.0.0.1", port=8000):
    """Start the FastAPI server."""
    print(f"🚀 Starting HezGene Web Interface at http://{host}:{port}")
    uvicorn.run("hezgene.web.app:app", host=host, port=port, reload=False)
