# How to Use HezGene

HezGene operates as a comprehensive static analysis and dynamic evolution platform. This guide covers how to analyze your codebase, view advanced software engineering metrics, and trigger autonomous evolution.

## Initialization

Before evolving a project, you must initialize it. This creates the `.hezgene` directory which houses the persistent DNA registry and the Sandbox environment.

```bash
hezgene init
```

## Scanning and Profiling

Want to see what HezGene *can* evolve without actually running a mutation cycle? Use the `scan` command to parse the Abstract Syntax Trees (AST) of your project.

```bash
hezgene scan src/database.py
```

*Expected Output:*
```text
  Found: 12 functions/methods
  Evolvable:
    > DBManager.connect            (line 15, 8 LOC)
    > fetch_records                (line 30, 22 LOC)
  Skipped:
    x DBManager.__init__           (Dunder method (__init__))
```

## Viewing Advanced Function DNA

HezGene extracts deep software engineering metrics from your code. To view the complete profile of a function—including Big O complexity, Halstead effort, test coverage, and dependency graphs—use the `dna` command.

```bash
hezgene dna src/utils.py:process_data
```

*Expected Output:*
```text
🧬 Function DNA: process_data
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Complexity Analysis:
   Time Complexity:     O(n) 🟡
   Space Complexity:    O(1) 🟢
   Cyclomatic:          6 🟡
   Halstead Effort:     1,231 🟡
   Maintainability:     72/100 🟡

⚡ Performance:
   Avg Speed:           0.0032 ms
   Peak Memory:         940 bytes
   Scalability:         Linear 🟢

🛡️ Reliability:
   Bug Count:           0
   Test Coverage:       100%
   Uncovered:           None

🔗 Dependencies:
   Called by:           fetch_records, main
   Calls:               validate_input
   Impact Score:        Medium (2 dependents)

📈 Evolution History:
   Evolved:             1 times
   Last Evolved:        2026-05-20

🧬 Genetic Score: 85.2/100 🟢
```

## Evolving Your Code

By default, the `run` command operates in **Sandbox Mode**. The evolved code is safely written to `.hezgene/sandbox/` and your original file is never touched unless you append the `--apply` flag.

### 1. Evolve a Single Function
Specify a file and a function name separated by a colon.
```bash
hezgene run src/utils.py:process_data
```

### 2. Evolve a Class Method
```bash
hezgene run src/models.py:UserModel.save
```

### 3. Evolve an Entire File
Provide just the file path. HezGene will automatically extract and evolve every valid function inside it.
```bash
hezgene run src/processor.py
```

### 4. Target Priorities (Slowest or Buggiest)
HezGene's DNA tracker continuously ranks functions across your project. You can ask HezGene to automatically find and optimize your worst offenders.
```bash
hezgene run --target slowest
hezgene run --target buggiest
```

## Freezing Code

For critical functions that must never be altered (e.g., cryptographic hashing, strict compliance logic), you can freeze their DNA.

```bash
hezgene freeze src/security.py:hash_password
```
To unlock it:
```bash
hezgene unfreeze src/security.py:hash_password
```

## Sandbox Management

If your `.hezgene/sandbox` directory is getting full of old variants, you can wipe it clean:
```bash
hezgene clean
```

To wipe the sandbox **and** completely reset the DNA registry (erasing all historical metrics):
```bash
hezgene clean --all
```
