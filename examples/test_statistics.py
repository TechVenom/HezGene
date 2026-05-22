def calculate_statistics(numbers: list[float]) -> dict:
    """
    Calculate min, max, average, and count of numbers.
    Multiple passes through the list are inefficient.
    """
    stats = {}
    stats["count"] = len(numbers)

    if stats["count"] == 0:
        stats["min"] = None
        stats["max"] = None
        stats["average"] = None
        stats["sum"] = 0
        return stats

    total = 0
    for num in numbers:
        total = total + num
    stats["sum"] = total
    stats["average"] = total / stats["count"]

    min_val = numbers[0]
    for num in numbers:
        if num < min_val:
            min_val = num
    stats["min"] = min_val

    max_val = numbers[0]
    for num in numbers:
        if num > max_val:
            max_val = num
    stats["max"] = max_val

    return stats
