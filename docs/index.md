# Welcome to HezGene

**HezGene** is the world's first autonomous genetic software evolution and static analysis platform. Instead of relying on manual refactoring, HezGene treats your functions like living organisms. It extracts their deep structural "DNA," spawns mutant variants, pits them against each other in an empirical fitness gauntlet, and seamlessly deploys the fittest survivor back into your codebase.

Your code gets faster, cleaner, mathematically sound, and rigorously analyzed—completely automatically.

## Quick Example

```bash
# Evolve all functions in your utils.py file
hezgene run src/utils.py

# Profile the deep software engineering metrics of a function
hezgene dna src/utils.py:process_data

# Automatically find and optimize the slowest function in your project
hezgene run --target slowest
```

## Documentation Map

- 🚀 [Getting Started](getting-started.md) — From zero to evolved code in 5 minutes.
- 📦 [Installation](installation.md) — How to install HezGene on any system.
- 📖 [Usage Guide](usage.md) — Comprehensive guide to profiling, ranking, and evolving your code.
- 💻 [CLI Reference](commands.md) — Detailed command-line reference.
- 🧠 [How It Works](how-it-works.md) — The architecture, Big O scaling tests, and science behind the evolution.
- 🌟 [Real-World Examples](examples.md) — See HezGene optimize real code.
- ❓ [FAQ](faq.md) — Answers to your most common questions.
- 🐍 [Python API](api-reference.md) — How to use HezGene's analysis and evolution engines programmatically.
