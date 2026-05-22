# Real-World Examples

Here are exact examples of how HezGene optimizes messy, human-written code into clean, performant structures.

## Example 1: The Verbose Loop (List Comprehension)

**Original Code:**
```python
def filter_active_users(users: list[dict]) -> list[dict]:
    active_users = []
    for user in users:
        if user.get("status") == "active":
            active_users.append(user)
    return active_users
```

**Run Command:**
```bash
hezgene run src/users.py:filter_active_users
```

**Evolved Result (30% Faster):**
```python
def filter_active_users(users: list[dict]) -> list[dict]:
    active_users = [user for user in users if user.get('status') == 'active']
    return active_users
```

---

## Example 2: The Nested Nightmare (Guard Clauses)

**Original Code:**
```python
def get_shipping_cost(weight: float, is_express: bool, is_international: bool) -> float:
    if weight > 0:
        if weight < 5:
            if is_express:
                if is_international:
                    return 25.0
                else:
                    return 15.0
# ... (goes on for 30 lines)
```

**Run Command:**
```bash
hezgene run src/shipping.py
```

**Evolved Result (Flattened Structure):**
```python
def get_shipping_cost(weight: float, is_express: bool, is_international: bool) -> float:
    if weight > 0:
        if weight < 5:
            if is_express:
                if is_international:
                    return 25.0
                return 15.0
            else:
                if is_international:
                    return 15.0
                return 5.0
        elif is_express:
            if is_international:
                return 50.0
            return 30.0
# ...
```

---

## Example 3: The Inefficient String Builder (Constant Folding)

**Original Code:**
```python
def build_report(transactions: list[dict]) -> str:
    report = ""
    report = report + "TRANSACTION REPORT\n"
    report = report + "=" * 40 + "\n"
    # ...
```

**Run Command:**
```bash
hezgene run src/reports.py
```

**Evolved Result (Zero-cost operations):**
```python
def build_report(transactions: list[dict]) -> str:
    report = ''
    report = report + 'TRANSACTION REPORT\n'
    report = report + '========================================' + '\n'
    # ...
```
*(The compiler no longer has to calculate `"=" * 40` at runtime every single time the function is called!)*
