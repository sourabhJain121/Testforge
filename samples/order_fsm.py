"""
order_fsm.py - E-commerce Order Lifecycle Finite State Machine.
Sample Target 3 for TestForge Benchmark Suite (State Transitions & RBAC Guards).
"""

from __future__ import annotations
from typing import Dict, List, Set, Tuple, Optional


ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    "CREATED": ["PENDING_PAYMENT", "CANCELLED"],
    "PENDING_PAYMENT": ["PAID", "CANCELLED"],
    "PAID": ["PROCESSING", "REFUNDED"],
    "PROCESSING": ["SHIPPED", "CANCELLED"],
    "SHIPPED": ["DELIVERED", "RETURNED"],
    "DELIVERED": ["COMPLETED"],
    "RETURNED": ["REFUNDED"],
    "CANCELLED": [],
    "REFUNDED": [],
    "COMPLETED": []
}

ADMIN_ONLY_TARGETS: Set[str] = {"REFUNDED", "CANCELLED"}
VALID_ROLES: Set[str] = {"CUSTOMER", "MERCHANT", "ADMIN", "SUPPORT"}


def validate_transition(
    current_state: str,
    next_state: str,
    user_role: str,
    amount: float
) -> Tuple[bool, Optional[str]]:
    """
    Pure validation function checking whether an order transition is permissible.
    Returns (allowed: bool, reason_or_error: Optional[str]).
    """
    if current_state not in ALLOWED_TRANSITIONS:
        return False, f"Unknown source state '{current_state}'"

    if next_state not in ALLOWED_TRANSITIONS:
        return False, f"Unknown target state '{next_state}'"

    allowed_targets = ALLOWED_TRANSITIONS.get(current_state, [])
    if next_state not in allowed_targets:
        return False, f"Illegal transition from '{current_state}' to '{next_state}'"

    if user_role not in VALID_ROLES:
        return False, f"Unauthorized role '{user_role}'"

    if next_state in ADMIN_ONLY_TARGETS and user_role not in ("ADMIN", "SUPPORT"):
        return False, f"State '{next_state}' requires administrative privileges"

    if next_state == "PAID" and amount >= 5000.0 and user_role == "CUSTOMER":
        return False, "High-value transactions require merchant or admin confirmation"

    return True, None


def transition_order_state(
    current_state: str,
    next_state: str,
    user_role: str,
    amount: float
) -> Tuple[bool, str]:
    """
    Executes a functional order state transition.
    Returns (success: bool, final_state_or_error: str).
    """
    allowed, reason = validate_transition(current_state, next_state, user_role, amount)
    if not allowed:
        return False, reason or "TRANSITION_REJECTED"
    return True, next_state


class OrderFSM:
    """
    Stateful object model governing order lifecycle transitions with audit history.
    """
    def __init__(self, order_id: str = "ORD-001", amount: float = 100.0, initial_state: str = "CREATED"):
        self.order_id: str = order_id
        self.amount: float = max(1.0, float(amount))
        self.state: str = initial_state if initial_state in ALLOWED_TRANSITIONS else "CREATED"
        self.history: List[Tuple[str, str, str]] = [("INITIAL", self.state, "SYSTEM")]

    def can_transition(self, next_state: str = "PENDING_PAYMENT", user_role: str = "CUSTOMER") -> Tuple[bool, Optional[str]]:
        """Checks if transition from current state is allowed."""
        return validate_transition(self.state, next_state, user_role, self.amount)

    def transition(self, next_state: str = "PENDING_PAYMENT", user_role: str = "CUSTOMER") -> Tuple[bool, str]:
        """Attempts transition, updating state and history if valid."""
        allowed, reason = self.can_transition(next_state, user_role)
        if not allowed:
            return False, reason or "REJECTED"
        prev = self.state
        self.state = next_state
        self.history.append((prev, next_state, user_role))
        return True, next_state

    def is_terminal(self) -> bool:
        """Returns True if the order has reached a terminal state."""
        return len(ALLOWED_TRANSITIONS.get(self.state, [])) == 0

    def get_audit_trail(self) -> List[str]:
        """Returns formatted string representations of state transition history."""
        return [f"{src}->{dst} by {role}" for src, dst, role in self.history]
