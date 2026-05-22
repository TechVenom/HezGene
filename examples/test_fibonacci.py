def fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number recursively.
    This is intentionally inefficient — O(2^n) complexity.
    """
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)
