"""
discount.py - E-commerce discount calculation engine with boolean and arithmetic rules.
"""

def calculate_discount(price: float, quantity: int, is_member: bool) -> float:
    """
    Calculates final price after applying volume and membership discounts.
    """
    if price <= 0.0:
        return 0.0

    discount_rate = 0.0
    if quantity >= 5:
        discount_rate = discount_rate + 0.10

    if is_member:
        discount_rate = discount_rate + 0.10

    final_price = price * (1.0 - discount_rate)
    return round(final_price, 2)
