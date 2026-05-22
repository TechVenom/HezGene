def get_shipping_cost(weight: float, is_express: bool, is_international: bool) -> float:
    """
    Calculate shipping cost based on weight, speed, and destination.
    Deeply nested conditions make this hard to read.
    """
    if weight > 0:
        if weight < 5:
            if is_express:
                if is_international:
                    return 25.0
                else:
                    return 15.0
            else:
                if is_international:
                    return 15.0
                else:
                    return 5.0
        else:
            if is_express:
                if is_international:
                    return 50.0
                else:
                    return 30.0
            else:
                if is_international:
                    return 35.0
                else:
                    return 10.0
    else:
        return 0.0
