"""
Allow `python -m hezgene ...` to behave like the `hezgene` console script.

This helps users and CI verification scripts ensure they are using the intended
Python interpreter (venv vs system Python).
"""

from __future__ import annotations

from hezgene.cli import main

if __name__ == "__main__":
    main()

