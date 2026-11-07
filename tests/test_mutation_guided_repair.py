"""
tests/test_mutation_guided_repair.py - Granular Generated-Test Validation Suite.

Milestone 1 for Phase 4.1:
Validates candidate test functions individually against clean target code so that
one broken or invalid test does not force the entire candidate suite to be discarded.
"""

import ast
import hashlib
from typing import Any, Dict
from unittest.mock import Mock

import pytest

from testforge.agents import AdversarialCriticAgent, TestGeneratorAgent
from testforge.blackboard import Blackboard
from testforge.equivalence import calculate_mutation_scores
from testforge.guidance import (
    SemanticMutantGuidance,
    derive_guidance_for_surviving_mutants,
    derive_semantic_guidance,
)
from testforge.mutator import ASTMutator
from testforge.sandbox import (
    CandidateSuiteValidationResult,
    GranularTestValidator,
    ParallelSandboxRunner,
    SubprocessSandbox,
    TestValidationStatus,
)
from testforge.state import MutantRecord, TestForgeState

TestGeneratorAgent.__test__ = False


CLEAN_MATH_TARGET = '''
"""Simple arithmetic service."""

def add(a: int, b: int) -> int:
    return a + b

def subtract(a: int, b: int) -> int:
    return a - b

def multiply(a: int, b: int) -> int:
    return a * b

def divide(a: int, b: int) -> float:
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b
'''


EXISTING_BASE_SUITE = '''
import pytest
from target import add

def test_add_baseline():
    assert add(1, 2) == 3
'''


class TestGranularTestValidation:
    """Suite testing granular candidate test extraction, isolation, and merge logic."""

    @pytest.fixture
    def sandbox(self):
        return SubprocessSandbox(timeout_seconds=3)

    @pytest.fixture
    def validator(self):
        return GranularTestValidator()

    # 1. Mixture of valid and failing candidate tests
    def test_mixture_of_valid_and_failing_candidate_tests(self, sandbox, validator):
        candidate = '''
import pytest
from target import add, subtract, multiply

def test_valid_sub():
    assert subtract(10, 4) == 6

def test_broken_assertion():
    assert add(2, 2) == 999  # Broken assertion against clean code

def test_valid_mul():
    assert multiply(3, 4) == 12
'''
        res: CandidateSuiteValidationResult = validator.validate_candidate_suite(
            candidate_test_code=candidate,
            target_code=CLEAN_MATH_TARGET,
            sandbox_runner=sandbox,
            existing_test_code=EXISTING_BASE_SUITE
        )

        assert res.total_candidates == 3
        assert res.retained_count == 2
        assert res.rejected_count == 1
        assert res.quarantined_count == 1

        valid_names = {t.name for t in res.valid_tests}
        failing_names = {t.name for t in res.failing_tests}

        assert "test_valid_sub" in valid_names
        assert "test_valid_mul" in valid_names
        assert "test_broken_assertion" in failing_names

        # Verify retained test code executes cleanly on target
        check = sandbox.run_single(res.retained_test_code, CLEAN_MATH_TARGET)
        assert check["status"] == "PASS"
        assert check["tests_passed"] >= 3  # baseline + 2 new valid tests
        assert check["tests_failed"] == 0

    # 2. Syntax errors
    def test_syntax_errors_handled_gracefully(self, sandbox, validator):
        broken_syntax_candidate = '''
from target import add

def test_bad_syntax(
    assert add(1, 2) == 3
'''
        res = validator.validate_candidate_suite(
            candidate_test_code=broken_syntax_candidate,
            target_code=CLEAN_MATH_TARGET,
            sandbox_runner=sandbox,
            existing_test_code=EXISTING_BASE_SUITE
        )

        assert res.overall_status == TestValidationStatus.SYNTAX_ERROR
        assert res.total_candidates == 0
        assert res.retained_count == 0
        assert "SyntaxError" in res.error_message
        assert res.retained_test_code == EXISTING_BASE_SUITE

    # 3. Missing imports or collection errors
    def test_missing_imports_classified_as_infrastructure_error(self, sandbox, validator):
        candidate_missing_import = '''
import nonexistent_package_xyz_998877
from target import add

def test_foo():
    assert add(1, 1) == 2
'''
        res = validator.validate_candidate_suite(
            candidate_test_code=candidate_missing_import,
            target_code=CLEAN_MATH_TARGET,
            sandbox_runner=sandbox,
            existing_test_code=EXISTING_BASE_SUITE
        )

        assert res.overall_status == TestValidationStatus.INFRASTRUCTURE_ERROR
        assert res.retained_count == 0
        # Inconclusive tests must NOT be misclassified as FAILING assertions
        assert len(res.failing_tests) == 0
        assert len(res.inconclusive_tests) > 0
        assert res.retained_test_code == EXISTING_BASE_SUITE

    # 4. Fixtures and parametrized tests
    def test_fixtures_and_parametrized_tests_preserved(self, sandbox, validator):
        candidate_with_fixtures = '''
import pytest
from target import add, divide

@pytest.fixture
def sample_numbers():
    return (20, 5)

@pytest.mark.parametrize("x, y, expected", [
    (1, 1, 2),
    (10, 20, 30),
    (-5, 5, 0),
])
def test_parametrized_add(x, y, expected):
    assert add(x, y) == expected

def test_fixture_division(sample_numbers):
    a, b = sample_numbers
    assert divide(a, b) == 4.0
'''
        res = validator.validate_candidate_suite(
            candidate_test_code=candidate_with_fixtures,
            target_code=CLEAN_MATH_TARGET,
            sandbox_runner=sandbox
        )

        assert res.overall_status == "ALL_VALID"
        assert res.retained_count == 2
        assert res.rejected_count == 0

        # Verify decorators and fixtures are preserved in retained code
        assert "@pytest.fixture" in res.retained_test_code
        assert "@pytest.mark.parametrize" in res.retained_test_code

        # Run in sandbox to confirm all runs pass
        run_res = sandbox.run_single(res.retained_test_code, CLEAN_MATH_TARGET)
        assert run_res["status"] == "PASS"
        assert run_res["tests_passed"] == 4  # 3 parametrized variants + 1 fixture test

    # 5. Candidate that times out
    def test_candidate_timeout_quarantined_without_discarding_valid_tests(self, sandbox, validator):
        # Runner with short 1-second timeout
        short_sandbox = SubprocessSandbox(timeout_seconds=1)
        candidate_with_hang = '''
from target import add

def test_instant_pass():
    assert add(2, 3) == 5

def test_infinite_loop():
    import time
    time.sleep(5)  # Exceeds 1s timeout
    assert add(1, 1) == 2
'''
        res = validator.validate_candidate_suite(
            candidate_test_code=candidate_with_hang,
            target_code=CLEAN_MATH_TARGET,
            sandbox_runner=short_sandbox,
            timeout_seconds=1
        )

        assert res.total_candidates == 2
        assert res.retained_count == 1
        assert "test_instant_pass" in {t.name for t in res.valid_tests}

        # Hanging test is classified as TIMEOUT, not FAILING
        assert len(res.inconclusive_tests) == 1
        assert res.inconclusive_tests[0].status == TestValidationStatus.TIMEOUT
        assert res.inconclusive_tests[0].name == "test_infinite_loop"

        # Retained suite contains only the instant pass
        run_res = short_sandbox.run_single(res.retained_test_code, CLEAN_MATH_TARGET)
        assert run_res["status"] == "PASS"
        assert run_res["tests_passed"] == 1

    # 6. Infrastructure failure not misclassified as a bad test
    def test_infrastructure_failure_not_misclassified(self, validator):
        # Empty candidate code
        empty_res = validator.validate_candidate_suite(
            candidate_test_code="   ",
            target_code=CLEAN_MATH_TARGET,
            existing_test_code=EXISTING_BASE_SUITE
        )
        assert empty_res.overall_status == "EMPTY_CANDIDATE"
        assert len(empty_res.failing_tests) == 0
        assert empty_res.retained_test_code == EXISTING_BASE_SUITE

    # 7. Trivial tests with no meaningful assertions rejected
    def test_trivial_assertions_rejected(self, sandbox, validator):
        candidate_trivial = '''
from target import add

def test_assert_true():
    assert True

def test_assert_not_false():
    assert not False

def test_no_assertions():
    x = add(1, 2)
    y = x + 1

def test_meaningful():
    assert add(10, 20) == 30
'''
        res = validator.validate_candidate_suite(
            candidate_test_code=candidate_trivial,
            target_code=CLEAN_MATH_TARGET,
            sandbox_runner=sandbox
        )

        assert res.total_candidates == 4
        assert res.retained_count == 1
        assert len(res.trivial_tests) == 3

        trivial_names = {t.name for t in res.trivial_tests}
        assert "test_assert_true" in trivial_names
        assert "test_assert_not_false" in trivial_names
        assert "test_no_assertions" in trivial_names
        assert res.valid_tests[0].name == "test_meaningful"

    # 8. Preservation of existing accepted suite when all candidates fail
    def test_preservation_of_existing_suite_when_all_fail(self, sandbox, validator):
        all_failing_candidate = '''
from target import add, subtract

def test_wrong_add():
    assert add(1, 1) == 999

def test_wrong_sub():
    assert subtract(5, 5) == 999
'''
        res = validator.validate_candidate_suite(
            candidate_test_code=all_failing_candidate,
            target_code=CLEAN_MATH_TARGET,
            sandbox_runner=sandbox,
            existing_test_code=EXISTING_BASE_SUITE
        )

        assert res.total_candidates == 2
        assert res.retained_count == 0
        assert res.rejected_count == 2
        assert res.quarantined_count == 2
        # Existing suite strictly preserved
        assert res.retained_test_code == EXISTING_BASE_SUITE

    # 9. Regression tests proving target source is unchanged
    def test_regression_target_source_code_strictly_unchanged(self, sandbox, validator):
        original_hash = hashlib.sha256(CLEAN_MATH_TARGET.encode("utf-8")).hexdigest()

        candidate = '''
from target import add
def test_add_ok():
    assert add(5, 5) == 10
'''
        res = validator.validate_candidate_suite(
            candidate_test_code=candidate,
            target_code=CLEAN_MATH_TARGET,
            sandbox_runner=sandbox
        )

        after_hash = hashlib.sha256(CLEAN_MATH_TARGET.encode("utf-8")).hexdigest()
        assert original_hash == after_hash, "Clean target source code must never be mutated during test validation."

    # 10. Valid test depending on shared module state or setup
    def test_shared_module_state_and_setup(self, sandbox, validator):
        candidate_stateful = '''
import pytest
from target import add

# Shared module state initialized in preamble
CALL_LOG = []

def helper_record(val):
    CALL_LOG.append(val)
    return val

def test_uses_shared_helper():
    res = helper_record(add(2, 3))
    assert res == 5
    assert len(CALL_LOG) > 0

def test_another_using_helper():
    res = helper_record(add(4, 4))
    assert res == 8
    assert len(CALL_LOG) >= 1
'''
        res = validator.validate_candidate_suite(
            candidate_test_code=candidate_stateful,
            target_code=CLEAN_MATH_TARGET,
            sandbox_runner=sandbox
        )

        assert res.overall_status == "ALL_VALID"
        assert res.retained_count == 2
        assert len(res.failing_tests) == 0

        # Verify execution
        run_res = sandbox.run_single(res.retained_test_code, CLEAN_MATH_TARGET)
        assert run_res["status"] == "PASS"
        assert run_res["tests_passed"] == 2


class TestSemanticMutantGuidanceAndM01:
    """Suite testing Milestone 2 semantic mutant guidance and M-01 custom assertion resolution."""

    @pytest.fixture
    def sandbox(self):
        return SubprocessSandbox(timeout_seconds=3)

    @pytest.fixture
    def validator(self):
        return GranularTestValidator()

    # 1. Semantic guidance for supported comparison mutations
    def test_semantic_guidance_comparison_mutations(self):
        mutant = MutantRecord(
            mutant_id="MUT_COMP_OP_001",
            mutation_type="COMP_OP",
            line_number=15,
            original_code_snippet="if x == 100:\n    return True",
            mutated_code_snippet="if x != 100:\n    return True",
            unified_diff="--- target.py\n+++ target.py\n@@ -15,1 +15,1 @@\n-if x == 100:\n+if x != 100:",
            original_expression="x == 100",
            mutated_expression="x != 100"
        )
        guidance = derive_semantic_guidance(mutant)
        assert guidance.mutant_id == "MUT_COMP_OP_001"
        assert guidance.mutation_type == "COMP_OP"
        assert guidance.line_number == 15
        assert guidance.confidence == "HIGH"
        assert "Equality comparison inverted" in guidance.behavioral_distinction
        assert any("LHS == RHS" in s for s in guidance.suggested_inputs)

    # 2. Boundary-value guidance
    def test_boundary_value_guidance(self):
        mutant = MutantRecord(
            mutant_id="MUT_BOUNDARY_SWAP_002",
            mutation_type="BOUNDARY_SWAP",
            line_number=20,
            original_code_snippet="return amount >= 50.0",
            mutated_code_snippet="return amount > 50.0",
            unified_diff="--- target.py\n+++ target.py\n@@ -20,1 +20,1 @@\n-return amount >= 50.0\n+return amount > 50.0",
            original_expression="amount >= 50.0",
            mutated_expression="amount > 50.0"
        )
        guidance = derive_semantic_guidance(mutant)
        assert guidance.confidence == "HIGH"
        assert "narrowed from inclusive" in guidance.behavioral_distinction
        assert any("LHS == RHS" in s for s in guidance.suggested_inputs)
        directive_text = guidance.to_directive_text()
        assert "[MUT_BOUNDARY_SWAP_002]" in directive_text
        assert "Line 20" in directive_text

    # 3. Non-comparison mutations (ARITH_OP, LOGICAL_CONN, MATH_FUNC)
    def test_non_comparison_mutation_guidance(self):
        arith_mutant = MutantRecord(
            mutant_id="MUT_ARITH_OP_003",
            mutation_type="ARITH_OP",
            line_number=8,
            original_code_snippet="return a + b",
            mutated_code_snippet="return a - b",
            unified_diff="--- target.py\n+++ target.py\n@@ -8,1 +8,1 @@\n-return a + b\n+return a - b",
            original_expression="a + b",
            mutated_expression="a - b"
        )
        g_arith = derive_semantic_guidance(arith_mutant)
        assert "Addition operator swapped with subtraction" in g_arith.behavioral_distinction
        assert any("b != 0" in s for s in g_arith.suggested_inputs)
        assert any("coincidental" in s for s in g_arith.suggested_inputs)

        logical_mutant = MutantRecord(
            mutant_id="MUT_LOGICAL_CONN_004",
            mutation_type="LOGICAL_CONN",
            line_number=12,
            original_code_snippet="return is_admin and is_active",
            mutated_code_snippet="return is_admin or is_active",
            unified_diff="--- target.py\n+++ target.py\n@@ -12,1 +12,1 @@\n-return is_admin and is_active\n+return is_admin or is_active",
            original_expression="is_admin and is_active",
            mutated_expression="is_admin or is_active"
        )
        g_logical = derive_semantic_guidance(logical_mutant)
        assert "conjunction ('and') swapped with disjunction ('or')" in g_logical.behavioral_distinction
        assert any("(True, False)" in s for s in g_logical.suggested_inputs)

    # 4. Unknown or ambiguous mutations handled safely
    def test_unknown_or_ambiguous_mutations(self):
        ambig_mutant = MutantRecord(
            mutant_id="MUT_CUSTOM_999",
            mutation_type="CUSTOM_OP_UNKNOWN",
            line_number=42,
            original_code_snippet="do_complex_thing()",
            mutated_code_snippet="do_other_thing()",
            unified_diff="--- target.py\n+++ target.py\n@@ -42,1 +42,1 @@\n-do_complex_thing()\n+do_other_thing()"
        )
        guidance = derive_semantic_guidance(ambig_mutant)
        assert guidance.confidence == "UNCERTAIN"
        assert guidance.uncertainty_note is not None
        assert "cannot be reliably inferred" in guidance.uncertainty_note

    # 5. Guidance reaching Critic and Generator context
    def test_guidance_reaches_critic_and_generator_context(self):
        mutant = MutantRecord(
            mutant_id="MUT_COMP_OP_005",
            mutation_type="COMP_OP",
            line_number=5,
            original_code_snippet="if discount > 0.0:",
            mutated_code_snippet="if discount >= 0.0:",
            unified_diff="--- target.py\n+++ target.py\n@@ -5,1 +5,1 @@\n-if discount > 0.0:\n+if discount >= 0.0:",
            original_expression="discount > 0.0",
            mutated_expression="discount >= 0.0"
        )
        critic = AdversarialCriticAgent()
        # Mock LLM client to verify deterministic offline fallback uses semantic guidance
        critic.llm_client.generate = Mock(side_effect=RuntimeError("Offline mode"))
        directives = critic.analyze_surviving_mutants(
            target_code="def f(discount):\n    if discount > 0.0:\n        return True\n    return False",
            surviving_mutant_diffs=[mutant.unified_diff],
            iteration=1,
            surviving_mutants=[mutant]
        )
        assert "Adversarial Directives:" in directives
        assert "MUT_COMP_OP_005" in directives
        assert "Line 5" in directives
        assert "Relational boundary comparison was widened" in directives

        # TestGeneratorAgent embeds guidance into prompt
        gen = TestGeneratorAgent()
        mock_generate = Mock(return_value="```python\ndef test_dummy():\n    pass\n```")
        gen.llm_client.generate = mock_generate
        code = gen.generate_tests(
            source_code="def calculate_discount(price, qty, vip):\n    return price * 0.9",
            surviving_diffs=[mutant.unified_diff],
            critic_feedback=directives,
            iteration=2,
            surviving_guidance=[derive_semantic_guidance(mutant)]
        )
        assert mock_generate.called
        call_kwargs = mock_generate.call_args[1]
        prompt_sent = call_kwargs.get("prompt", "")
        assert "MUT_COMP_OP_005" in prompt_sent
        assert "Relational boundary comparison was widened" in prompt_sent

    # 6. Blackboard and state propagation
    def test_blackboard_and_state_propagation(self):
        bb = Blackboard()
        mutant = MutantRecord(
            mutant_id="MUT_CONST_001",
            mutation_type="CONST_VAL",
            line_number=3,
            original_code_snippet="x = True",
            mutated_code_snippet="x = False",
            unified_diff="--- target.py\n+++ target.py\n@@ -3,1 +3,1 @@\n-x = True\n+x = False",
            original_expression="True",
            mutated_expression="False"
        )
        guidance = derive_semantic_guidance(mutant)
        guidance_dict = guidance.model_dump() if hasattr(guidance, "model_dump") else guidance.dict()

        # Update critic space with semantic guidance
        critic_space = bb.update_critic_space(
            latest_directive=guidance.to_directive_text(),
            critic_directives=[guidance.to_directive_text()],
            failure_mechanisms={guidance.mutant_id: guidance.behavioral_distinction},
            semantic_guidance=[guidance_dict]
        )
        assert len(critic_space.semantic_guidance) == 1
        assert critic_space.semantic_guidance[0]["mutant_id"] == "MUT_CONST_001"
        assert "MUT_CONST_001" in critic_space.failure_mechanisms

        # TestForgeState field compatibility
        state = TestForgeState()
        state.surviving_guidance = [guidance_dict]
        assert len(state.surviving_guidance) == 1
        assert state.surviving_guidance[0]["mutation_type"] == "CONST_VAL"

    # 7. M-01 fix: Custom assertion helper recognized and NOT rejected as trivial
    def test_m01_custom_assertion_helper_accepted(self, sandbox, validator):
        candidate_with_custom_helper = '''
import pytest
from target import add

def assert_valid_sum(actual, expected):
    assert actual == expected

def test_add_using_custom_helper():
    assert_valid_sum(add(5, 5), 10)
'''
        res = validator.validate_candidate_suite(
            candidate_test_code=candidate_with_custom_helper,
            target_code=CLEAN_MATH_TARGET,
            sandbox_runner=sandbox
        )
        assert res.retained_count == 1
        assert len(res.trivial_tests) == 0
        assert res.valid_tests[0].name == "test_add_using_custom_helper"
        assert res.valid_tests[0].has_meaningful_assertions is True

    # 8. M-01 preservation: Ordinary helper call without assertions is rejected
    def test_m01_ordinary_helper_without_assertions_rejected(self, sandbox, validator):
        candidate_ordinary_helper = '''
from target import add

def log_debug(message):
    pass

def test_calls_only_logging():
    log_debug(add(1, 2))
'''
        res = validator.validate_candidate_suite(
            candidate_test_code=candidate_ordinary_helper,
            target_code=CLEAN_MATH_TARGET,
            sandbox_runner=sandbox
        )
        assert res.retained_count == 0
        assert len(res.trivial_tests) == 1
        assert res.trivial_tests[0].name == "test_calls_only_logging"
        assert res.trivial_tests[0].has_meaningful_assertions is False

    # 9. No regression in granular test validation
    def test_no_regression_granular_validation(self, sandbox, validator):
        candidate_mixed = '''
from target import add, subtract

def test_valid():
    assert add(2, 3) == 5

def test_broken():
    assert subtract(10, 2) == 999
'''
        res = validator.validate_candidate_suite(
            candidate_test_code=candidate_mixed,
            target_code=CLEAN_MATH_TARGET,
            sandbox_runner=sandbox,
            existing_test_code=EXISTING_BASE_SUITE
        )
        assert res.retained_count == 1
        assert res.rejected_count == 1
        assert res.valid_tests[0].name == "test_valid"
        assert res.failing_tests[0].name == "test_broken"

    # 10. Surviving mutant killed after repair tested deterministically
    def test_surviving_mutant_killed_after_repair_deterministic(self, sandbox, validator):
        target = '''
def check_threshold(val: int) -> bool:
    if val >= 10:
        return True
    return False
'''
        mutants = ASTMutator.mutate(target)
        boundary_mutants = [m for m in mutants if m.mutation_type == "BOUNDARY_SWAP"]
        assert len(boundary_mutants) > 0
        b_mutant = boundary_mutants[0]

        # Weak test passes clean code AND survives mutated code (tested only at 5 and 20)
        weak_test = '''
from target import check_threshold

def test_weak():
    assert check_threshold(5) is False
    assert check_threshold(20) is True
'''
        weak_run = sandbox.run_single(weak_test, b_mutant.mutated_code_snippet)
        assert weak_run["status"] == "PASS", "Mutant should survive weak test suite."

        # Hardened test targeted at exact boundary 10 based on semantic guidance
        hardened_test = '''
from target import check_threshold

def test_boundary_hardened():
    assert check_threshold(10) is True
'''
        res = validator.validate_candidate_suite(
            candidate_test_code=hardened_test,
            target_code=target,
            sandbox_runner=sandbox,
            existing_test_code=weak_test,
            surviving_mutants=[b_mutant]
        )
        assert res.retained_count == 1
        assert b_mutant.mutant_id in res.mutants_killed


# ==============================================================================
# Phase 4.1.3: Step C - Benchmark Validity & Clean Reference Validation Tests
# ==============================================================================

class TestBenchmarkValidityAndCleanReferenceValidation:
    """
    Deterministic regression tests for Step C / Finding H-01:
    Verifies that mutation kills can only occur when tests pass on clean reference code,
    and that false-positive / broken candidate tests cannot artificially inflate scores.
    """

    @pytest.fixture
    def sandbox(self):
        return SubprocessSandbox(timeout_seconds=3)

    @pytest.fixture
    def validator(self):
        return GranularTestValidator()

    @pytest.fixture
    def target_and_mutant(self):
        target = (
            "def classify_number(n: int) -> str:\n"
            "    if n > 0:\n"
            "        return 'POSITIVE'\n"
            "    elif n < 0:\n"
            "        return 'NEGATIVE'\n"
            "    return 'ZERO'\n"
        )
        mutants = ASTMutator.mutate(target)
        # Find a comparison flip mutant: n > 0 -> n >= 0
        comp_mutants = [m for m in mutants if m.mutation_type == "COMP_OP" or m.mutation_type == "BOUNDARY_SWAP"]
        assert len(comp_mutants) > 0
        return target, comp_mutants[0], mutants

    # 1. Passes original and fails mutant -> COUNTS AS A KILL
    def test_pass_original_fail_mutant_counts_as_kill(self, sandbox, target_and_mutant):
        target, mutant, all_mutants = target_and_mutant
        # Valid test passing on clean code
        valid_test = (
            "from target import classify_number\n"
            "def test_zero():\n"
            "    assert classify_number(0) == 'ZERO'\n"
        )
        # Check reference pass
        ref_run = sandbox.run_single(valid_test, target)
        assert ref_run["status"] == "PASS"
        assert ref_run["tests_failed"] == 0

        # Evaluate against mutant with baseline_passed=True
        evaluated = sandbox.evaluate_mutants_parallel(
            test_code=valid_test,
            mutants=[mutant],
            baseline_passed=True
        )
        assert len(evaluated) == 1
        assert evaluated[0].status == "KILLED"
        scores = calculate_mutation_scores(evaluated)
        assert scores["killed_mutants"] == 1
        assert scores["raw_mutation_score"] == 100.0

    # 2. Fails on both original and mutant -> DOES NOT COUNT AS A KILL
    def test_fail_original_and_fail_mutant_does_not_count_as_kill(self, sandbox, target_and_mutant):
        target, mutant, all_mutants = target_and_mutant
        # Broken test that fails on clean reference code
        broken_test = (
            "from target import classify_number\n"
            "def test_hallucination():\n"
            "    assert classify_number(0) == 'NON_EXISTENT_RESULT'\n"
        )
        # Check reference fails
        ref_run = sandbox.run_single(broken_test, target)
        assert ref_run["status"] == "FAIL" or ref_run["tests_failed"] > 0
        ref_passed = (ref_run["status"] == "PASS" and ref_run["tests_failed"] == 0)
        assert ref_passed is False

        # Evaluate with explicit baseline_passed=False
        evaluated = sandbox.evaluate_mutants_parallel(
            test_code=broken_test,
            mutants=[mutant],
            baseline_passed=ref_passed
        )
        assert len(evaluated) == 1
        assert evaluated[0].status == "ERROR"
        assert evaluated[0].status != "KILLED"
        scores = calculate_mutation_scores(evaluated)
        assert scores["killed_mutants"] == 0
        assert scores["raw_mutation_score"] == 0.0

    # 3. Mixture of valid and false-positive tests retains valid tests only
    def test_mixture_valid_and_false_positive_retains_valid_only(self, sandbox, validator, target_and_mutant):
        target, mutant, all_mutants = target_and_mutant
        mixed_candidate_suite = (
            "from target import classify_number\n\n"
            "def test_clean_valid():\n"
            "    assert classify_number(0) == 'ZERO'\n\n"
            "def test_hallucinated_false_positive():\n"
            "    assert classify_number(10) == 'BOGUS_STRING'\n"
        )
        val_res = validator.validate_candidate_suite(
            candidate_test_code=mixed_candidate_suite,
            target_code=target,
            sandbox_runner=sandbox
        )
        assert val_res.total_candidates == 2
        assert val_res.retained_count == 1
        assert val_res.rejected_count == 1
        assert val_res.valid_tests[0].name == "test_clean_valid"
        assert val_res.failing_tests[0].name == "test_hallucinated_false_positive"

        # The retained code only contains the valid test
        assert "test_clean_valid" in val_res.retained_test_code
        assert "test_hallucinated_false_positive" not in val_res.retained_test_code

        # Running evaluated mutants with retained code gives true kills
        evaluated = sandbox.evaluate_mutants_parallel(
            test_code=val_res.retained_test_code,
            mutants=[mutant],
            baseline_passed=True
        )
        assert evaluated[0].status == "KILLED"

    # 4. Clean reference timeout or infrastructure error does not count as a kill
    def test_clean_reference_timeout_or_error_does_not_count_as_kill(self, sandbox, target_and_mutant):
        target, mutant, all_mutants = target_and_mutant
        # Infinite loop test
        looping_test = (
            "from target import classify_number\n"
            "def test_hang():\n"
            "    while True:\n"
            "        pass\n"
        )
        val_res = GranularTestValidator().validate_candidate_suite(
            candidate_test_code=looping_test,
            target_code=target,
            sandbox_runner=sandbox,
            timeout_seconds=2
        )
        assert val_res.retained_count == 0
        ref_passed = (val_res.retained_count > 0 and bool(val_res.retained_test_code))
        assert ref_passed is False

        evaluated = sandbox.evaluate_mutants_parallel(
            test_code=val_res.retained_test_code,
            mutants=[mutant],
            baseline_passed=ref_passed
        )
        assert evaluated[0].status in ("ERROR", "SURVIVED")
        assert evaluated[0].status != "KILLED"
        scores = calculate_mutation_scores(evaluated)
        assert scores["killed_mutants"] == 0

    # 5. Empty or fully rejected suite produces zero score without misleading results
    def test_empty_or_fully_rejected_suite_produces_zero_score(self, sandbox, target_and_mutant):
        target, mutant, all_mutants = target_and_mutant
        # Completely empty test code
        evaluated_empty = sandbox.evaluate_mutants_parallel(
            test_code="",
            mutants=[mutant],
            baseline_passed=False
        )
        scores_empty = calculate_mutation_scores(evaluated_empty)
        assert scores_empty["killed_mutants"] == 0
        assert scores_empty["raw_mutation_score"] == 0.0

        # All-failing suite
        all_failing_suite = (
            "from target import classify_number\n"
            "def test_fail_1(): assert False\n"
            "def test_fail_2(): assert False\n"
        )
        val_res = GranularTestValidator().validate_candidate_suite(
            candidate_test_code=all_failing_suite,
            target_code=target,
            sandbox_runner=sandbox
        )
        assert val_res.retained_count == 0
        assert val_res.retained_test_code == ""
        evaluated_rejected = sandbox.evaluate_mutants_parallel(
            test_code=val_res.retained_test_code,
            mutants=[mutant],
            baseline_passed=(val_res.retained_count > 0)
        )
        scores_rejected = calculate_mutation_scores(evaluated_rejected)
        assert scores_rejected["killed_mutants"] == 0
        assert scores_rejected["raw_mutation_score"] == 0.0

    # 6. Baseline, zero-shot, and agentic reflection strategies use comparable validation rules
    def test_all_strategies_use_comparable_validation_rules(self):
        from testforge.corpus.models import CorpusFixture
        from testforge.corpus.runner import CorpusBenchmarkRunner

        fixture = CorpusFixture(
            fixture_id="mini_calc",
            name="Mini Calc",
            description="Minimal deterministic fixture for testing runner contracts",
            category="Math",
            source_file="samples/calc.py",
            source_code="def calc(x: int) -> int:\n    if x > 5:\n        return x * 2\n    return x\n",
            function_contract="calc(x: int) -> int",
            baseline_test_code="from target import calc\ndef test_baseline():\n    assert calc(6) == 12\n    assert calc(3) == 3\n",
            defects={}
        )

        runner = CorpusBenchmarkRunner(fast_mode=False)
        # Execute baseline
        rec_base = runner._execute_strategy_run(
            fixture=fixture,
            scenario="baseline",
            run_id="run_test_base",
            rep_index=1,
            has_api_key=False
        )
        # In baseline, all tests pass reference code
        assert rec_base.tests_collected > 0
        assert rec_base.tests_passed_on_reference == rec_base.tests_collected
        assert rec_base.tests_failed_on_reference == 0
        assert rec_base.false_positive_rate_pct == 0.0
        # Mutants killed must be > 0 (calc(6)==12 kills x > 5 and x * 2 mutants)
        assert rec_base.mutants_killed > 0
        assert rec_base.mutation_score_pct > 0.0


class TestAgenticReflectionQualityRemediation:
    """
    Phase 5.2 Quality Remediation Regression Tests:
    1. Pass 0 valid, Pass 1 invalid preserves Pass 0 suite and baseline validity.
    2. Pass 0 valid, Pass 1 empty preserves Pass 0 suite.
    3. Pass 0 invalid, Pass 1 valid adopts valid Pass 1 tests.
    4. Both passes invalid yields 0 kills and False baseline validity.
    5. Preserved suite genuinely kills mutants.
    6. Currency converter deterministic fallback passes clean reference code.
    7. Quarantined test failure feedback is formatted into generator prompt.
    """
    @pytest.fixture
    def sandbox(self):
        return SubprocessSandbox(timeout_seconds=5)

    @pytest.fixture
    def validator(self):
        return GranularTestValidator()

    # 1. Pass 0 valid, Pass 1 invalid preserves Pass 0 suite
    def test_pass0_valid_pass1_invalid_preserves_pass0_suite(self, sandbox, validator):
        target = "def calc(x: int) -> int:\n    return x * 10\n"
        pass0_code = "from target import calc\ndef test_pass0():\n    assert calc(2) == 20\n"
        pass1_broken = "from target import calc\ndef test_pass1():\n    assert calc(2) == 9999\n"

        val_pass0 = validator.validate_candidate_suite(pass0_code, target, sandbox_runner=sandbox)
        assert val_pass0.retained_count == 1
        clean_v0 = val_pass0.retained_test_code

        val_pass1 = validator.validate_candidate_suite(
            candidate_test_code=pass1_broken,
            target_code=target,
            sandbox_runner=sandbox,
            existing_test_code=clean_v0
        )
        assert val_pass1.retained_count == 0  # Pass 1 alone had 0 valid tests
        # Crucial preservation contract: retained_test_code falls back to existing suite clean_v0
        assert val_pass1.retained_test_code == clean_v0
        assert "test_pass0" in val_pass1.retained_test_code

    # 2. Pass 0 valid, Pass 1 empty preserves Pass 0 suite
    def test_pass0_valid_pass1_empty_preserves_pass0_suite(self, sandbox, validator):
        target = "def calc(x: int) -> int:\n    return x + 5\n"
        clean_v0 = "from target import calc\ndef test_pass0():\n    assert calc(5) == 10\n"

        val_pass1 = validator.validate_candidate_suite(
            candidate_test_code="",
            target_code=target,
            sandbox_runner=sandbox,
            existing_test_code=clean_v0
        )
        assert val_pass1.retained_test_code == clean_v0
        assert "test_pass0" in val_pass1.retained_test_code

    # 3. Pass 0 invalid, Pass 1 valid adopts valid Pass 1 tests
    def test_pass0_invalid_pass1_valid_adopts_valid_pass1(self, sandbox, validator):
        target = "def calc(x: int) -> int:\n    return x * 3\n"
        pass0_broken = "from target import calc\ndef test_pass0():\n    assert calc(2) == 999\n"
        pass1_valid = "from target import calc\ndef test_pass1():\n    assert calc(2) == 6\n"

        val_pass0 = validator.validate_candidate_suite(pass0_broken, target, sandbox_runner=sandbox)
        assert val_pass0.retained_count == 0
        clean_v0 = val_pass0.retained_test_code  # empty string

        val_pass1 = validator.validate_candidate_suite(
            candidate_test_code=pass1_valid,
            target_code=target,
            sandbox_runner=sandbox,
            existing_test_code=clean_v0
        )
        assert val_pass1.retained_count == 1
        assert "test_pass1" in val_pass1.retained_test_code

    # 4. Both passes invalid yields 0 kills and False baseline validity
    def test_both_passes_invalid_yields_zero_kills(self, sandbox, validator):
        target = "def calc(x: int) -> int:\n    return x * 2\n"
        pass0_broken = "from target import calc\ndef test_pass0():\n    assert calc(2) == 999\n"
        pass1_broken = "from target import calc\ndef test_pass1():\n    assert calc(2) == 888\n"

        val_pass0 = validator.validate_candidate_suite(pass0_broken, target, sandbox_runner=sandbox)
        clean_v0 = val_pass0.retained_test_code  # empty

        val_pass1 = validator.validate_candidate_suite(
            candidate_test_code=pass1_broken,
            target_code=target,
            sandbox_runner=sandbox,
            existing_test_code=clean_v0
        )
        final_code = val_pass1.retained_test_code if (val_pass1.retained_test_code and val_pass1.retained_test_code.strip()) else clean_v0
        assert not final_code or not final_code.strip()

        # Mutant evaluation with empty code must yield 0 kills
        mutants = ASTMutator.mutate(target)
        eval_res = sandbox.evaluate_mutants_parallel(final_code, mutants, baseline_passed=False)
        killed = sum(1 for m in eval_res if m.status == "KILLED")
        assert killed == 0

    # 5. Preserved suite genuinely kills mutants
    def test_preserved_suite_genuinely_kills_mutants(self, sandbox, validator):
        target = "def calc(x: int) -> int:\n    if x > 5:\n        return x * 2\n    return x\n"
        pass0_code = "from target import calc\ndef test_pass0():\n    assert calc(6) == 12\n"
        pass1_broken = "from target import calc\ndef test_broken():\n    assert calc(6) == 999\n"

        val_pass0 = validator.validate_candidate_suite(pass0_code, target, sandbox_runner=sandbox)
        clean_v0 = val_pass0.retained_test_code

        val_pass1 = validator.validate_candidate_suite(
            candidate_test_code=pass1_broken,
            target_code=target,
            sandbox_runner=sandbox,
            existing_test_code=clean_v0
        )
        test_code_to_eval = val_pass1.retained_test_code if val_pass1.retained_test_code.strip() else clean_v0
        assert "test_pass0" in test_code_to_eval

        # Must cleanly kill the x * 2 mutant
        mutants = ASTMutator.mutate(target)
        eval_res = sandbox.evaluate_mutants_parallel(test_code_to_eval, mutants, baseline_passed=True)
        killed = sum(1 for m in eval_res if m.status == "KILLED")
        assert killed > 0

    # 6. Currency converter deterministic fallback passes clean reference code
    def test_currency_converter_fallback_passes_clean_reference(self, sandbox):
        from testforge.agents import CodeSanitizer, TestGeneratorAgent, extract_function_signatures
        from testforge.corpus.fixtures.currency_converter import REFERENCE_CODE

        gen = TestGeneratorAgent(model_name="Local Ollama:qwen2.5-coder:7b", api_key="")
        sigs = extract_function_signatures(REFERENCE_CODE)
        
        # Iteration 0 baseline fallback
        raw_v0 = gen._synthesize_ast_aware_tests(REFERENCE_CODE, sigs, surviving_diffs=None)
        extracted_v0 = CodeSanitizer.extract_and_validate(raw_v0)[1]
        val_v0 = sandbox.validate_and_filter_candidate_suite(extracted_v0, REFERENCE_CODE)
        assert val_v0.retained_count > 0
        assert val_v0.rejected_count == 0

        # Iteration 1 hardened fallback
        raw_v1 = gen._synthesize_ast_aware_tests(REFERENCE_CODE, sigs, surviving_diffs=["diff sample"])
        extracted_v1 = CodeSanitizer.extract_and_validate(raw_v1)[1]
        val_v1 = sandbox.validate_and_filter_candidate_suite(extracted_v1, REFERENCE_CODE)
        assert val_v1.retained_count > 0
        assert val_v1.rejected_count == 0

    # 7. Quarantined test failure feedback is formatted into generator prompt
    def test_quarantined_test_feedback_formatted_into_prompt(self):
        from testforge.agents import TestGeneratorAgent
        from testforge.sandbox import TestFunctionRecord, TestValidationStatus

        fake_quarantined = [
            TestFunctionRecord(
                name="test_broken_calc",
                code="assert calc(2) == 999",
                status=TestValidationStatus.FAILING,
                reason="AssertionError: assert 4 == 999"
            )
        ]

        class CapturingLLM:
            def __init__(self):
                self.last_prompt = ""
                self.active_provider = "Mock"
            def generate(self, prompt, **kwargs):
                self.last_prompt = prompt
                return "```python\nfrom target import calc\ndef test_ok():\n    assert calc(2) == 4\n```"

        mock_llm = CapturingLLM()
        gen = TestGeneratorAgent(model_name="mock", llm_client=mock_llm)
        gen.generate_tests(
            source_code="def calc(x: int) -> int:\n    return x * 2\n",
            iteration=1,
            quarantined_tests=fake_quarantined
        )
        assert "Quarantined Candidate Tests" in mock_llm.last_prompt
        assert "test_broken_calc" in mock_llm.last_prompt
        assert "AssertionError: assert 4 == 999" in mock_llm.last_prompt



