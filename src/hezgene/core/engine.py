"""
Backward-compat shim.

The public package is a single unified `hezgene` distribution. The engine lives at
`hezgene.engine:EvolutionEngine`.
"""

from ..engine import EvolutionEngine

__all__ = ["EvolutionEngine"]
