"""
test_mode_c_ingestion.py - Automated regression tests for Mode C GitHub Ingestion
and Hardening Pipeline Execution on real public repository files.

Authors: Sourabh & Shreshth
Course: CSE3101 - Agentic AI
"""

import pytest
from pathlib import Path
from testforge.ingestion import (
    TargetManagerAgent,
    fetch_github_source_with_meta,
    parse_and_normalize_github_url,
    normalize_github_url
)
from testforge.orchestrator import TestForgeOrchestrator

STATUS_CODES_URL = "https://github.com/psf/requests/blob/main/src/requests/status_codes.py"
COOKIES_URL = "https://github.com/psf/requests/blob/main/src/requests/cookies.py"
MODELS_URL = "https://github.com/psf/requests/blob/main/src/requests/models.py"


def test_regression_test_1_url_normalization():
    """
    TEST 1:
    Input: https://github.com/psf/requests/blob/main/src/requests/models.py
    Expected normalized URL: https://github.com/psf/requests/blob/main/src/requests/models.py
    Expected raw URL: https://raw.githubusercontent.com/psf/requests/main/src/requests/models.py
    """
    input_url = "https://github.com/psf/requests/blob/main/src/requests/models.py"
    info = parse_and_normalize_github_url(input_url)
    assert info["normalized_url"] == "https://github.com/psf/requests/blob/main/src/requests/models.py"
    assert info["raw_url"] == "https://raw.githubusercontent.com/psf/requests/main/src/requests/models.py"
    assert normalize_github_url(input_url) == "https://github.com/psf/requests/blob/main/src/requests/models.py"


def test_regression_test_2_malformed_url_rejection():
    """
    TEST 2:
    Input: https://github.com/psf/requests/blob/main/src/requests/models.py [Fetch & Ingest]
    Expected: VALIDATION FAILURE
    The system must NOT send this malformed string to network layer.
    The error should clearly say that the URL contains unexpected characters/text.
    """
    malformed_input = "https://github.com/psf/requests/blob/main/src/requests/models.py [Fetch & Ingest]"
    with pytest.raises(ValueError) as exc_info:
        parse_and_normalize_github_url(malformed_input)
    err_msg = str(exc_info.value)
    assert "invalid control characters" in err_msg or "unexpected" in err_msg or "UI artifacts" in err_msg


def test_regression_test_3_raw_github_url_support():
    """
    TEST 3:
    Input: https://raw.githubusercontent.com/psf/requests/main/src/requests/models.py
    Expected: accepted as a valid raw GitHub URL.
    """
    raw_input = "https://raw.githubusercontent.com/psf/requests/main/src/requests/models.py"
    info = parse_and_normalize_github_url(raw_input)
    assert info["raw_url"] == raw_input
    assert info["normalized_url"] == raw_input
    assert info["repository"] == "psf/requests"
    assert info["branch"] == "main"
    assert info["file_path"] == "src/requests/models.py"


def test_regression_test_4_sequential_replacement_full_state(tmp_path):
    """
    TEST 4:
    Change sequence:
    status_codes.py -> Fetch & Ingest -> verify status_codes source
    cookies.py -> Fetch & Ingest -> verify cookies source
    models.py -> Fetch & Ingest -> verify models source
    Each fetch must replace the complete ingestion state.
    """
    tm = TargetManagerAgent()

    # 1. status_codes.py
    path_1, analysis_1 = tm.ingest_github(STATUS_CODES_URL, output_dir=str(tmp_path))
    assert "status_codes" in analysis_1.module_name
    assert "class Request" not in analysis_1.source_code
    assert "LookupDict" in analysis_1.source_code
    assert analysis_1.ast_class_count == 0

    # 2. cookies.py
    path_2, analysis_2 = tm.ingest_github(COOKIES_URL, output_dir=str(tmp_path))
    assert "cookies" in analysis_2.module_name
    assert "status_codes" not in analysis_2.module_name
    assert "RequestsCookieJar" in analysis_2.classes
    assert analysis_2.source_sha != analysis_1.source_sha
    assert analysis_2.source_code != analysis_1.source_code
    assert "class RequestsCookieJar" in analysis_2.source_code

    # 3. models.py
    path_3, analysis_3 = tm.ingest_github(MODELS_URL, output_dir=str(tmp_path))
    assert "models" in analysis_3.module_name
    assert "cookies" not in analysis_3.module_name
    assert "status_codes" not in analysis_3.module_name
    assert "Request" in analysis_3.classes
    assert "PreparedRequest" in analysis_3.classes
    assert "Response" in analysis_3.classes
    assert analysis_3.source_sha != analysis_2.source_sha
    assert analysis_3.source_code != analysis_2.source_code
    assert "class Request" in analysis_3.source_code


def test_mode_c_cookies_ingestion(tmp_path):
    tm = TargetManagerAgent()
    saved_path, analysis = tm.ingest_github(COOKIES_URL, output_dir=str(tmp_path))

    assert saved_path.exists()
    assert "status_codes" not in analysis.module_name
    assert "cookies" in analysis.module_name

    # Expected: multiple classes, multiple functions/methods
    assert len(analysis.classes) >= 3, f"Expected multiple classes in cookies.py, got {analysis.classes}"
    assert "RequestsCookieJar" in analysis.classes
    assert analysis.ast_function_count >= 20, f"Expected multiple callables, got {analysis.ast_function_count}"

    # Verify metadata contracts
    meta = analysis.github_metadata
    assert meta["repository"] == "psf/requests"
    assert meta["branch"] == "main"
    assert meta["file_path"] == "src/requests/cookies.py"
    assert len(meta["source_sha"]) == 64
    assert meta["source_sha"] == analysis.source_sha
    assert meta["line_count"] > 100


def test_mode_c_models_ingestion(tmp_path):
    tm = TargetManagerAgent()
    saved_path, analysis = tm.ingest_github(MODELS_URL, output_dir=str(tmp_path))

    assert saved_path.exists()
    assert "status_codes" not in analysis.module_name
    assert "models" in analysis.module_name

    # Expected: multiple classes including Request, PreparedRequest and Response
    assert "Request" in analysis.classes
    assert "PreparedRequest" in analysis.classes
    assert "Response" in analysis.classes
    assert len(analysis.classes) >= 5, f"Expected at least 5 classes in models.py, got {analysis.classes}"
    assert analysis.ast_function_count >= 40, f"Expected substantially more callables, got {analysis.ast_function_count}"

    # Verify metadata contracts
    meta = analysis.github_metadata
    assert meta["repository"] == "psf/requests"
    assert meta["file_path"] == "src/requests/models.py"
    assert len(meta["source_sha"]) == 64


def test_mode_c_sequential_replacement_and_ast_transition(tmp_path):
    """
    Validates the exact sequence:
    status_codes.py -> Fetch -> verify AST
    cookies.py -> Fetch -> verify AST changed
    models.py -> Fetch -> verify AST changed again
    """
    tm = TargetManagerAgent()

    # 1. status_codes.py
    path_1, analysis_1 = tm.ingest_github(STATUS_CODES_URL, output_dir=str(tmp_path))
    assert "status_codes" in analysis_1.module_name
    sha_1 = analysis_1.source_sha
    classes_1 = list(analysis_1.classes)
    callables_1 = analysis_1.ast_function_count
    assert len(classes_1) == 0, "status_codes.py should have 0 classes"
    assert callables_1 == 1, "status_codes.py should have 1 top-level callable (_init)"

    # 2. cookies.py -> verify AST changed completely
    path_2, analysis_2 = tm.ingest_github(COOKIES_URL, output_dir=str(tmp_path))
    assert "cookies" in analysis_2.module_name
    assert "status_codes" not in analysis_2.module_name
    sha_2 = analysis_2.source_sha
    classes_2 = list(analysis_2.classes)
    callables_2 = analysis_2.ast_function_count

    assert sha_2 != sha_1, "cookies.py SHA-256 must differ from status_codes.py"
    assert len(classes_2) > 0, "cookies.py must contain classes"
    assert classes_2 != classes_1, "cookies.py classes must differ from status_codes.py"
    assert callables_2 > callables_1, "cookies.py must have more callables than status_codes.py"

    # 3. models.py -> verify AST changed again
    path_3, analysis_3 = tm.ingest_github(MODELS_URL, output_dir=str(tmp_path))
    assert "models" in analysis_3.module_name
    assert "status_codes" not in analysis_3.module_name
    assert "cookies" not in analysis_3.module_name
    sha_3 = analysis_3.source_sha
    classes_3 = list(analysis_3.classes)
    callables_3 = analysis_3.ast_function_count

    assert sha_3 != sha_2 and sha_3 != sha_1, "models.py SHA-256 must be distinct"
    assert classes_3 != classes_2, "models.py classes must differ from cookies.py"
    assert "Request" in classes_3
    assert "PreparedRequest" in classes_3
    assert "Response" in classes_3


def test_hardening_pipeline_on_models(tmp_path):
    """
    Executes the hardening pipeline against models.py and verifies all explicit execution metrics.
    """
    tm = TargetManagerAgent()
    saved_path, analysis = tm.ingest_github(MODELS_URL, output_dir=str(tmp_path))

    trace_file = str(tmp_path / "models_trace.jsonl")
    orch = TestForgeOrchestrator(
        target_source_code=analysis.source_code,
        max_iterations=1,
        target_mutation_score=85.0,
        trace_log_path=trace_file,
        target_file_path=str(saved_path),
        engine_mode="local"
    )

    state = orch.run()
    assert state is not None

    # Verify that the target source under test is genuinely models.py
    assert "class Request" in state.target_source_code
    assert "class PreparedRequest" in state.target_source_code
    assert "class Response" in state.target_source_code

    # Verify mutants generated on models.py
    assert state.mutants_generated > 50, f"Expected >50 mutants on models.py, got {state.mutants_generated}"

    # Verify explicit metrics exist and are populated
    assert isinstance(state.baseline_tests_generated, int)
    assert isinstance(state.baseline_tests_executed, int)
    assert isinstance(state.baseline_passed, bool)
    assert isinstance(state.lines_covered, int)
    assert isinstance(state.baseline_line_coverage, float)
    assert isinstance(state.mutants_generated, int)
    assert isinstance(state.mutants_executed, int)
    assert isinstance(state.mutants_killed, int)
    assert isinstance(state.mutants_survived, int)
    assert isinstance(state.mutation_execution_errors, int)
    assert isinstance(state.final_mutation_score, float)
    assert isinstance(state.reflection_iterations_performed, int)
    assert state.final_hardening_status in ("SUCCESS", "FAILED_BASELINE", "ZERO_COVERAGE_WARNING", "TARGET_SCORE_UNREACHED")

    # Anti-cheat check: Must NOT report SUCCESS if coverage is 0.0%
    if state.baseline_line_coverage == 0.0:
        assert state.final_hardening_status != "SUCCESS", "Cannot claim SUCCESS with 0.0% coverage"
