# 🧬 Hezgene-Core

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![Build Status](https://github.com/TechVenom/Hezgene-Core/actions/workflows/test.yml/badge.svg)

**Hezgene-Core** is an autonomous genetic software evolution engine. It treats your Python functions like DNA, applying AST (Abstract Syntax Tree) mutations to breed faster, more efficient, and more readable variations of your code. Mutants are tested in a rigorous Fitness Gauntlet, and only the mathematically superior code survives.

This is the free, fully functional, MIT-licensed core engine.

---

## ⚡ Quick Start

### Installation

```bash
pip install hezgene-core
```

### 5 Commands to Evolve Your Code

1. **Initialize** the evolutionary environment in your project:
   ```bash
   hezgene init
   ```
2. **Scan** a file to establish baseline DNA performance:
   ```bash
   hezgene dna src/utils.py
   ```
3. **Evolve** a specific function (results go to a safe sandbox):
   ```bash
   hezgene run src/utils.py:process_data --verbose
   ```
4. **Verify** that the mutant behaves identically to the original:
   ```bash
   hezgene verify src/utils.py:process_data
   ```
5. **Apply** the winning evolution directly to your source file:
   ```bash
   hezgene run src/utils.py:process_data --apply
   ```

---

## 🛠️ Free Core Features

The `hezgene-core` package gives you a powerful evolutionary framework:
- **AST Mutation Engine**: 6 built-in semantic mutation strategies (Loop Unrolling, Comprehension Compression, Early Exits, etc.).
- **Fitness Gauntlet**: Strict 5-ring correctness testing using standard library fuzzing.
- **DNA Tracker**: Halstead complexity and runtime performance profiling.
- **Tournament Manager**: Automated rank-and-replace for mutants.
- **Safe Sandbox**: Evolutions happen safely inside `.hezgene/sandbox/`.

---

## 🚀 HezGene Enterprise

Want to take evolution to the next level? **HezGene Enterprise** integrates seamlessly with the core engine to provide premium features for professional teams.

- **🤖 LLM Mutations**: Unlock intelligent, semantic mutations using GPT-4, Claude, Gemini, or local models via Ollama.
- **🖥️ Battle Arena UI**: A gorgeous real-time web dashboard to watch your code evolve.
- **♾️ CI/CD Integration**: Automatically evolve code on every Pull Request via GitHub Actions or GitLab CI.
- **👥 Team Management**: Shared evolution configs and license pools.

**[Upgrade to HezGene Enterprise](https://hezgene.ai/pricing)**

---

## 🤝 Contributing

We welcome community contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to set up the dev environment, write tests, and submit PRs for new AST mutation strategies.

### Development Setup
```bash
git clone https://github.com/TechVenom/Hezgene-Core.git
cd Hezgene-Core
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## 📄 License

MIT License. See the `LICENSE` file for more details.
