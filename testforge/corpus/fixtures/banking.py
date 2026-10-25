"""
banking.py - Fixture 4: Banking Operations Module.

Category: Financial Ledger & Transaction Rules
Domain: Account transaction authorization with fee deductions and strict minimum reserve invariants.
"""

from testforge.corpus.models import CorpusFixture, DefectVariant

REFERENCE_CODE = '''"""
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
'''

BASELINE_TESTS = '''"""
baseline_tests.py - Test suite for Banking Operations Module.
"""
from target import banking_transaction


def test_nominal_transaction_succeeds():
    # $100.0 balance, $50.0 withdrawal, $5.0 fee -> balance 100 > 55 -> True
    assert banking_transaction(100.0, 50.0, 5.0) is True


def test_insufficient_funds_rejected():
    # $50.0 balance, $60.0 withdrawal, $2.0 fee -> 50 < 62 -> False
    assert banking_transaction(50.0, 60.0, 2.0) is False


def test_exact_balance_boundary_rejected_to_protect_reserve():
    # Rule requires balance strictly > total_deduction to maintain nonzero balance reserve
    # $55.0 balance, $50.0 withdrawal, $5.0 fee -> 55.0 is not > 55.0 -> False
    assert banking_transaction(55.0, 50.0, 5.0) is False


def test_zero_amount_rejected():
    assert banking_transaction(100.0, 0.0, 5.0) is False


def test_negative_amount_rejected():
    assert banking_transaction(100.0, -20.0, 5.0) is False


def test_zero_balance_rejected():
    assert banking_transaction(0.0, 10.0, 1.0) is False


def test_negative_balance_rejected():
    assert banking_transaction(-10.0, 10.0, 1.0) is False


def test_zero_fee_nominal_transaction():
    assert banking_transaction(100.0, 99.0, 0.0) is True
'''

# Defect 1: Exact balance allowed (>= instead of >), wiping out account reserve
BUGGY_CODE_DEFECT_1 = REFERENCE_CODE.replace(
    '    if balance > total_deduction:',
    '    if balance >= total_deduction:  # DEFECT: reserve boundary breach'
)

# Defect 2: Inverted balance comparison (< instead of >)
BUGGY_CODE_DEFECT_2 = REFERENCE_CODE.replace(
    '    if balance > total_deduction:',
    '    if balance < total_deduction:  # DEFECT: inverted balance condition'
)

# Defect 3: Negative amount check omitted (amount == 0 check only)
BUGGY_CODE_DEFECT_3 = REFERENCE_CODE.replace(
    '    if amount <= 0:\n        return False',
    '    if amount == 0:  # DEFECT: negative amounts bypass guard\n        return False'
)

DEFECTS = {
    "DEFECT-BK-001": DefectVariant(
        defect_id="DEFECT-BK-001",
        fixture_id="banking_operations_module",
        name="Minimum Reserve Invariant Breach (>= vs >)",
        defect_type="Boundary Relational Error (>= vs >)",
        description="Allows total deduction to equal balance (>= instead of >), breaching mandatory nonzero reserve invariant.",
        target_function="banking_transaction",
        buggy_source_code=BUGGY_CODE_DEFECT_1,
        expected_failing_test="test_exact_balance_boundary_rejected_to_protect_reserve",
        expected_error_type="AssertionError",
        expected_message_substring="assert banking_transaction(55.0, 50.0, 5.0) is False"
    ),
    "DEFECT-BK-002": DefectVariant(
        defect_id="DEFECT-BK-002",
        fixture_id="banking_operations_module",
        name="Transaction Approval Condition Inversion",
        defect_type="Condition Inversion / Logic Error",
        description="Inverts approval condition from balance > total_deduction to balance < total_deduction, rejecting solvent accounts.",
        target_function="banking_transaction",
        buggy_source_code=BUGGY_CODE_DEFECT_2,
        expected_failing_test="test_nominal_transaction_succeeds",
        expected_error_type="AssertionError",
        expected_message_substring="assert banking_transaction(100.0, 50.0, 5.0) is True"
    ),
    "DEFECT-BK-003": DefectVariant(
        defect_id="DEFECT-BK-003",
        fixture_id="banking_operations_module",
        name="Negative Amount Validation Drop",
        defect_type="Input Validation / Boundary Relational Flaw",
        description="Checks only amount == 0 instead of amount <= 0, permitting negative withdrawal amounts.",
        target_function="banking_transaction",
        buggy_source_code=BUGGY_CODE_DEFECT_3,
        expected_failing_test="test_negative_amount_rejected",
        expected_error_type="AssertionError",
        expected_message_substring="assert banking_transaction(100.0, -20.0, 5.0) is False"
    ),
}

FIXTURE = CorpusFixture(
    fixture_id="banking_operations_module",
    name="Banking Operations Module",
    category="Banking & Financial Ledger",
    description="Transaction authorization module enforcing fee deduction, balance constraints, and nonzero reserve invariants.",
    function_contract="banking_transaction(balance: float, amount: float, fee: float) -> bool",
    source_file="samples/banking.py",
    source_code=REFERENCE_CODE,
    baseline_test_code=BASELINE_TESTS,
    defects=DEFECTS,
)
