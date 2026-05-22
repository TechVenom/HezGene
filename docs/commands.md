# Complete CLI Reference

Here is a comprehensive breakdown of every command available in the HezGene CLI.

---

### `hezgene init`
**Description:** Initializes a project for genetic evolution by creating the `.hezgene` directory, DNA registry, and sandbox.
**Options:** None
**Example:** `hezgene init`

---

### `hezgene scan` (or `hezgene analyze`)
**Description:** Analyzes a Python file and displays a breakdown of which functions and classes are evolvable, and which are skipped (and why).
**Arguments:** 
- `PATH`: The path to the Python file to analyze.
**Example:** `hezgene scan src/main.py`

---

### `hezgene run`
**Description:** Runs the evolution cycle on a target. Generates mutants, runs them through the fitness gauntlet, and outputs the winner to the sandbox.
**Arguments:** 
- `PATH`: File, Directory, or specific function (e.g., `file.py:func`).
**Options:**
- `--all`: Evolve all tracked functions in the entire DNA registry.
- `--target [slowest|buggiest]`: Automatically pick and evolve the highest priority target.
- `--apply`: **DANGER.** Surgically deploys the evolved code into your original source file, replacing the old code.
- `-g, --generations INTEGER`: Number of mutations to spawn per cycle (default: 5).
**Example:** `hezgene run src/utils.py --apply -g 10`

---

### `hezgene verify`
**Description:** Looks in the sandbox for evolved functions and dynamically executes them side-by-side against the original functions to verify that the logic remains 100% identical.
**Arguments:** 
- `TEST_SCRIPT` (Optional): A custom Python script to run the verification (default: `verify_outputs.py`).
**Example:** `hezgene verify`

---

### `hezgene clean`
**Description:** Clears out the temporary generated files in the `.hezgene/sandbox` directory to save space.
**Options:**
- `--all`: Also completely clears out the `dna_registry.json`, erasing all historical metrics.
**Example:** `hezgene clean --all`

---

### `hezgene log`
**Description:** Displays a tabular history of all evolutions that have occurred across your project.
**Options:** None
**Example:** `hezgene log`

---

### `hezgene dna`
**Description:** Displays the exact DNA profile (Memory, Speed, Complexity, LOC) for a specific function.
**Arguments:**
- `TARGET`: The specific function (e.g., `src/utils.py:func`).
**Example:** `hezgene dna src/utils.py:process_data`

---

### `hezgene freeze`
**Description:** Locks a function so that it can never be mutated or evolved by the `run` command.
**Arguments:**
- `TARGET`: The specific function to freeze.
**Example:** `hezgene freeze src/auth.py:verify_token`

---

### `hezgene unfreeze`
**Description:** Unlocks a previously frozen function, allowing it to evolve again.
**Arguments:**
- `TARGET`: The specific function to unfreeze.
**Example:** `hezgene unfreeze src/auth.py:verify_token`

---

### `hezgene rollback`
**Description:** Reverts a deployed evolution back to the previous version of the function (Requires `--apply` to have been used).
**Arguments:**
- `TARGET`: The specific function to rollback.
**Example:** `hezgene rollback src/utils.py:process_data`

---

### `hezgene config`
**Description:** Configure global HezGene settings (such as strictness of the gauntlet, or LLM integration keys for Phase 2).
**Options:**
- `--set KEY VALUE`: Set a configuration value.
- `--list`: List all configurations.
**Example:** `hezgene config --set min_improvement 10.0`
