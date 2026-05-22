"""
🧬 HezGene — The DNA of Software
Autonomous genetic software evolution platform.

Every function has genes. We make them evolve.
— Hezron Paipai
"""

__version__ = "0.1.0"
__author__ = "Hezron Paipai"

from hezgene.analysis.file_ingestor import FileIngestor
from hezgene.analysis.project_scanner import ProjectScanner
from hezgene.core.dna_tracker import DNATracker, FunctionDNA
from hezgene.deployment.deployer import AutoDeployer
from hezgene.evaluation.gauntlet import FitnessGauntlet
from hezgene.evaluation.tournament import TournamentManager
from hezgene.mutation.ast_mutator import MutationEngine

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


from hezgene.core.engine import EvolutionEngine
