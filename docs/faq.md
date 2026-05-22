# Frequently Asked Questions

### Is HezGene safe to use on production code?
**Yes.** By default, HezGene runs entirely in **Sandbox Mode**. Your original files are completely untouched. HezGene only writes the evolved functions into `.hezgene/sandbox/` for you to review. To actually modify your production files, you must intentionally pass the `--apply` flag.

### What happens if a mutant breaks my code?
It will never see the light of day. The very first test in the **Fitness Gauntlet** is the Correctness Gate. The mutated function is executed side-by-side with your original function. If the outputs differ in any way, the mutant is instantly destroyed and disqualified from the tournament.

### Can I undo changes?
**Yes.** If you use `--apply` and realize later you want the old code back, you can use `hezgene rollback <target>` to surgically revert the function to its previous DNA state.

### Does HezGene work with any Python project?
**Yes.** HezGene is framework-agnostic. Whether you are building a Django backend, a FastAPI microservice, or a Data Science Pandas pipeline, HezGene parses the raw Python Abstract Syntax Tree (AST). 

### Does HezGene need test cases from me?
**No.** HezGene is fully autonomous. While you *can* provide test inputs, if you don't, HezGene's Fitness Gauntlet dynamically inspects your function's type hints and structure to auto-generate edge-case tests (empty lists, None types, extreme integers) to hammer the function.

### What types of functions can HezGene evolve?
Any standard Python function or class method. 

### Can HezGene evolve classes?
It evolves the *methods* inside the classes. It will intelligently skip constructor methods (`__init__`, `__new__`) and magic dunder methods to protect your system's structural integrity, focusing only on the logic methods.

### How does HezGene know what output is correct?
It assumes that the **Original Code** you wrote is logically correct, just inefficient. It treats your original code as the Ground Truth, and ensures all mutants perfectly match its behavior. 

### What if HezGene makes my code worse?
The Tournament Manager enforces a `min_improvement` threshold. If a mutant is not definitively faster, less memory intensive, or mathematically less complex than the original, HezGene simply discards it and reports `Unchanged`. It will never apply a downgrade.

### Can I control how aggressive the evolution is?
**Yes.** You can use the `-g` (generations) flag on the `run` command to increase or decrease how many mutants are spawned (e.g., `hezgene run src/utils.py -g 50`).

### Will HezGene change my imports or constants?
**No.** The Auto Deployer uses strict line-number mapping to ensure it only surgicaly replaces the exact block of code that defines the targeted function. Global variables, constants, imports, and surrounding comments remain untouched.
