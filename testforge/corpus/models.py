"""
models.py - Structured Data Models for the TestForge Evaluation Corpus (GAP-04).

Defines:
  1. CorpusFixture: Self-contained specification of a benchmark fixture.
  2. DefectVariant: Controlled defect injection variant with expected failure modes.
  3. FixtureEvaluationResult: Multi-dimensional verification results.
"""

from __future__ import annotations
import hashlib
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


def compute_sha256(text: str) -> str:
    """Computes deterministic SHA-256 hash of normalized code string."""
    normalized = "\n".join(line.rstrip() for line in text.strip().splitlines())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class DefectVariant(BaseModel):
    """Represents a controlled, isolated defect variant for a fixture."""
    defect_id: str
    fixture_id: str
    name: str
    defect_type: str
    description: str
    target_function: str
    buggy_source_code: str
    buggy_source_hash: str = ""
    diff: str = ""
    expected_failing_test: str
    expected_error_type: str = "AssertionError"
    expected_message_substring: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.buggy_source_hash and self.buggy_source_code:
            self.buggy_source_hash = compute_sha256(self.buggy_source_code)


class CorpusFixture(BaseModel):
    """Represents a clean reference implementation with contract, baseline tests, and defect variants."""
    fixture_id: str
    name: str
    category: str
    description: str
    function_contract: str
    source_file: str
    source_code: str
    source_hash: str = ""
    baseline_test_code: str
    defects: Dict[str, DefectVariant] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if not self.source_hash and self.source_code:
            self.source_hash = compute_sha256(self.source_code)

    def get_defect(self, defect_id: str) -> Optional[DefectVariant]:
        return self.defects.get(defect_id)


class DefectDetectionReport(BaseModel):
    defect_id: str
    fixture_id: str
    detected: bool
    failing_test_name: Optional[str] = None
    observed_error_type: Optional[str] = None
    observed_error_message: Optional[str] = None
    matched_expected_assertion: bool = False
    duration_ms: float = 0.0


class FixtureEvaluationResult(BaseModel):
    fixture_id: str
    fixture_name: str
    source_hash: str
    reference_tests_total: int
    reference_tests_passed: int
    reference_passed: bool
    defect_reports: List[DefectDetectionReport] = Field(default_factory=list)
    defects_detected_count: int = 0
    defects_total_count: int = 0
    mutation_score_pct: float = 0.0
    adjusted_mutation_score_pct: float = 0.0
    mutants_total: int = 0
    mutants_killed: int = 0
    mutants_survived: int = 0
    mutants_timed_out: int = 0
    mutants_invalid: int = 0
    mutants_equivalent: int = 0
    mutants_potentially_equivalent: int = 0
    line_coverage_pct: float = 0.0
    execution_duration_sec: float = 0.0
    raw_execution_output: Optional[str] = None
