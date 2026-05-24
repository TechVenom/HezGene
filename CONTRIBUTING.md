# Contributing to HezGene

Thank you for your interest in contributing to HezGene! 🧬

## Getting Started

1. **Fork the repository** and clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/hezgene.git
   cd hezgene
   ```

2. **Create a virtual environment** and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. **Initialize HezGene** in the project directory:
   ```bash
   hezgene init
   ```

## Development Workflow

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and ensure they pass linting:
   ```bash
   ruff check .
   ```

3. Run the test suite:
   ```bash
   pytest
   ```

4. Commit your changes with clear messages:
   ```bash
   git commit -m "feat: add new mutation strategy for loop unrolling"
   ```

## Code Style

- We use **ruff** for linting (configured in `pyproject.toml`).
- We use **black** for formatting with a line length of 100.
- All functions should have **type hints** and **docstrings**.
- Follow **PEP 8** conventions.

## Project Structure

```
src/hezgene/
├── analysis/          # Code analysis (file ingestion, complexity, dependencies)
├── core/              # Core engine (DNA tracker, evolution engine, config)
├── mutation/          # Mutation strategies (AST-based)
├── evaluation/        # Fitness evaluation (gauntlet, tournament)
└── deployment/        # Auto-deployment and rollback
```

## What Can You Contribute?

### 🟢 Welcomed Contributions

- **New AST mutation strategies** — Add to `src/hezgene/mutation/ast_mutator.py`
- **Fitness gauntlet improvements** — Better benchmarking and evaluation
- **Bug fixes and stability** — Help us squash bugs
- **Documentation** — Improve docs, examples, and tutorials
- **Test coverage** — Add unit tests and integration tests
- **Performance** — Make HezGene faster and more memory efficient

### 🟡 Discuss First

- **Major architectural changes** — Open an issue to discuss before starting
- **New CLI commands** — Propose via issue so we can agree on UX
- **Dependency additions** — We aim to keep the core lightweight

## Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation only
- `refactor:` — Code refactoring (no feature change)
- `test:` — Adding or updating tests
- `chore:` — Build process or tooling changes

## Code of Conduct

Be respectful, constructive, and supportive. We're all here to make
software evolve. 🧬

## License

By contributing, you agree that your contributions will be licensed under the MIT License, the same as the rest of the project.
