"""
🧬 HezGene — The DNA of Software
Autonomous genetic software evolution platform.

Every function has genes. We make them evolve.
— Hezron Paipai
"""

try:
    # Prefer the installed package metadata when available.
    from importlib.metadata import PackageNotFoundError, version

    __version__ = version("hezgene")
except Exception:
    # Fallback for source checkouts / environments without metadata.
    __version__ = "1.0.0"
__author__ = "Hezron Paipai"
__license__ = "MIT"

from .analysis.file_ingestor import FileIngestor
from .analysis.project_scanner import ProjectScanner
from .core.dna_tracker import DNATracker, FunctionDNA
from .deployment.deployer import AutoDeployer
from .evaluation.gauntlet import FitnessGauntlet
from .evaluation.tournament import TournamentManager
from .mutation.ast_mutator import MutationEngine

__all__ = [
    "EvolutionEngine",
    "DNATracker",
    "FunctionDNA",
    "MutationEngine",
    "FitnessGauntlet",
    "TournamentManager",
    "AutoDeployer",
    "ProjectScanner",
    "FileIngestor",
]


from .engine import EvolutionEngine
