# Installation

HezGene is built purely in Python and supports Windows, macOS, and Linux.

## Requirements

- **Python 3.9+**
- Basic dependencies: `click`, `rich` (installed automatically)

## Install from PyPI (Recommended)

To install the latest stable release of HezGene globally or in your virtual environment:

```bash
pip install hezgene
```

## Install from GitHub (Latest Bleeding-Edge)

If you want the absolute latest features that haven't been published to PyPI yet, you can install directly from the main branch:

```bash
pip install git+https://github.com/your-org/hezgene.git
```

## Development Installation (From Source)

If you plan to contribute to HezGene or modify its internal mutation strategies, clone the repository and install it in editable mode:

```bash
git clone https://github.com/your-org/hezgene.git
cd hezgene
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install in editable mode
pip install -e .
```

## Verifying the Installation

To confirm HezGene is installed and accessible in your path, run:

```bash
hezgene --version
```

*Expected Output:*
```text
hezgene, version 0.1.0
```

You can also view the full help menu:
```bash
hezgene --help
```
