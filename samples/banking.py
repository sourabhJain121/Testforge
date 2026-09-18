"""
banking.py - Target sample function with tricky boundary constraints.
"""

def banking_transaction(balance: float, amount: float, fee: float) -> bool:
    """
    Executes a banking transaction with fee verification.
    Requires:
      - balance > 0
      - amount > 0
      - balance > amount + fee
    """
    if balance <= 0:
        return False

    if amount <= 0:
        return False

    total_deduction = amount + fee
    if balance > total_deduction:
        balance = balance - total_deduction
        return True

    return False
