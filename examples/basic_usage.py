def calculate_total(prices: list[float], tax_rate: float = 0.0) -> float:
    """
    Calculate the total price including tax.
    This is an unoptimized version meant to be evolved.
    """
    total = 0.0
    for price in prices:
        if price < 0:
            continue
        else:
            total = total + price

    if tax_rate > 0:
        tax = total * tax_rate
        total = total + tax

    return total


if __name__ == "__main__":
    print(f"Total: {calculate_total([10.0, 20.0], 0.1)}")
