"""
tests/test_multi_file_dependency_hardening.py - Multi-File Dependency-Aware Hardening Verification Suite.

Tests local sibling AST import resolution, compact symbol extraction, isolated sandbox mounting,
and end-to-end multi-file orchestration under DEF-022 clean-code verification.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

from testforge.dependency_resolver import (
    DependencyBundle,
    MultiFileDependencyResolver,
    resolve_dependencies_for_file,
)
from testforge.orchestrator import TestForgeOrchestrator
from testforge.sandbox import ParallelSandboxRunner


# ==============================================================================
# 1. Dependency Resolver Unit & AST Extraction Tests
# ==============================================================================

def test_dependency_resolver_extracts_local_imports_and_ignores_stdlib():
    with tempfile.TemporaryDirectory(prefix="testforge_dep_test_") as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Companion 1: models.py
        models_code = (
            "from dataclasses import dataclass\n"
            "from typing import Optional\n"
            "\n"
            "@dataclass\n"
            "class CustomerRecord:\n"
            "    customer_id: str\n"
            "    tier: str = 'standard'\n"
            "    is_active: bool = True\n"
            "\n"
            "def validate_customer_id(cid: str) -> bool:\n"
            "    return bool(cid and cid.startswith('CUST-'))\n"
        )
        (tmp_path / "models.py").write_text(models_code, encoding="utf-8")
        
        # Companion 2: tax_calc.py
        tax_code = (
            "TAX_RATE = 0.0825\n"
            "\n"
            "def compute_tax(subtotal: float) -> float:\n"
            "    return round(subtotal * TAX_RATE, 2)\n"
        )
        (tmp_path / "tax_calc.py").write_text(tax_code, encoding="utf-8")

        # Primary: service.py (imports stdlib + local sibling modules)
        service_code = (
            "import os\n"
            "import json\n"
            "from typing import List, Dict, Any\n"
            "import models\n"
            "from tax_calc import compute_tax\n"
            "\n"
            "def process_order(customer_id: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:\n"
            "    if not models.validate_customer_id(customer_id):\n"
            "        raise ValueError('Invalid customer ID format')\n"
            "    subtotal = sum(i.get('price', 0.0) * i.get('qty', 1) for i in items)\n"
            "    tax = compute_tax(subtotal)\n"
            "    return {'customer_id': customer_id, 'subtotal': subtotal, 'tax': tax, 'total': round(subtotal + tax, 2)}\n"
        )
        service_file = tmp_path / "service.py"
        service_file.write_text(service_code, encoding="utf-8")

        # Resolve dependencies
        resolver = MultiFileDependencyResolver(search_roots=[tmp_path])
        bundle = resolver.resolve_local_dependencies(str(service_file), service_code)

        # Assertions
        assert isinstance(bundle, DependencyBundle)
        assert bundle.primary_filename == "service.py"
        # Ignored stdlib: os, json, typing
        assert "os" not in bundle.companion_files
        assert "json" not in bundle.companion_files
        assert "typing" not in bundle.companion_files
        
        # Captured sibling modules
        assert "models.py" in bundle.companion_files
        assert "tax_calc.py" in bundle.companion_files
        assert "CustomerRecord" in bundle.resolved_symbols
        assert "validate_customer_id" in bundle.resolved_symbols
        assert "compute_tax" in bundle.resolved_symbols

        # Prompt formatting context includes signatures
        ctx = bundle.format_prompt_context()
        assert "models.py" in ctx
        assert "tax_calc.py" in ctx
        assert "def compute_tax(subtotal: float) -> float:" in ctx
        assert "class CustomerRecord:" in ctx


def test_dependency_resolver_handles_cycles_without_infinite_recursion():
    with tempfile.TemporaryDirectory(prefix="testforge_dep_cycle_") as tmpdir:
        tmp_path = Path(tmpdir)

        # module_a imports module_b; module_b imports module_a
        mod_a = (
            "import module_b\n"
            "def foo():\n"
            "    return module_b.bar()\n"
        )
        mod_b = (
            "import module_a\n"
            "def bar():\n"
            "    return 42\n"
        )
        (tmp_path / "module_a.py").write_text(mod_a, encoding="utf-8")
        (tmp_path / "module_b.py").write_text(mod_b, encoding="utf-8")

        resolver = MultiFileDependencyResolver(search_roots=[tmp_path], max_depth=3)
        bundle = resolver.resolve_local_dependencies(str(tmp_path / "module_a.py"), mod_a)

        assert "module_b.py" in bundle.companion_files
        assert "bar" in bundle.resolved_symbols


# ==============================================================================
# 2. Isolated Multi-File Sandbox Execution Tests
# ==============================================================================

def test_multi_file_sandbox_runner_mounts_companions():
    helper_code = (
        "def helper_compute(val: int) -> int:\n"
        "    return val * 10 + 5\n"
    )
    target_code = (
        "import helper\n"
        "def main_calc(x: int) -> int:\n"
        "    if x <= 0:\n"
        "        return 0\n"
        "    return helper.helper_compute(x)\n"
    )
    test_code = (
        "import pytest\n"
        "from target import main_calc\n"
        "\n"
        "def test_main_calc_positive():\n"
        "    assert main_calc(2) == 25\n"
        "\n"
        "def test_main_calc_zero():\n"
        "    assert main_calc(0) == 0\n"
    )

    runner = ParallelSandboxRunner(
        timeout_seconds=5,
        target_file_path="service.py",
        companion_files={"helper.py": helper_code}
    )

    # Run clean test suite inside isolated sandbox
    res = runner.run_single(test_code, target_code)
    assert res.get("status") == "PASS", f"Expected test to pass with companion file mounted, got: {res.get('stdout')} {res.get('stderr')}"
    assert res.get("tests_passed") == 2
    assert res.get("tests_failed") == 0


# ==============================================================================
# 3. End-to-End Multi-File Orchestrator Hardening Run
# ==============================================================================

def test_multi_file_orchestration_hardening_loop():
    models_code = (
        "class OrderItem:\n"
        "    def __init__(self, name: str, price: float, qty: int = 1):\n"
        "        self.name = name\n"
        "        self.price = price\n"
        "        self.qty = qty\n"
        "\n"
        "    def subtotal(self) -> float:\n"
        "        return self.price * self.qty\n"
    )
    billing_code = (
        "from models import OrderItem\n"
        "\n"
        "def calculate_invoice_total(items: list, discount_pct: float = 0.0) -> float:\n"
        "    if discount_pct < 0.0 or discount_pct > 1.0:\n"
        "        raise ValueError('Invalid discount')\n"
        "    gross = sum(item.subtotal() for item in items)\n"
        "    net = gross * (1.0 - discount_pct)\n"
        "    return round(net, 2)\n"
    )
    initial_test = (
        "import pytest\n"
        "from target import calculate_invoice_total\n"
        "from models import OrderItem\n"
        "\n"
        "def test_invoice_total_basic():\n"
        "    items = [OrderItem('Widget', 10.0, 2), OrderItem('Gadget', 5.0, 1)]\n"
        "    assert calculate_invoice_total(items, 0.1) == 22.5\n"
        "\n"
        "def test_invoice_invalid_discount():\n"
        "    items = [OrderItem('Widget', 10.0, 1)]\n"
        "    with pytest.raises(ValueError):\n"
        "        calculate_invoice_total(items, -0.05)\n"
    )

    with tempfile.TemporaryDirectory(prefix="testforge_e2e_multi_") as tmpdir:
        tmp_path = Path(tmpdir)
        models_file = tmp_path / "models.py"
        models_file.write_text(models_code, encoding="utf-8")
        billing_file = tmp_path / "billing.py"
        billing_file.write_text(billing_code, encoding="utf-8")

        orch = TestForgeOrchestrator(
            target_source_code=billing_code,
            initial_test_code=initial_test,
            target_file_path=str(billing_file),
            max_iterations=1,
            target_mutation_score=80.0,
            engine_mode="legacy",
            companion_files={"models.py": models_code}
        )

        final_state = orch.run()

        # DEF-022 Integrity
        assert final_state.baseline_tests_failed == 0
        assert final_state.baseline_tests_passed >= 2

        # TargetSpace has companion files & symbols
        tspace = orch.blackboard.get_target_space()
        assert "models.py" in tspace.companion_files
        assert "OrderItem" in tspace.resolved_symbols

        # Mutants evaluated
        mspace = orch.blackboard.get_mutant_space()
        assert mspace.mutants_generated > 0
        assert mspace.mutants_killed > 0


# ==============================================================================
# 4. Ingestion API Endpoint Tests
# ==============================================================================

def test_api_targets_ingest_multi():
    from fastapi.testclient import TestClient
    from server import app

    client = TestClient(app)
    payload = {
        "primary_filename": "service.py",
        "primary_code": "import helpers\ndef run(x): return helpers.double(x)\n",
        "companion_files": {
            "helpers.py": "def double(n: int) -> int:\n    return n * 2\n"
        }
    }
    resp = client.post("/api/targets/ingest-multi", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "success"
    assert "run" in data["functions"]
    dep = data["resolved_dependencies"]
    assert dep["companion_count"] == 1
    assert "helpers.py" in dep["companion_files"]
    assert "double" in dep["resolved_symbols"]

