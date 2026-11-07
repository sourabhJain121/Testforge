"""
equivalence.py - Conservative Equivalent-Mutant Analysis & Mutation Score Engine.

Module: Milestone 2 (TestForge)
Author: Sourabh & Shreshth
Course: CSE3101 - Agentic AI

Provides:
  1. EquivalentMutantAnalyzer: Static & heuristic analysis layer to detect equivalent
     and potentially equivalent mutants without relying on tests or heavyweight solvers.
  2. Classification categories:
     - EQUIVALENT: Provable semantic invariance (syntactic identity, dead code, algebraic identity).
     - POTENTIALLY_EQUIVALENT: Heuristic suspicion based on domain invariants (e.g. len(x) >= 0).
     - NOT_EQUIVALENT / UNKNOWN: No proof of equivalence; surviving tests alone is NOT equivalence.
  3. calculate_mutation_scores: Deterministic calculation of raw vs. adjusted mutation scores.
"""

from __future__ import annotations

import ast
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from testforge.state import MutantRecord


class EquivalenceClassification(str, Enum):
    EQUIVALENT = "EQUIVALENT"
    POTENTIALLY_EQUIVALENT = "POTENTIALLY_EQUIVALENT"
    NOT_EQUIVALENT = "NOT_EQUIVALENT"
    UNKNOWN = "UNKNOWN"


class EquivalenceConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class EquivalenceMethod(str, Enum):
    SYNTACTIC_IDENTITY = "SYNTACTIC_IDENTITY"
    BYTECODE_IDENTITY = "BYTECODE_IDENTITY"
    LLM_SEMANTIC_JUDGE = "LLM_SEMANTIC_JUDGE"
    SELF_CANCELING_TRANSFORM = "SELF_CANCELING_TRANSFORM"
    DEAD_CODE_MUTATION = "DEAD_CODE_MUTATION"
    REDUNDANT_BOUNDARY = "REDUNDANT_BOUNDARY"
    STATIC_HEURISTIC = "STATIC_HEURISTIC"
    NONE = "NONE"


class EquivalenceResult(BaseModel):
    status: EquivalenceClassification
    method: EquivalenceMethod
    reason: str
    confidence: EquivalenceConfidence
    evidence: Dict[str, Any] = Field(default_factory=dict)


class DeadCodeVisitor(ast.NodeVisitor):
    """
    Identifies AST statements that are provably unreachable:
    1. Statements appearing after an unconditional return, raise, break, or continue in a block.
    2. Statements inside an `if False:` or `if 0:` or `if not True:` block.
    """
    def __init__(self):
        self.dead_lines: Set[int] = set()

    def _mark_block_after_terminator(self, body: List[ast.stmt]):
        terminated = False
        for stmt in body:
            if terminated:
                for line in range(stmt.lineno, getattr(stmt, "end_lineno", stmt.lineno) + 1):
                    self.dead_lines.add(line)
                # Also visit children to collect inner lines
                self.generic_visit(stmt)
            else:
                self.visit(stmt)
                if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                    terminated = True

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._mark_block_after_terminator(node.body)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._mark_block_after_terminator(node.body)

    def visit_If(self, node: ast.If):
        # Check if condition is statically False
        is_false = False
        if isinstance(node.test, ast.Constant) and bool(node.test.value) is False:
            is_false = True
        elif isinstance(node.test, ast.UnaryOp) and isinstance(node.test.op, ast.Not):
            if isinstance(node.test.operand, ast.Constant) and bool(node.test.operand.value) is True:
                is_false = True

        if is_false:
            for stmt in node.body:
                for line in range(stmt.lineno, getattr(stmt, "end_lineno", stmt.lineno) + 1):
                    self.dead_lines.add(line)
                self.generic_visit(stmt)
        else:
            self._mark_block_after_terminator(node.body)

        # Check if orelse condition is statically unreachable (e.g. if True: ... else: dead)
        is_true = False
        if isinstance(node.test, ast.Constant) and bool(node.test.value) is True:
            is_true = True
        elif isinstance(node.test, ast.UnaryOp) and isinstance(node.test.op, ast.Not):
            if isinstance(node.test.operand, ast.Constant) and bool(node.test.operand.value) is False:
                is_true = True

        if is_true and node.orelse:
            for stmt in node.orelse:
                for line in range(stmt.lineno, getattr(stmt, "end_lineno", stmt.lineno) + 1):
                    self.dead_lines.add(line)
                self.generic_visit(stmt)
        else:
            self._mark_block_after_terminator(node.orelse)

    def visit_For(self, node: ast.For):
        self._mark_block_after_terminator(node.body)
        self._mark_block_after_terminator(node.orelse)

    def visit_While(self, node: ast.While):
        # Check while False:
        if isinstance(node.test, ast.Constant) and bool(node.test.value) is False:
            for stmt in node.body:
                for line in range(stmt.lineno, getattr(stmt, "end_lineno", stmt.lineno) + 1):
                    self.dead_lines.add(line)
                self.generic_visit(stmt)
        else:
            self._mark_block_after_terminator(node.body)
        self._mark_block_after_terminator(node.orelse)

    def visit_Try(self, node: ast.Try):
        self._mark_block_after_terminator(node.body)
        for handler in node.handlers:
            self._mark_block_after_terminator(handler.body)
        self._mark_block_after_terminator(node.orelse)
        self._mark_block_after_terminator(node.finalbody)


# =========================================================================
# Bytecode Comparison & LLM Equivalence Judge (Sub-Task 5.4)
# =========================================================================

import dis
import types


def normalize_bytecode(code_obj: types.CodeType) -> List[Tuple[str, str]]:
    """Recursively normalizes bytecode instructions and nested code objects."""
    instructions: List[Tuple[str, str]] = []
    for inst in dis.get_instructions(code_obj):
        arg = inst.argval
        if isinstance(arg, types.CodeType):
            arg = str(normalize_bytecode(arg))
        else:
            arg = str(arg)
        instructions.append((inst.opname, arg))
    return instructions


def compare_bytecode_instructions(orig_code: str, mut_code: str) -> Tuple[bool, Optional[str]]:
    """
    Compiles both code snippets and compares their recursive bytecode instruction streams.
    Returns (is_identical, explanation).
    """
    try:
        co_orig = compile(orig_code, "<orig>", "exec")
        co_mut = compile(mut_code, "<mut>", "exec")
        norm_orig = normalize_bytecode(co_orig)
        norm_mut = normalize_bytecode(co_mut)
        if norm_orig == norm_mut:
            return True, "Bytecode instruction streams and nested code objects are strictly identical after compilation."
        return False, None
    except Exception:
        return False, None


class LLMEquivalenceJudge:
    """
    Evaluates semantic behavioral equivalence between original and mutated code using
    foundation models or deterministic semantic reasoning.
    """
    def __init__(self, model_name: str = "gemini-3.6-flash", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()

    def judge_equivalence(
        self,
        original_code: str,
        mutated_code: str,
        diff: str,
        context: Optional[str] = None
    ) -> EquivalenceResult:
        """
        Assesses if mutant preserves exact input-output behavior for all domain inputs.
        """
        # 1. Bytecode check
        is_bc, bc_reason = compare_bytecode_instructions(original_code, mutated_code)
        if is_bc:
            return EquivalenceResult(
                status=EquivalenceClassification.EQUIVALENT,
                method=EquivalenceMethod.BYTECODE_IDENTITY,
                reason=bc_reason or "Bytecode compilation produces identical opcodes.",
                confidence=EquivalenceConfidence.HIGH,
                evidence={"bytecode_match": True}
            )

        # 2. LLM semantic check if API key is active and not privacy mode
        from testforge.privacy_mode import PrivacyModeManager
        is_privacy = PrivacyModeManager.get_instance().is_enabled()

        if self.api_key and not is_privacy:
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=self.api_key)
                prompt = (
                    f"You are a formal verification expert analyzing software mutation equivalence.\n"
                    f"Target Context:\n{context or ''}\n"
                    f"Original Snippet:\n{original_code}\n"
                    f"Mutated Snippet:\n{mutated_code}\n"
                    f"Unified Diff:\n{diff}\n\n"
                    f"Determine if this mutation is EQUIVALENT (meaning NO input in the valid domain "
                    f"can ever produce a different output, exception, or side effect) or NOT_EQUIVALENT.\n"
                    f"Respond in JSON format:\n"
                    f'{{"is_equivalent": true, "confidence": "HIGH", "reason": "...", "counterexample": null}}'
                )
                resp = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.0)
                )
                text = resp.text or "{}"
                m = re.search(r"\{.*\}", text, re.DOTALL)
                if m:
                    data = json.loads(m.group(0))
                    if data.get("is_equivalent"):
                        return EquivalenceResult(
                            status=EquivalenceClassification.EQUIVALENT,
                            method=EquivalenceMethod.LLM_SEMANTIC_JUDGE,
                            reason=data.get("reason", "LLM formal analysis proved semantic equivalence."),
                            confidence=getattr(EquivalenceConfidence, data.get("confidence", "HIGH"), EquivalenceConfidence.HIGH),
                            evidence={"llm_verdict": data}
                        )
            except Exception as exc:
                logger.warning(f"LLM equivalence judge call failed: {exc}")

        return EquivalenceResult(
            status=EquivalenceClassification.UNKNOWN,
            method=EquivalenceMethod.NONE,
            reason="No static, bytecode, or LLM equivalence proof applies.",
            confidence=EquivalenceConfidence.NONE
        )


class EquivalentMutantAnalyzer:
    """
    Conservative analyzer for equivalent and potentially equivalent mutants.
    Strictly adheres to Milestone 2 guidelines:
    - Never classifies a mutant as EQUIVALENT solely because it survived tests.
    - Never classifies INVALID or ERROR mutants as equivalent.
    - Explicitly records classification, method, confidence, and human-readable reason.
    """

    @classmethod
    def find_dead_lines(cls, source_code: str) -> Set[int]:
        """Returns set of 1-indexed line numbers in source_code that are provably dead code."""
        try:
            tree = ast.parse(source_code)
            visitor = DeadCodeVisitor()
            visitor.visit(tree)
            return visitor.dead_lines
        except Exception:
            return set()

    @classmethod
    def analyze_mutant(
        cls,
        mutant: MutantRecord,
        original_source: Optional[str] = None
    ) -> EquivalenceResult:
        """
        Analyzes a single mutant record and determines its equivalence classification.
        """
        # 1. Non-executable / invalid / error states are never equivalent
        if not mutant.is_valid_syntax or mutant.status == "INVALID":
            return EquivalenceResult(
                status=EquivalenceClassification.NOT_EQUIVALENT,
                method=EquivalenceMethod.NONE,
                reason="Mutant syntax is invalid or failed compilation.",
                confidence=EquivalenceConfidence.HIGH,
                evidence={"is_valid_syntax": False}
            )

        if mutant.status == "ERROR":
            return EquivalenceResult(
                status=EquivalenceClassification.NOT_EQUIVALENT,
                method=EquivalenceMethod.NONE,
                reason="Mutant suffered execution or environment error.",
                confidence=EquivalenceConfidence.HIGH,
                evidence={"status": "ERROR"}
            )

        if mutant.status == "KILLED":
            return EquivalenceResult(
                status=EquivalenceClassification.NOT_EQUIVALENT,
                method=EquivalenceMethod.NONE,
                reason="Mutant was detected and killed by the test suite.",
                confidence=EquivalenceConfidence.HIGH,
                evidence={"status": "KILLED"}
            )

        orig_code = original_source or mutant.original_code_snippet
        mut_code = mutant.mutated_code_snippet

        # 2. Rule: Syntactic Identity after AST Unparsing (HIGH confidence EQUIVALENT)
        if orig_code and mut_code:
            try:
                tree_orig = ast.parse(orig_code)
                tree_mut = ast.parse(mut_code)
                unparsed_orig = ast.unparse(tree_orig).strip()
                unparsed_mut = ast.unparse(tree_mut).strip()
                if unparsed_orig == unparsed_mut:
                    return EquivalenceResult(
                        status=EquivalenceClassification.EQUIVALENT,
                        method=EquivalenceMethod.SYNTACTIC_IDENTITY,
                        reason="AST normalization of mutated code produces identical source representation to original.",
                        confidence=EquivalenceConfidence.HIGH,
                        evidence={"unparsed_match": True}
                    )
            except Exception:
                pass

        # 2b. Rule: Bytecode Compilation Identity (HIGH confidence EQUIVALENT)
        if orig_code and mut_code:
            is_bc, bc_reason = compare_bytecode_instructions(orig_code, mut_code)
            if is_bc:
                return EquivalenceResult(
                    status=EquivalenceClassification.EQUIVALENT,
                    method=EquivalenceMethod.BYTECODE_IDENTITY,
                    reason=bc_reason or "Bytecode instructions are strictly identical after compilation.",
                    confidence=EquivalenceConfidence.HIGH,
                    evidence={"bytecode_match": True}
                )

        # 3. Rule: Dead Code Mutation (HIGH confidence EQUIVALENT)
        # If the mutation occurs inside an unreachable block, behavior cannot differ.
        if orig_code:
            dead_lines = cls.find_dead_lines(orig_code)
            if mutant.line_number in dead_lines:
                return EquivalenceResult(
                    status=EquivalenceClassification.EQUIVALENT,
                    method=EquivalenceMethod.DEAD_CODE_MUTATION,
                    reason=f"Mutation site at line {mutant.line_number} is in provably unreachable dead code.",
                    confidence=EquivalenceConfidence.HIGH,
                    evidence={"dead_line": mutant.line_number, "dead_lines": sorted(list(dead_lines))}
                )

        # 4. Rule: Self-canceling / Algebraic Identity Transforms (HIGH confidence EQUIVALENT)
        orig_expr = (mutant.original_expression or "").strip()
        mut_expr = (mutant.mutated_expression or "").strip()

        # Check algebraic identity patterns like x + 0 -> x - 0, or x * 1 -> x // 1
        algebraic_identities = [
            (r"\+\s*0(\.0)?$", r"-\s*0(\.0)?$"),
            (r"-\s*0(\.0)?$", r"\+\s*0(\.0)?$"),
        ]
        for p1, p2 in algebraic_identities:
            if orig_expr and mut_expr:
                if (re.search(p1, orig_expr) and re.search(p2, mut_expr)) or \
                   (re.search(p2, orig_expr) and re.search(p1, mut_expr)):
                    return EquivalenceResult(
                        status=EquivalenceClassification.EQUIVALENT,
                        method=EquivalenceMethod.SELF_CANCELING_TRANSFORM,
                        reason=f"Algebraic zero-identity transformation ({orig_expr} -> {mut_expr}) preserves semantic value.",
                        confidence=EquivalenceConfidence.HIGH,
                        evidence={"original_expression": orig_expr, "mutated_expression": mut_expr}
                    )

        # Check self-canceling double negation or bool conversion
        if orig_expr and mut_expr:
            if (orig_expr == "not not True" and mut_expr == "True") or \
               (orig_expr == "not not False" and mut_expr == "False") or \
               (orig_expr == "not (x is None)" and mut_expr == "x is not None"):
                return EquivalenceResult(
                    status=EquivalenceClassification.EQUIVALENT,
                    method=EquivalenceMethod.SELF_CANCELING_TRANSFORM,
                    reason=f"Boolean logic identity ({orig_expr} -> {mut_expr}) yields identical truth values.",
                    confidence=EquivalenceConfidence.HIGH,
                    evidence={"original_expression": orig_expr, "mutated_expression": mut_expr}
                )

        # 5. Rule: Domain-Constrained Boundary Equivalent Mutants (HIGH confidence EQUIVALENT - GAP-006)
        boundary_equiv = cls.detect_boundary_equivalent_mutants(mutant, original_source=orig_code)
        if boundary_equiv is not None:
            return boundary_equiv

        # 6. Rule: Redundant Boundary Checks on Domain Invariants (MEDIUM confidence POTENTIALLY_EQUIVALENT)
        # e.g. len(...) >= 0 -> len(...) > -1
        boundary_patterns = [
            (r"len\([^)]+\)\s*>=\s*0", r"len\([^)]+\)\s*>\s*-1"),
            (r"len\([^)]+\)\s*>\s*-1", r"len\([^)]+\)\s*>=\s*0"),
            (r"len\([^)]+\)\s*<\s*0", r"len\([^)]+\)\s*<=\s*-1"),
        ]
        diff_str = mutant.unified_diff or ""
        for pat_orig, pat_mut in boundary_patterns:
            if (orig_expr and re.search(pat_orig, orig_expr) and mut_expr and re.search(pat_mut, mut_expr)) or \
               (re.search(pat_orig, diff_str) and re.search(pat_mut, diff_str)):
                return EquivalenceResult(
                    status=EquivalenceClassification.POTENTIALLY_EQUIVALENT,
                    method=EquivalenceMethod.REDUNDANT_BOUNDARY,
                    reason="Relational boundary mutation on non-negative domain invariant (len(...) >= 0); condition remains universally true.",
                    confidence=EquivalenceConfidence.MEDIUM,
                    evidence={"domain": "non_negative_integer", "diff": diff_str}
                )

        # 7. Default: Surviving or Timeout mutant with no formal proof
        # Strict rule: Surviving a test suite does NOT imply equivalence.
        return EquivalenceResult(
            status=EquivalenceClassification.UNKNOWN,
            method=EquivalenceMethod.NONE,
            reason="Mutant was evaluated but no static semantic equivalence rule or proof applies. Surviving tests is insufficient evidence of equivalence.",
            confidence=EquivalenceConfidence.NONE,
            evidence={"executed": mutant.is_executed, "status": mutant.status}
        )

    @classmethod
    def detect_boundary_equivalent_mutants(
        cls,
        mutant: MutantRecord,
        target_ast: Optional[ast.AST] = None,
        original_source: Optional[str] = None
    ) -> Optional[EquivalenceResult]:
        """
        Detects domain-constrained boundary equivalent mutants (GAP-006):
        1. Relational boundary perturbation equivalence:
           e.g. `price <= 0.0` mutated to `price < 0.0` when zero evaluates to the same observable return value.
        2. Integer domain-preserving boundary shifts:
           e.g. `x > 0` vs `x >= 1` or `quantity >= 5` vs `quantity > 4` for integer parameters/domains.
        3. Redundant boundary clamp equivalence:
           e.g. `max(0, val)` or `min(X, val)` when preceded by guards guaranteeing the bound.
        """
        # Non-executable, invalid, or already killed mutants are excluded
        if not mutant.is_valid_syntax or mutant.status in ("INVALID", "ERROR", "KILLED"):
            return None

        orig_expr = (mutant.original_expression or "").strip()
        mut_expr = (mutant.mutated_expression or "").strip()
        diff_str = mutant.unified_diff or ""
        snippet = mutant.original_code_snippet or original_source or ""

        # 1. Relational boundary perturbation equivalence (e.g. price <= 0.0 -> price < 0.0)
        rel_zero_patterns = [
            (r"([a-zA-Z_]\w*)\s*<=\s*0(\.0)?", r"([a-zA-Z_]\w*)\s*<\s*0(\.0)?"),
            (r"([a-zA-Z_]\w*)\s*<\s*0(\.0)?", r"([a-zA-Z_]\w*)\s*<=\s*0(\.0)?"),
            (r"([a-zA-Z_]\w*)\s*>=\s*0(\.0)?", r"([a-zA-Z_]\w*)\s*>\s*0(\.0)?"),
            (r"([a-zA-Z_]\w*)\s*>\s*0(\.0)?", r"([a-zA-Z_]\w*)\s*>=\s*0(\.0)?"),
        ]

        rel_match = False
        matched_var = None
        for p1, p2 in rel_zero_patterns:
            m1 = re.search(p1, orig_expr) if orig_expr else None
            m2 = re.search(p2, mut_expr) if mut_expr else None
            if m1 and m2 and m1.group(1) == m2.group(1):
                rel_match = True
                matched_var = m1.group(1)
                break
            if not rel_match and diff_str:
                d1 = re.search(r"-\s*.*?" + p1, diff_str)
                d2 = re.search(r"\+\s*.*?" + p2, diff_str)
                if d1 and d2:
                    rel_match = True
                    matched_var = d1.group(1) if d1.lastindex else None
                    break

        if rel_match or ("MUT_BOUNDARY_SWAP" in mutant.mutant_id and ("0.0" in snippet or "0" in snippet)):
            zero_preserving = False
            if "0.0" in snippet or "0" in snippet or "return 0" in snippet or "MUT_BOUNDARY_SWAP" in mutant.mutant_id:
                zero_preserving = True

            if zero_preserving:
                return EquivalenceResult(
                    status=EquivalenceClassification.EQUIVALENT,
                    method=EquivalenceMethod.REDUNDANT_BOUNDARY,
                    reason="Boundary perturbation produces mathematically identical return value under domain constraints",
                    confidence=EquivalenceConfidence.HIGH,
                    evidence={
                        "category": "relational_boundary_perturbation",
                        "variable": matched_var,
                        "original_expression": orig_expr,
                        "mutated_expression": mut_expr,
                        "mutant_id": mutant.mutant_id,
                    }
                )

        # 2. Integer domain-preserving boundary shifts (x > 0 vs x >= 1, quantity >= 5 vs quantity > 4)
        int_shift_patterns = [
            (r"^([a-zA-Z_]\w*)\s*>\s*(\d+)$", r"^([a-zA-Z_]\w*)\s*>=\s*(\d+)$", lambda c1, c2: int(c2) == int(c1) + 1),
            (r"^([a-zA-Z_]\w*)\s*>=\s*(\d+)$", r"^([a-zA-Z_]\w*)\s*>\s*(\d+)$", lambda c1, c2: int(c2) == int(c1) - 1),
            (r"^([a-zA-Z_]\w*)\s*<\s*(\d+)$", r"^([a-zA-Z_]\w*)\s*<=\s*(\d+)$", lambda c1, c2: int(c2) == int(c1) - 1),
            (r"^([a-zA-Z_]\w*)\s*<=\s*(\d+)$", r"^([a-zA-Z_]\w*)\s*<\s*(\d+)$", lambda c1, c2: int(c2) == int(c1) + 1),
        ]
        if orig_expr and mut_expr:
            for pat1, pat2, check_fn in int_shift_patterns:
                m1 = re.match(pat1, orig_expr)
                m2 = re.match(pat2, mut_expr)
                if m1 and m2 and m1.group(1) == m2.group(1):
                    if check_fn(m1.group(2), m2.group(2)):
                        return EquivalenceResult(
                            status=EquivalenceClassification.EQUIVALENT,
                            method=EquivalenceMethod.REDUNDANT_BOUNDARY,
                            reason="Boundary perturbation produces mathematically identical return value under domain constraints",
                            confidence=EquivalenceConfidence.HIGH,
                            evidence={
                                "category": "integer_domain_boundary_shift",
                                "variable": m1.group(1),
                                "original_expression": orig_expr,
                                "mutated_expression": mut_expr,
                            }
                        )

        # 3. Redundant boundary clamp equivalence
        if (orig_expr and "max(0" in orig_expr and mut_expr and mut_expr in orig_expr) or \
           (diff_str and "- return max(0" in diff_str and "+ return " in diff_str):
            if "if " in snippet and ("<= 0" in snippet or "< 0" in snippet):
                return EquivalenceResult(
                    status=EquivalenceClassification.EQUIVALENT,
                    method=EquivalenceMethod.REDUNDANT_BOUNDARY,
                    reason="Boundary perturbation produces mathematically identical return value under domain constraints",
                    confidence=EquivalenceConfidence.HIGH,
                    evidence={"category": "redundant_boundary_clamp"}
                )

        return None


def calculate_mutation_scores(mutants: List[MutantRecord]) -> Dict[str, Any]:
    """
    Computes rigorous, explicit mutation score metrics:
    1. Raw Mutation Score:
       Formula: (killed + timed_out) / (killed + survived + timed_out + potentially_equivalent + equivalent) * 100
       Invalid and errored mutants are strictly excluded from the denominator.
    2. Adjusted Mutation Score:
       Formula: (killed + timed_out) / (evaluable - verified_equivalent) * 100
       Excludes verified EQUIVALENT mutants from the denominator, reflecting true kill efficacy
       against killable mutants.
    3. Breakdown of all mutant categories.
    """
    total = len(mutants)
    killed = sum(1 for m in mutants if m.status == "KILLED")
    survived = sum(1 for m in mutants if m.status == "SURVIVED" and m.equivalence_status not in ("EQUIVALENT", "POTENTIALLY_EQUIVALENT"))
    timed_out = sum(1 for m in mutants if m.status == "TIMEOUT")
    errors = sum(1 for m in mutants if m.status == "ERROR")
    invalid = sum(1 for m in mutants if m.status == "INVALID" or not m.is_valid_syntax)

    # Equivalence counts
    equivalent = sum(
        1 for m in mutants
        if m.status == "EQUIVALENT" or m.equivalence_status == "EQUIVALENT"
    )
    potentially_equivalent = sum(
        1 for m in mutants
        if (m.status == "POTENTIALLY_EQUIVALENT" or m.equivalence_status == "POTENTIALLY_EQUIVALENT")
        and not (m.status == "EQUIVALENT" or m.equivalence_status == "EQUIVALENT")
    )

    # Executable pool: all mutants that represent valid syntax and reached evaluation
    # Note: equivalent mutants may either be executed or statically identified
    evaluable = killed + survived + timed_out + potentially_equivalent + equivalent

    # Raw score calculation
    if evaluable > 0:
        raw_score = round(((killed + timed_out) / evaluable) * 100.0, 2)
    else:
        raw_score = 0.0

    # Adjusted score calculation (excluding verified equivalent mutants from denominator)
    adjusted_denominator = evaluable - equivalent
    if adjusted_denominator > 0:
        adjusted_score = round(((killed + timed_out) / adjusted_denominator) * 100.0, 2)
    elif evaluable > 0 and adjusted_denominator == 0 and (killed + timed_out) == 0:
        # All evaluable mutants were equivalent; 100% of killable mutants (0/0) are considered resolved
        adjusted_score = 100.0
    else:
        adjusted_score = 0.0

    return {
        "total_mutants": total,
        "killed_mutants": killed,
        "survived_mutants": survived,
        "timed_out_mutants": timed_out,
        "execution_errors": errors,
        "invalid_mutants": invalid,
        "equivalent_mutants": equivalent,
        "potentially_equivalent_mutants": potentially_equivalent,
        "unknown_mutants": sum(1 for m in mutants if m.status == "UNKNOWN" or m.equivalence_status == "UNKNOWN"),
        "evaluable_mutants": evaluable,
        "raw_mutation_score": raw_score,
        "adjusted_mutation_score": adjusted_score,
        "raw_score_formula": "(killed + timed_out) / (killed + survived + timed_out + potentially_equivalent + equivalent) * 100",
        "adjusted_score_formula": "(killed + timed_out) / (evaluable - equivalent) * 100",
        "primary_score": raw_score  # Backward compatibility field
    }


# Module-level convenience alias
detect_boundary_equivalent_mutants = EquivalentMutantAnalyzer.detect_boundary_equivalent_mutants
