"""
state.py - TestForge Shared Typed State Contract across Iterations.

Authors: Sourabh & Shreshth
"""

from __future__ import annotations
from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field


class MutantRecord(BaseModel):
    mutant_id: str = Field(..., description="Deterministic unique identifier, e.g. 'MUT_COMP_OP_001'")
    mutation_type: Literal["COMP_OP", "ARITH_OP", "COND_INV", "RETURN_VAL"]
    line_number: int
    original_code_snippet: str
    mutated_code_snippet: str
    unified_diff: str
    status: Literal["PENDING", "KILLED", "SURVIVED", "TIMEOUT", "ERROR"] = "PENDING"
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: float = 0.0


class IterationMetrics(BaseModel):
    iteration: int
    total_mutants: int
    killed_mutants: int
    survived_mutants: int
    timed_out_mutants: int
    mutation_score: float = 0.0
    line_coverage_pct: float = 0.0
    duration_seconds: float = 0.0


class TestForgeState(BaseModel):
    target_module_path: str = "target.py"
    test_module_path: str = "test_target.py"
    target_source_code: str = ""
    current_test_code: str = ""
    
    current_iteration: int = 0
    max_iterations: int = 3
    target_mutation_score: float = 85.0
    
    baseline_line_coverage: float = 0.0
    mutants: List[MutantRecord] = Field(default_factory=list)
    history: List[IterationMetrics] = Field(default_factory=list)
    
    surviving_mutant_diffs: List[str] = Field(default_factory=list)
    reflection_notes: List[str] = Field(default_factory=list)
    
    terminated: bool = False
    termination_reason: str = ""
    hardware_info: Dict[str, Any] = Field(default_factory=dict)
    active_provider: str = "Google GenAI Live"
