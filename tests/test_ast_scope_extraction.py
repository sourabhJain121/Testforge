"""
tests/test_ast_scope_extraction.py - Targeted regression test suite for lexical AST scope
and signature extraction across module functions, static methods, class methods,
instance methods, and nested closures.
"""

import json

import pytest

from testforge.adk_generator import ADKModelBridge
from testforge.agents import CodeSanitizer, TestGeneratorAgent, build_nominal_arguments, extract_function_signatures
from testforge.sandbox import ParallelSandboxRunner


def generate_tests_for_code(code: str) -> str:
    bridge = ADKModelBridge(api_key="")
    prompt = f"```python\n{code}\n```"
    raw_json = bridge._synthesize_deterministic_tests(prompt)
    data = json.loads(raw_json)
    return data["test_code"]


# ==============================================================================
# 1. TOP-LEVEL MODULE FUNCTION EXTRACTION
# ==============================================================================

def test_top_level_function_extraction():
    code = """
def calculate_subtotal(unit_price: float, quantity: int = 1) -> float:
    \"\"\"Calculates subtotal.\"\"\"
    return unit_price * quantity
"""
    sigs = extract_function_signatures(code)
    assert len(sigs) == 1
    sig = sigs[0]

    assert sig["name"] == "calculate_subtotal"
    assert sig["qualified_name"] == "calculate_subtotal"
    assert sig["scope"] == "module"
    assert sig["parent_class"] is None
    assert sig["parent_function"] is None
    assert sig["is_method"] is False
    assert sig["method_type"] is None
    assert sig["required_pos"] == ["unit_price"]
    assert sig["optional_pos"] == ["quantity"]

    test_code = generate_tests_for_code(code)
    assert "from target import calculate_subtotal" in test_code
    assert "test_calculate_subtotal_nominal" in test_code


# ==============================================================================
# 2. INSTANCE METHOD EXTRACTION
# ==============================================================================

def test_instance_method_extraction():
    code = """
class OrderAccount:
    def __init__(self, account_id: str):
        self.account_id = account_id

    def deposit(self, amount: float) -> bool:
        return amount > 0
"""
    sigs = extract_function_signatures(code)
    method_sigs = [s for s in sigs if s["name"] == "deposit"]
    assert len(method_sigs) == 1
    sig = method_sigs[0]

    assert sig["name"] == "deposit"
    assert sig["qualified_name"] == "OrderAccount.deposit"
    assert sig["scope"] == "class"
    assert sig["parent_class"] == "OrderAccount"
    assert sig["is_method"] is True
    assert sig["method_type"] == "instance"
    assert sig["pos_args"] == ["amount"]  # 'self' must be stripped
    assert sig["required_pos"] == ["amount"]

    test_code = generate_tests_for_code(code)
    # Must NOT attempt to import instance method directly as a module function
    assert "from target import deposit" not in test_code


# ==============================================================================
# 3. STATIC METHOD EXTRACTION
# ==============================================================================

def test_static_method_extraction():
    code = """
class TaxCalculator:
    @staticmethod
    def compute_sales_tax(amount: float, rate: float = 0.05) -> float:
        return amount * rate
"""
    sigs = extract_function_signatures(code)
    assert len(sigs) == 1
    sig = sigs[0]

    assert sig["name"] == "compute_sales_tax"
    assert sig["qualified_name"] == "TaxCalculator.compute_sales_tax"
    assert sig["scope"] == "class"
    assert sig["parent_class"] == "TaxCalculator"
    assert sig["is_method"] is True
    assert sig["method_type"] == "staticmethod"
    assert "staticmethod" in sig["decorators"]
    assert sig["required_pos"] == ["amount"]

    test_code = generate_tests_for_code(code)
    assert "from target import TaxCalculator" in test_code
    assert "TaxCalculator.compute_sales_tax" in test_code
    assert "from target import compute_sales_tax" not in test_code


# ==============================================================================
# 4. CLASS METHOD EXTRACTION
# ==============================================================================

def test_class_method_extraction():
    code = """
class SessionConfig:
    @classmethod
    def default_config(cls, env: str = "prod"):
        return {"env": env}
"""
    sigs = extract_function_signatures(code)
    assert len(sigs) == 1
    sig = sigs[0]

    assert sig["name"] == "default_config"
    assert sig["qualified_name"] == "SessionConfig.default_config"
    assert sig["scope"] == "class"
    assert sig["parent_class"] == "SessionConfig"
    assert sig["is_method"] is True
    assert sig["method_type"] == "classmethod"
    assert "classmethod" in sig["decorators"]
    assert sig["pos_args"] == ["env"]  # 'cls' must be stripped

    test_code = generate_tests_for_code(code)
    assert "from target import SessionConfig" in test_code
    assert "SessionConfig.default_config" in test_code
    assert "from target import default_config" not in test_code


# ==============================================================================
# 5. NESTED FUNCTION HANDLING
# ==============================================================================

def test_nested_function_handling():
    code = """
def outer_pipeline(data: list) -> list:
    def _inner_filter(item):
        return item is not None
    return [_inner_filter(x) for x in data]
"""
    sigs = extract_function_signatures(code)
    assert len(sigs) == 2

    outer_sig = next(s for s in sigs if s["name"] == "outer_pipeline")
    inner_sig = next(s for s in sigs if s["name"] == "_inner_filter")

    assert outer_sig["scope"] == "module"
    assert outer_sig["parent_class"] is None
    assert outer_sig["parent_function"] is None

    assert inner_sig["scope"] == "nested"
    assert inner_sig["parent_function"] == "outer_pipeline"
    assert inner_sig["qualified_name"] == "outer_pipeline.<locals>._inner_filter"
    assert inner_sig["is_method"] is False

    test_code = generate_tests_for_code(code)
    # Must target outer_pipeline and NEVER attempt to import inner helper
    assert "from target import outer_pipeline" in test_code
    assert "from target import _inner_filter" not in test_code


# ==============================================================================
# 6. DECORATED METHODS AND PROPERTIES
# ==============================================================================

def test_decorated_methods_and_properties():
    code = """
class SystemHealth:
    @property
    def is_alive(self) -> bool:
        return True

    @property
    def load_factor(self) -> float:
        return 0.5
"""
    sigs = extract_function_signatures(code)
    assert len(sigs) == 2
    for sig in sigs:
        assert sig["scope"] == "class"
        assert sig["method_type"] == "property"
        assert "property" in sig["decorators"]
        assert sig["is_method"] is True

    # build_nominal_arguments must return None for property getters
    for sig in sigs:
        assert build_nominal_arguments(sig) is None


# ==============================================================================
# 7. MULTI-ARGUMENT FUNCTION SIGNATURES
# ==============================================================================

def test_multi_argument_function_signatures():
    code = """
def dispatch_shipment(origin: str, destination: str, weight_kg: float, express: bool = False) -> str:
    return f"{origin}->{destination}:{weight_kg}"
"""
    sigs = extract_function_signatures(code)
    sig = sigs[0]

    assert sig["required_pos"] == ["origin", "destination", "weight_kg"]
    assert sig["optional_pos"] == ["express"]

    nominal = build_nominal_arguments(sig)
    assert nominal is not None
    assert '"US"' in nominal or '"test"' in nominal
    assert "10.0" in nominal

    test_code = generate_tests_for_code(code)
    assert "from target import dispatch_shipment" in test_code
    assert "multi_arg_scenario" in test_code


# ==============================================================================
# 8. KEYWORD-ONLY ARGUMENT HANDLING
# ==============================================================================

def test_keyword_only_argument_handling():
    code = """
def secure_hash(payload: str, *, salt: str, iterations: int = 1000) -> str:
    return payload + salt
"""
    sigs = extract_function_signatures(code)
    sig = sigs[0]

    assert sig["required_pos"] == ["payload"]
    assert sig["required_kwonly"] == ["salt"]
    assert sig["kwonly_args"] == ["salt", "iterations"]

    nominal = build_nominal_arguments(sig)
    assert "salt=" in nominal


# ==============================================================================
# 9. PREPAREDREQUEST._ENCODE_PARAMS SPECIFIC REGRESSION TEST
# ==============================================================================

def test_prepared_request_encode_params_regression():
    """
    Verifies that for classes with static methods like PreparedRequest._encode_params:
    1. Scope is correctly identified as 'class' with parent 'PreparedRequest'.
    2. method_type is identified as 'staticmethod'.
    3. Generator imports the class, NOT the static method directly.
    4. Pytest executes without ImportError.
    """
    code = """
class PreparedRequest:
    @staticmethod
    def _encode_params(data: str) -> str:
        if isinstance(data, str):
            return data
        return str(data)
"""
    sigs = extract_function_signatures(code)
    assert len(sigs) == 1
    sig = sigs[0]

    assert sig["name"] == "_encode_params"
    assert sig["qualified_name"] == "PreparedRequest._encode_params"
    assert sig["scope"] == "class"
    assert sig["parent_class"] == "PreparedRequest"
    assert sig["is_method"] is True
    assert sig["method_type"] == "staticmethod"

    test_code = generate_tests_for_code(code)

    # STRICT ASSERTIONS:
    # Must NOT attempt to import _encode_params from target
    assert "from target import _encode_params" not in test_code
    # Must import PreparedRequest
    assert "from target import PreparedRequest" in test_code
    # Must access via PreparedRequest._encode_params
    assert "PreparedRequest._encode_params" in test_code

    # Verify that the generated test executes cleanly against the target code in sandbox
    runner = ParallelSandboxRunner(timeout_seconds=5)
    res = runner.run_single(test_code, code)
    assert res["status"] == "PASS"
    assert res["tests_passed"] >= 1
    assert res["exit_code"] == 0
