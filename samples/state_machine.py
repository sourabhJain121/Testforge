"""
samples/state_machine.py - Order lifecycle finite state machine with RBAC guards.
"""

ALLOWED_TRANSITIONS = {
    "CREATED": ["PAYMENT_PENDING", "CANCELLED"],
    "PAYMENT_PENDING": ["PAID", "CANCELLED"],
    "PAID": ["PROCESSING", "REFUNDED"],
    "PROCESSING": ["SHIPPED", "CANCELLED"],
    "SHIPPED": ["DELIVERED", "RETURNED"],
    "DELIVERED": ["COMPLETED"],
    "CANCELLED": [],
    "REFUNDED": [],
    "RETURNED": ["REFUNDED"],
    "COMPLETED": []
}

ADMIN_ONLY_TARGETS = {"REFUNDED", "CANCELLED"}

def transition_order_state(
    current_state: str,
    next_state: str,
    user_role: str,
    order_amount: float
) -> tuple[bool, str]:
    """
    Validates and executes order state transition.

    Returns:
      (success: bool, final_state_or_error: str)
    """
    if current_state not in ALLOWED_TRANSITIONS:
        return (False, "INVALID_CURRENT_STATE")

    if next_state not in ALLOWED_TRANSITIONS[current_state]:
        return (False, "INVALID_TRANSITION")

    # Guard admin-restricted target states
    if next_state in ADMIN_ONLY_TARGETS:
        if user_role != "ADMIN" and user_role != "SUPERUSER":
            return (False, "UNAUTHORIZED_TRANSITION")

    # High value order safety condition
    if next_state == "PAID" and order_amount >= 10000.0:
        if user_role == "GUEST":
            return (False, "VERIFICATION_REQUIRED")

    return (True, next_state)
