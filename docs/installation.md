# Installation

HezGene is built purely in Python and supports Windows, macOS, and Linux.

## Requirements

- **Python 3.9+**
- Basic dependencies: `click`, `rich` (installed automatically)

## Install from PyPI (Recommended)

To install the latest stable release of HezGene globally or in your virtual environment:

```bash
python -m pip install hezgene
```

## Install from GitHub (Latest Bleeding-Edge)

If you want the absolute latest features that haven't been published to PyPI yet, you can install directly from the main branch:

```bash
python -m pip install git+https://github.com/TechVenom/HezGene.git
```

## Development Installation (From Source)

If you plan to contribute to HezGene or modify its internal mutation strategies, clone the repository and install it in editable mode:

```bash
git clone https://github.com/TechVenom/HezGene.git
cd HezGene
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install in editable mode
python -m pip install -e .
```

## Verifying the Installation

To confirm HezGene is installed and accessible in your path, run:

```bash
hezgene --version
```

*Expected Output:*
```text
hezgene, version 1.0.0
```

### Interpreter mismatch troubleshooting

If `hezgene --version` works but `python -c "import hezgene"` fails, you're likely using
two different Python interpreters (e.g., system Python vs a project venv).

Use these commands to ensure everything runs in the same interpreter:

```bash
python -m pip show hezgene
python -c "from hezgene import EvolutionEngine; print(EvolutionEngine)"
python -m hezgene --version
```

You can also view the full help menu:
```bash
hezgene --help
```
