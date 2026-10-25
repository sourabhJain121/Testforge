"""
Auto-generated module based on specification:
Create a simple math multiplier function with input type checks.
"""

def process_transaction(amount: float, balance: float, is_vip: bool) -> tuple[bool, float]:
    """
    Executes a processed transaction with balance verification and VIP waivers.
    """
    if amount <= 0.0:
        return (False, balance)

    fee = 0.0 if is_vip else 2.50
    total_needed = amount + fee

    if balance >= total_needed:
        new_balance = balance - total_needed
        return (True, round(new_balance, 2))

    return (False, balance)
