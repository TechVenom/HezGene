# Getting Started with HezGene

Take your code from static to self-evolving in under 5 minutes.

## 1. Install HezGene

```bash
pip install hezgene
```

## 2. Initialize Your Project

Navigate to your Python project and run the initialization command. This creates a `.hezgene` directory to track the DNA of your functions and store sandbox results.

```bash
cd my_python_project
hezgene init
```

*Expected Output:*
```text
HezGene initialized!
Your project now has genetic evolution.
Run hezgene run <file.py> to start.
Results go to .hezgene/sandbox/ (original code is never modified).
```

## 3. Evolve Your First File

Pick a file that has some functions in it and run HezGene. By default, HezGene operates in **Sandbox Mode**, meaning it will generate optimized code but will *never* modify your original file unless you explicitly tell it to.

```bash
hezgene run src/utils.py
```

*Expected Output:*
```text
──────────────── HezGene -- Analyzing src/utils.py ─────────────────
  Found: 3 functions/methods

  > calculate_totals            SANDBOX
┌──────────────┬──────────┬─────────┬──────────┐
│  Metric      │  Before  │  After  │  Delta   │
├──────────────┼──────────┼─────────┼──────────┤
│  Fitness     │  45.2    │  89.4   │  +44.2   │
│  Speed (ms)  │  -       │  -      │  -12.500 │
│  Memory (B)  │  -       │  -      │  -1024   │
└──────────────┴──────────┴─────────┴──────────┘
```

## 4. Verify the Results

HezGene comes with a built-in verification tool that runs the original code and the evolved sandbox code side-by-side to guarantee that the logic remains 100% identical.

```bash
hezgene verify
```

## 5. Apply the Evolution

If you are happy with the results in the sandbox, you can run the command with the `--apply` flag to surgically inject the optimized code back into your original file.

```bash
hezgene run src/utils.py --apply
```

Congratulations! You've successfully evolved your software. Read the [Usage Guide](usage.md) to discover how to target the slowest or buggiest parts of your codebase automatically.
