"""
state_machine.py - Fixture 1: Task / Order Lifecycle State Machine with RBAC.

Category: Task / State Transition System
Domain: E-commerce order lifecycle FSM with role-based access control and high-value verification.
"""

from testforge.corpus.models import CorpusFixture, DefectVariant

REFERENCE_CODE = '''"""
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
'''

BASELINE_TESTS = '''"""
baseline_tests.py - Test suite for Order Lifecycle State Machine.
"""
from target import transition_order_state


def test_nominal_transition_created_to_payment_pending():
    ok, state = transition_order_state("CREATED", "PAYMENT_PENDING", "CUSTOMER", 50.0)
    assert ok is True
    assert state == "PAYMENT_PENDING"


def test_nominal_shipping_to_delivery():
    ok, state = transition_order_state("SHIPPED", "DELIVERED", "LOGISTICS", 120.0)
    assert ok is True
    assert state == "DELIVERED"


def test_invalid_current_state_rejected():
    ok, err = transition_order_state("NON_EXISTENT", "PAID", "ADMIN", 10.0)
    assert ok is False
    assert err == "INVALID_CURRENT_STATE"


def test_disallowed_transition_sequence():
    ok, err = transition_order_state("CREATED", "DELIVERED", "ADMIN", 10.0)
    assert ok is False
    assert err == "INVALID_TRANSITION"


def test_terminal_state_completed_has_no_outgoing_transitions():
    ok, err = transition_order_state("COMPLETED", "RUNNING", "ADMIN", 50.0)
    assert ok is False
    assert err == "INVALID_TRANSITION"


def test_admin_cancellation_authorized():
    ok, state = transition_order_state("PROCESSING", "CANCELLED", "ADMIN", 300.0)
    assert ok is True
    assert state == "CANCELLED"


def test_customer_cancellation_unauthorized_from_processing():
    ok, err = transition_order_state("PROCESSING", "CANCELLED", "CUSTOMER", 300.0)
    assert ok is False
    assert err == "UNAUTHORIZED_TRANSITION"


def test_high_value_guest_payment_requires_verification():
    ok, err = transition_order_state("PAYMENT_PENDING", "PAID", "GUEST", 10000.0)
    assert ok is False
    assert err == "VERIFICATION_REQUIRED"


def test_high_value_verified_user_payment_permitted():
    ok, state = transition_order_state("PAYMENT_PENDING", "PAID", "VERIFIED_USER", 15000.0)
    assert ok is True
    assert state == "PAID"
'''

# Defect 1: Unauthorized cancellation bypass (fails RBAC check)
BUGGY_CODE_DEFECT_1 = REFERENCE_CODE.replace(
    '''    # Guard admin-restricted target states
    if next_state in ADMIN_ONLY_TARGETS:
        if user_role != "ADMIN" and user_role != "SUPERUSER":
            return (False, "UNAUTHORIZED_TRANSITION")''',
    '''    # Guard admin-restricted target states (DEFECT: user check removed)
    if next_state in ADMIN_ONLY_TARGETS and False:
        if user_role != "ADMIN" and user_role != "SUPERUSER":
            return (False, "UNAUTHORIZED_TRANSITION")'''
)

# Defect 2: Terminal State Leak (COMPLETED allows transitions to RUNNING)
BUGGY_CODE_DEFECT_2 = REFERENCE_CODE.replace(
    '    "COMPLETED": []',
    '    "COMPLETED": ["RUNNING"]'
)

# Defect 3: High value verification boundary strict comparison bug (> instead of >=)
BUGGY_CODE_DEFECT_3 = REFERENCE_CODE.replace(
    'if next_state == "PAID" and order_amount >= 10000.0:',
    'if next_state == "PAID" and order_amount > 10000.0:'
)

DEFECTS = {
    "DEFECT-SM-001": DefectVariant(
        defect_id="DEFECT-SM-001",
        fixture_id="task_state_transition",
        name="RBAC Authorization Bypass on Cancellation",
        defect_type="Security / Authorization Bypass",
        description="Disabled role check allowing unprivileged CUSTOMER users to cancel in-progress orders.",
        target_function="transition_order_state",
        buggy_source_code=BUGGY_CODE_DEFECT_1,
        expected_failing_test="test_customer_cancellation_unauthorized_from_processing",
        expected_error_type="AssertionError",
        expected_message_substring="assert err == 'UNAUTHORIZED_TRANSITION'"
    ),
    "DEFECT-SM-002": DefectVariant(
        defect_id="DEFECT-SM-002",
        fixture_id="task_state_transition",
        name="Terminal State Leak on COMPLETED",
        defect_type="Finite State Machine Logic / Terminal Leak",
        description="Allows illegal transition from terminal state COMPLETED back to RUNNING.",
        target_function="transition_order_state",
        buggy_source_code=BUGGY_CODE_DEFECT_2,
        expected_failing_test="test_terminal_state_completed_has_no_outgoing_transitions",
        expected_error_type="AssertionError",
        expected_message_substring="assert ok is False"
    ),
    "DEFECT-SM-003": DefectVariant(
        defect_id="DEFECT-SM-003",
        fixture_id="task_state_transition",
        name="High-Value Verification Boundary Off-By-One",
        defect_type="Boundary Relational Error (> vs >=)",
        description="Fails to trigger VERIFICATION_REQUIRED on exactly $10,000.0 orders due to strict inequality.",
        target_function="transition_order_state",
        buggy_source_code=BUGGY_CODE_DEFECT_3,
        expected_failing_test="test_high_value_guest_payment_requires_verification",
        expected_error_type="AssertionError",
        expected_message_substring="assert err == 'VERIFICATION_REQUIRED'"
    ),
}

FIXTURE = CorpusFixture(
    fixture_id="task_state_transition",
    name="Task & Order Lifecycle State Machine",
    category="Finite State Machine & Access Control",
    description="Branching state machine enforcing multi-step transitions, terminal guarantees, and RBAC guards.",
    function_contract="transition_order_state(current_state: str, next_state: str, user_role: str, order_amount: float) -> tuple[bool, str]",
    source_file="samples/state_machine.py",
    source_code=REFERENCE_CODE,
    baseline_test_code=BASELINE_TESTS,
    defects=DEFECTS,
)
