"""
tests/test_flaky_detection.py

Automated Test Suite for Flaky-Test Detection and Automated Quarantine (Sub-Task 5.3).
"""

import pytest
from starlette.testclient import TestClient

from server import app
from testforge.flaky_detector import FlakyDetectionResult, FlakyTestDetector

CLEAN_TEST_CODE = """
def test_add():
    assert 1 + 1 == 2

def test_sub():
    assert 5 - 3 == 2

def test_mul():
    assert 3 * 4 == 12
"""

FLAKY_ORDER_CODE = """
_FLAG = {"ready": False}

def test_init():
    _FLAG["ready"] = True
    assert _FLAG["ready"] is True

def test_consume():
    # Flaky: requires test_init to run before test_consume
    assert _FLAG["ready"] is True
"""


def test_deterministic_suite_zero_flakiness():
    detector = FlakyTestDetector(iterations=3)
    res = detector.detect_flakiness(CLEAN_TEST_CODE, "x = 1", "clean_module")

    assert isinstance(res, FlakyDetectionResult)
    assert res.total_tests_evaluated == 3
    assert res.flaky_count == 0
    assert res.deterministic_pass_count == 3
    assert len(res.quarantined_tests) == 0


def test_order_dependent_flaky_detection_and_quarantine():
    detector = FlakyTestDetector(iterations=5, base_seeds=[1, 2, 3, 4, 5])
    res = detector.detect_flakiness(FLAKY_ORDER_CODE, "x = 1", "flaky_module")

    assert isinstance(res, FlakyDetectionResult)
    assert res.flaky_count >= 1
    assert "test_consume" in res.quarantined_tests

    # Reconstructed clean code must omit the quarantined test
    assert "def test_consume" not in res.clean_test_code
    assert "def test_init" in res.clean_test_code


def test_flaky_detect_api_endpoint():
    client = TestClient(app)
    resp = client.post("/api/flaky/detect", json={
        "test_code": FLAKY_ORDER_CODE,
        "target_source": "x = 1",
        "iterations": 5
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "flaky_count" in data
    assert "quarantined_tests" in data
    assert data["flaky_count"] >= 1
    assert "test_consume" in data["quarantined_tests"]

