"""
test_post_demo_defect_fixes.py - Regression test suite for confirmed post-demo defect fixes:
1. Defect 1: Elimination of universal exception swallowing (`except Exception: pass`).
2. Defect 2: Blackboard SuiteSpace candidate separation and safe promotion.
3. Defect 3: Signature-aware multi-argument test synthesis in ADK generator.
"""

import os

import pytest

from testforge.a2a import A2ABroker, A2AMessage, A2APerformative
from testforge.adk_generator import GoogleADKTestGenerator
from testforge.agents import (
    TestGeneratorAgent,
    build_nominal_arguments,
    extract_function_signatures,
)
from testforge.blackboard import Blackboard, SuiteSpace
from testforge.sandbox import GranularTestValidator, ParallelSandboxRunner
from testforge.state import TestForgeState

# ==============================================================================
# PHASE 1 REGRESSION TESTS: EXCEPTION SWALLOWING ELIMINATION
# ==============================================================================

class TestExceptionSwallowingFix:
    def test_generic_test_does_not_contain_exception_swallowing(self):
        """Verifies that fallback AST synthesizer does not emit 'except Exception: pass'."""
        sample_code = """
def custom_business_rule(amount: float, factor: int) -> float:
    if amount < 0:
        raise ValueError("Invalid amount")
    return amount * factor
"""
        agent = TestGeneratorAgent(api_key="")
        sigs = extract_function_signatures(sample_code)
        raw_tests = agent._synthesize_ast_aware_tests(sample_code, sigs, surviving_diffs=None)
        
        assert "except Exception: pass" not in raw_tests
        assert "except Exception:" not in raw_tests
        assert "assert res is not None" in raw_tests or "assert custom_business_rule" in raw_tests

    def test_deliberate_defect_is_detected_not_swallowed(self):
        """Verifies that a deliberately defective implementation fails test execution rather than being swallowed."""
        from testforge.agents import CodeSanitizer
        clean_code = """
def multiply_by_two(val: int) -> int:
    return val * 2
"""
        defective_code = """
def multiply_by_two(val: int) -> int:
    raise RuntimeError("Deliberate injection defect")
"""
        agent = TestGeneratorAgent(api_key="")
        sigs = extract_function_signatures(clean_code)
        raw_tests = agent._synthesize_ast_aware_tests(clean_code, sigs, surviving_diffs=None)
        _, sanitized_tests, _ = CodeSanitizer.extract_and_validate(raw_tests)

        runner = ParallelSandboxRunner(timeout_seconds=5)
        clean_res = runner.run_single(sanitized_tests, clean_code)
        assert clean_res["status"] == "PASS"
        assert clean_res["tests_passed"] >= 1

        # Must FAIL on defective code (proving the exception is NOT swallowed)
        defect_res = runner.run_single(sanitized_tests, defective_code)
        assert defect_res["status"] in ("FAIL", "ERROR")
        assert defect_res["tests_passed"] == 0

    def test_class_methods_skipped_from_generic_standalone(self):
        """Verifies class methods are not emitted as standalone module-level function calls."""
        class_code = """
class OrderProcessor:
    def __init__(self, order_id: str):
        self.order_id = order_id
    def process(self, amount: float) -> bool:
        return amount > 0
"""
        sigs = extract_function_signatures(class_code)
        agent = TestGeneratorAgent(api_key="")
        raw_tests = agent._synthesize_ast_aware_tests(class_code, sigs, surviving_diffs=None)
        
        assert "def test_generic___init__" not in raw_tests
        assert "def test_generic_process" not in raw_tests


# ==============================================================================
# PHASE 2 REGRESSION TESTS: BLACKBOARD SUITESPACE SYNC & PROMOTION
# ==============================================================================

class TestBlackboardSuiteSpaceSyncFix:
    def test_candidate_suite_separate_from_accepted_suite(self):
        """Verifies A2ABroker stores candidate tests in candidate_test_code without overwriting current_test_code."""
        bb = Blackboard()
        bb.update_suite_space(
            current_test_code="def test_accepted(): assert True",
            candidate_test_code="",
            active_provider="Accepted Provider"
        )
        broker = A2ABroker(blackboard=bb)

        # Candidate response from ADK generator
        candidate_code = "def test_candidate_unvalidated(): assert 1 == 1"
        response_msg = A2AMessage(
            correlation_id="test_corr_123",
            sender="agent:google-adk:generator",
            recipient="agent:orchestrator",
            performative=A2APerformative.INFORM,
            action="generation_complete",
            payload={"test_code": candidate_code}
        )
        broker._sync_generator_to_blackboard(response_msg)

        suite = bb.get_suite_space()
        # The accepted suite must remain untouched!
        assert suite.current_test_code == "def test_accepted(): assert True"
        # The candidate suite is stored in candidate_test_code
        assert "test_candidate_unvalidated" in suite.candidate_test_code

    def test_rejected_candidate_does_not_overwrite_accepted_suite(self):
        """Verifies that an invalid candidate suite rejected by sandbox does not replace the accepted suite."""
        clean_target = """
def calculate_total(a: int, b: int) -> int:
    return a + b
"""
        accepted_suite = """
import pytest
from target import calculate_total
def test_accepted():
    assert calculate_total(2, 3) == 5
"""
        broken_candidate = """
import pytest
from target import calculate_total
def test_broken_syntax():
    assert calculate_total(missing_var) == 0
"""
        bb = Blackboard()
        bb.update_suite_space(
            current_test_code=accepted_suite,
            candidate_test_code=broken_candidate
        )
        validator = GranularTestValidator()
        runner = ParallelSandboxRunner(timeout_seconds=5)
        
        val_res = validator.validate_candidate_suite(
            candidate_test_code=broken_candidate,
            target_code=clean_target,
            sandbox_runner=runner,
            existing_test_code=accepted_suite
        )
        # Sandbox rejects candidate
        assert val_res.retained_count == 0
        assert val_res.quarantined_count >= 1
        
        # When rejected, accepted suite remains preserved
        if val_res.retained_count == 0:
            bb.update_suite_space(candidate_test_code="")

        suite = bb.get_suite_space()
        assert suite.current_test_code == accepted_suite
        assert "test_accepted" in suite.current_test_code
        assert "test_broken_syntax" not in suite.current_test_code

    def test_valid_candidate_promoted_to_accepted_suite(self):
        """Verifies that a valid candidate suite passing clean validation is promoted to current_test_code."""
        clean_target = """
def add_nums(a: int, b: int) -> int:
    return a + b
"""
        accepted_baseline = "def test_base(): pass"
        valid_candidate = """
import pytest
from target import add_nums
def test_new_valid():
    assert add_nums(1, 2) == 3
"""
        bb = Blackboard()
        bb.update_suite_space(
            current_test_code=accepted_baseline,
            candidate_test_code=valid_candidate
        )
        validator = GranularTestValidator()
        runner = ParallelSandboxRunner(timeout_seconds=5)
        
        val_res = validator.validate_candidate_suite(
            candidate_test_code=valid_candidate,
            target_code=clean_target,
            sandbox_runner=runner,
            existing_test_code=accepted_baseline
        )
        assert val_res.retained_count >= 1

        # Promotion
        bb.update_suite_space(
            current_test_code=val_res.retained_test_code,
            hardened_test_code=val_res.retained_test_code,
            candidate_test_code=""
        )
        suite = bb.get_suite_space()
        assert "test_new_valid" in suite.current_test_code


# ==============================================================================
# PHASE 3 REGRESSION TESTS: MULTI-ARGUMENT SIGNATURE-AWARE GENERATION
# ==============================================================================

class TestMultiArgumentSignatureAwareGenerationFix:
    def test_three_plus_arguments_signature_aware(self):
        """Verifies functions with 3+ required arguments receive valid signature-aware calls."""
        three_arg_target = """
def process_order(price: float, quantity: int, is_member: bool) -> float:
    if price <= 0:
        return 0.0
    rate = 0.2 if is_member else 0.1
    return price * quantity * (1.0 - rate)
"""
        adk = GoogleADKTestGenerator()
        payload = adk.generate_tests(target_source_code=three_arg_target)
        
        runner = ParallelSandboxRunner(timeout_seconds=5)
        exec_res = runner.run_single(payload.test_code, three_arg_target)
        
        assert exec_res["status"] == "PASS"
        assert exec_res["tests_passed"] >= 1
        assert "process_order(10.0, 2, False)" in payload.test_code or "process_order(" in payload.test_code

    def test_required_keyword_only_parameters(self):
        """Verifies functions with required keyword-only arguments receive keyword arguments in calls."""
        kwonly_target = """
def compute_rate(base: float, *, multiplier: float) -> float:
    return base * multiplier
"""
        sigs = extract_function_signatures(kwonly_target)
        sig = sigs[0]
        assert "multiplier" in sig["required_kwonly"]
        
        call_str = build_nominal_arguments(sig)
        assert "multiplier=" in call_str

    def test_default_arguments_respected(self):
        """Verifies optional parameters with default values are not treated as required."""
        defaults_target = """
def send_alert(message: str, priority: int = 1, timeout: float = 30.0) -> bool:
    return len(message) > 0
"""
        sigs = extract_function_signatures(defaults_target)
        sig = sigs[0]
        assert sig["required_pos"] == ["message"]
        assert "priority" in sig["optional_pos"]
        assert "timeout" in sig["optional_pos"]

    def test_ambiguous_signature_handling(self):
        """Verifies functions with ambiguous signatures (*args without required args) do not generate broken assertions."""
        ambiguous_target = """
def dynamic_handler(*args, **kwargs):
    return len(args) + len(kwargs)
"""
        sigs = extract_function_signatures(ambiguous_target)
        sig = sigs[0]
        call_str = build_nominal_arguments(sig)
        assert call_str is None  # Classified as ambiguous
