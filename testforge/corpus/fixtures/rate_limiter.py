"""
rate_limiter.py - Fixture 2: Token Bucket Rate Limiter.

Category: Concurrency & Rate Limiting Algorithm
Domain: Token bucket algorithm with burst capacity, fractional time decay, and boundary validation.
"""

from testforge.corpus.models import CorpusFixture, DefectVariant

REFERENCE_CODE = '''"""
rate_limiter.py - Token bucket algorithm with time-decay and burst boundaries.
"""
from typing import Tuple


def evaluate_rate_limit(
    tokens_available: float,
    bucket_capacity: float,
    refill_rate_per_sec: float,
    elapsed_seconds: float,
    requested_tokens: int
) -> Tuple[bool, float]:
    """
    Evaluates a rate limit request using the token bucket algorithm.

    Preconditions:
      - bucket_capacity >= 1.0.
      - requested_tokens >= 1.
      - elapsed_seconds >= 0.0.
      - refill_rate_per_sec >= 0.0.

    Postconditions:
      - Returns (is_allowed: bool, remaining_tokens: float).
      - Tokens cannot exceed bucket_capacity after refill.
      - If request is granted: remaining_tokens = current_tokens - requested_tokens.
      - If request is denied: remaining_tokens = current_tokens.
    """
    if bucket_capacity < 1.0 or requested_tokens < 1:
        return (False, max(0.0, tokens_available))

    if elapsed_seconds < 0.0 or refill_rate_per_sec < 0.0:
        return (False, tokens_available)

    # Refill tokens up to bucket capacity
    refilled = tokens_available + (refill_rate_per_sec * elapsed_seconds)
    current_tokens = min(bucket_capacity, refilled)

    if current_tokens >= float(requested_tokens):
        new_balance = current_tokens - float(requested_tokens)
        return (True, round(new_balance, 3))

    return (False, round(current_tokens, 3))
'''

BASELINE_TESTS = '''"""
baseline_tests.py - Test suite for Token Bucket Rate Limiter.
"""
from target import evaluate_rate_limit


def test_nominal_request_allowed_with_deduction():
    allowed, rem = evaluate_rate_limit(5.0, 10.0, 1.0, 1.0, 2)
    assert allowed is True
    # 5.0 + (1.0 * 1.0) = 6.0; 6.0 - 2 = 4.0
    assert rem == 4.0


def test_refill_capped_at_bucket_capacity():
    # 8.0 tokens + (5.0/s * 2.0s) = 18.0 tokens; capped at 10.0; request 3 -> 7.0 left
    allowed, rem = evaluate_rate_limit(8.0, 10.0, 5.0, 2.0, 3)
    assert allowed is True
    assert rem == 7.0


def test_request_denied_when_insufficient_tokens():
    # 1.0 token + (0.5 * 2.0) = 2.0 tokens; request 5 -> denied, 2.0 left
    allowed, rem = evaluate_rate_limit(1.0, 10.0, 0.5, 2.0, 5)
    assert allowed is False
    assert rem == 2.0


def test_exact_balance_boundary_request_granted():
    # Exactly 3.0 tokens available, requesting exactly 3 tokens
    allowed, rem = evaluate_rate_limit(3.0, 10.0, 0.0, 0.0, 3)
    assert allowed is True
    assert rem == 0.0


def test_negative_elapsed_seconds_rejected():
    allowed, rem = evaluate_rate_limit(5.0, 10.0, 1.0, -2.0, 1)
    assert allowed is False
    assert rem == 5.0


def test_invalid_zero_capacity_rejected():
    allowed, rem = evaluate_rate_limit(0.0, 0.0, 1.0, 1.0, 1)
    assert allowed is False


def test_invalid_zero_requested_tokens_rejected():
    allowed, rem = evaluate_rate_limit(5.0, 10.0, 1.0, 1.0, 0)
    assert allowed is False


def test_fractional_refill_precision():
    # 2.5 tokens + (1.25 * 0.4) = 2.5 + 0.5 = 3.0; request 1 -> 2.0
    allowed, rem = evaluate_rate_limit(2.5, 5.0, 1.25, 0.4, 1)
    assert allowed is True
    assert rem == 2.0
'''

# Defect 1: Refill not capped at bucket capacity
BUGGY_CODE_DEFECT_1 = REFERENCE_CODE.replace(
    '    current_tokens = min(bucket_capacity, refilled)',
    '    current_tokens = refilled  # DEFECT: uncapped accumulation'
)

# Defect 2: Negative elapsed seconds not guarded
BUGGY_CODE_DEFECT_2 = REFERENCE_CODE.replace(
    '    if elapsed_seconds < 0.0 or refill_rate_per_sec < 0.0:\n        return (False, tokens_available)',
    '    # DEFECT: negative time guard removed\n    pass'
)

# Defect 3: Strict inequality starving exact balance requests (> instead of >=)
BUGGY_CODE_DEFECT_3 = REFERENCE_CODE.replace(
    '    if current_tokens >= float(requested_tokens):',
    '    if current_tokens > float(requested_tokens):  # DEFECT: strict inequality'
)

DEFECTS = {
    "DEFECT-RL-001": DefectVariant(
        defect_id="DEFECT-RL-001",
        fixture_id="token_bucket_rate_limiter",
        name="Uncapped Bucket Capacity Accumulation",
        defect_type="Boundary Clamping Omission",
        description="Omits min(bucket_capacity, refilled), allowing tokens to exceed bucket maximum burst size.",
        target_function="evaluate_rate_limit",
        buggy_source_code=BUGGY_CODE_DEFECT_1,
        expected_failing_test="test_refill_capped_at_bucket_capacity",
        expected_error_type="AssertionError",
        expected_message_substring="assert rem == 7.0"
    ),
    "DEFECT-RL-002": DefectVariant(
        defect_id="DEFECT-RL-002",
        fixture_id="token_bucket_rate_limiter",
        name="Negative Elapsed Time Clock Reversal Blindness",
        defect_type="Input Validation / Clock Reversal Anomaly",
        description="Fails to reject negative elapsed_seconds, permitting time-travel token balance distortion.",
        target_function="evaluate_rate_limit",
        buggy_source_code=BUGGY_CODE_DEFECT_2,
        expected_failing_test="test_negative_elapsed_seconds_rejected",
        expected_error_type="AssertionError",
        expected_message_substring="assert allowed is False"
    ),
    "DEFECT-RL-003": DefectVariant(
        defect_id="DEFECT-RL-003",
        fixture_id="token_bucket_rate_limiter",
        name="Exact Balance Request Starvation (> vs >=)",
        defect_type="Boundary Relational Error (> vs >=)",
        description="Requires current_tokens > requested_tokens instead of >=, rejecting requests when exact balance matches.",
        target_function="evaluate_rate_limit",
        buggy_source_code=BUGGY_CODE_DEFECT_3,
        expected_failing_test="test_exact_balance_boundary_request_granted",
        expected_error_type="AssertionError",
        expected_message_substring="assert allowed is True"
    ),
}

FIXTURE = CorpusFixture(
    fixture_id="token_bucket_rate_limiter",
    name="Token Bucket Rate Limiter",
    category="Rate Limiting & Traffic Shaping",
    description="Deterministic token bucket rate limiter with burst bounds, time-decay refill, and parameter validation.",
    function_contract="evaluate_rate_limit(tokens_available: float, bucket_capacity: float, refill_rate_per_sec: float, elapsed_seconds: float, requested_tokens: int) -> Tuple[bool, float]",
    source_file="samples/rate_limiter.py",
    source_code=REFERENCE_CODE,
    baseline_test_code=BASELINE_TESTS,
    defects=DEFECTS,
)
