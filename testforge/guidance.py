"""
guidance.py - Semantic Guidance Engine for Surviving AST Mutants.

Milestone 2 for Phase 4.1:
Transforms raw surviving mutant diffs into structured, actionable semantic guidance
for the Adversarial Critic and Test Generator agents. Derives the precise behavioral
distinction introduced by the mutation, boundary/edge conditions likely to distinguish
the original program from the mutated version, and confidence annotations.
"""

from __future__ import annotations
import ast
import re
from typing import List, Dict, Optional, Literal, Any, Union
from pydantic import BaseModel, Field

from testforge.state import MutantRecord


class SemanticMutantGuidance(BaseModel):
    """
    Structured semantic guidance for an individual surviving mutant.
    Captures operational distinctions, suggested boundary inputs, and confidence.
    """
    mutant_id: str = Field(..., description="Unique mutant identifier e.g. MUT_COMP_OP_001")
    mutation_type: str = Field(..., description="Mutation operator category e.g. COMP_OP, ARITH_OP")
    line_number: int = Field(default=1, description="1-indexed source line location")
    original_expression: Optional[str] = Field(default=None, description="Original source AST expression")
    mutated_expression: Optional[str] = Field(default=None, description="Mutated AST expression")
    behavioral_distinction: str = Field(..., description="Concise explanation of the behavioral change")
    suggested_inputs: List[str] = Field(default_factory=list, description="Inputs or boundaries likely to distinguish original from mutant")
    confidence: Literal["HIGH", "MEDIUM", "LOW", "UNCERTAIN"] = "HIGH"
    uncertainty_note: Optional[str] = Field(default=None, description="Caveats when semantics cannot be inferred safely")

    def to_directive_text(self) -> str:
        """Formats guidance into an actionable numbered directive for agent prompting."""
        orig_s = f"'{self.original_expression}'" if self.original_expression else "original"
        mut_s = f"'{self.mutated_expression}'" if self.mutated_expression else "mutant"
        lines = [
            f"[{self.mutant_id}] Line {self.line_number} ({self.mutation_type}): {orig_s} -> {mut_s}",
            f"  - Distinction: {self.behavioral_distinction}",
        ]
        if self.suggested_inputs:
            inputs_str = "; ".join(self.suggested_inputs)
            lines.append(f"  - Suggested verification: {inputs_str}")
        if self.uncertainty_note:
            lines.append(f"  - Note ({self.confidence}): {self.uncertainty_note}")
        return "\n".join(lines)


def _extract_expressions_from_diff(diff: str) -> tuple[Optional[str], Optional[str]]:
    """Fallback extraction of original and mutated line snippets from unified diff."""
    orig_line = None
    mut_line = None
    for line in diff.splitlines():
        if line.startswith("-") and not line.startswith("---"):
            orig_line = line[1:].strip()
        elif line.startswith("+") and not line.startswith("+++"):
            mut_line = line[1:].strip()
    return orig_line, mut_line


def derive_semantic_guidance(
    mutant: Union[MutantRecord, Dict[str, Any]],
    target_code: Optional[str] = None
) -> SemanticMutantGuidance:
    """
    Derives structured semantic guidance for a surviving mutant based on its
    mutation type, AST expressions, line number, and behavioral divergence.
    Supports both MutantRecord instances and dictionary records.
    """
    if isinstance(mutant, dict):
        m_id = mutant.get("mutant_id", "MUT_UNKNOWN")
        m_type = mutant.get("mutation_type", "UNKNOWN")
        line_no = mutant.get("line_number", 1)
        orig_expr = mutant.get("original_expression")
        mut_expr = mutant.get("mutated_expression")
        diff = mutant.get("unified_diff", "")
    else:
        m_id = getattr(mutant, "mutant_id", "MUT_UNKNOWN")
        m_type = getattr(mutant, "mutation_type", "UNKNOWN")
        line_no = getattr(mutant, "line_number", 1)
        orig_expr = getattr(mutant, "original_expression", None)
        mut_expr = getattr(mutant, "mutated_expression", None)
        diff = getattr(mutant, "unified_diff", "")

    if not orig_expr or not mut_expr:
        diff_orig, diff_mut = _extract_expressions_from_diff(diff)
        orig_expr = orig_expr or diff_orig
        mut_expr = mut_expr or diff_mut

    # 1. Comparison Inversion (COMP_OP) & Boundary Swaps (BOUNDARY_SWAP)
    if m_type in ("COMP_OP", "BOUNDARY_SWAP"):
        return _guidance_for_comparison(m_id, m_type, line_no, orig_expr, mut_expr)

    # 2. Off-By-One Constant Shifts (OFF_BY_ONE)
    elif m_type == "OFF_BY_ONE":
        return _guidance_for_off_by_one(m_id, m_type, line_no, orig_expr, mut_expr)

    # 3. Arithmetic Operator Swapping (ARITH_OP)
    elif m_type == "ARITH_OP":
        return _guidance_for_arithmetic(m_id, m_type, line_no, orig_expr, mut_expr)

    # 4. Logical Connective Swaps (LOGICAL_CONN)
    elif m_type == "LOGICAL_CONN":
        return _guidance_for_logical(m_id, m_type, line_no, orig_expr, mut_expr)

    # 5. Math Functions & Precision (MATH_FUNC)
    elif m_type == "MATH_FUNC":
        return _guidance_for_math_func(m_id, m_type, line_no, orig_expr, mut_expr)

    # 6. Conditional Inversion (COND_INV)
    elif m_type == "COND_INV":
        return _guidance_for_cond_inv(m_id, m_type, line_no, orig_expr, mut_expr)

    # 7. Return Value Mutations (RETURN_VAL)
    elif m_type == "RETURN_VAL":
        return _guidance_for_return_val(m_id, m_type, line_no, orig_expr, mut_expr)

    # 8. Constant Literal Mutations (CONST_VAL)
    elif m_type == "CONST_VAL":
        return _guidance_for_const_val(m_id, m_type, line_no, orig_expr, mut_expr)

    # 9. Exception Handler Mutations (EXCEPT_HANDLER)
    elif m_type == "EXCEPT_HANDLER":
        return _guidance_for_except_handler(m_id, m_type, line_no, orig_expr, mut_expr)

    # 10. Default / Ambiguous / Unknown Mutations
    else:
        return SemanticMutantGuidance(
            mutant_id=m_id,
            mutation_type=m_type,
            line_number=line_no,
            original_expression=orig_expr,
            mutated_expression=mut_expr,
            behavioral_distinction="Syntactic AST modification whose precise operational semantics cannot be classified statically.",
            suggested_inputs=["Inspect unified diff and formulate assertions targeting divergent output states"],
            confidence="UNCERTAIN",
            uncertainty_note="Behavioral distinction cannot be reliably inferred statically from AST diff alone."
        )



def _guidance_for_comparison(
    mutant_id: str,
    m_type: str,
    line_no: int,
    orig_expr: Optional[str],
    mut_expr: Optional[str]
) -> SemanticMutantGuidance:
    orig = orig_expr or ""
    mut = mut_expr or ""

    # Relational boundary swaps: < vs <=, > vs >=
    if (">=" in orig and ">" in mut and "<" not in mut) or ("<=" in orig and "<" in mut):
        distinction = (
            f"Relational boundary comparison was narrowed from inclusive ('{orig}') to strict ('{mut}'). "
            "The mutated code excludes and fails exact boundary equality."
        )
        suggested = [
            "Test exact boundary equality where LHS == RHS",
            "Test values immediately above and below the boundary threshold"
        ]
        return SemanticMutantGuidance(
            mutant_id=mutant_id,
            mutation_type=m_type,
            line_number=line_no,
            original_expression=orig_expr,
            mutated_expression=mut_expr,
            behavioral_distinction=distinction,
            suggested_inputs=suggested,
            confidence="HIGH",
            uncertainty_note="Exact numeric values depend on surrounding preconditions and argument types."
        )

    if (">" in orig and ">=" in mut and "<" not in orig) or ("<" in orig and "<=" in mut):
        distinction = (
            f"Relational boundary comparison was widened from strict ('{orig}') to inclusive ('{mut}'). "
            "The mutated code improperly accepts exact boundary equality."
        )
        suggested = [
            "Test exact boundary equality where LHS == RHS",
            "Test nearest adjacent boundary neighbor values"
        ]
        return SemanticMutantGuidance(
            mutant_id=mutant_id,
            mutation_type=m_type,
            line_number=line_no,
            original_expression=orig_expr,
            mutated_expression=mut_expr,
            behavioral_distinction=distinction,
            suggested_inputs=suggested,
            confidence="HIGH",
            uncertainty_note="Exact numeric values depend on surrounding preconditions and argument types."
        )

    # Equality inversions: == vs !=
    if "==" in orig and "!=" in mut:
        return SemanticMutantGuidance(
            mutant_id=mutant_id,
            mutation_type=m_type,
            line_number=line_no,
            original_expression=orig_expr,
            mutated_expression=mut_expr,
            behavioral_distinction="Equality comparison inverted from '==' to '!='. Produces inverted boolean truth value on matching items.",
            suggested_inputs=[
                "Assert execution when operands are equal (LHS == RHS)",
                "Assert execution when operands are distinct (LHS != RHS)"
            ],
            confidence="HIGH"
        )
    if "!=" in orig and "==" in mut:
        return SemanticMutantGuidance(
            mutant_id=mutant_id,
            mutation_type=m_type,
            line_number=line_no,
            original_expression=orig_expr,
            mutated_expression=mut_expr,
            behavioral_distinction="Inequality comparison inverted from '!=' to '=='.",
            suggested_inputs=[
                "Assert execution when operands are distinct (LHS != RHS)",
                "Assert execution when operands are identical (LHS == RHS)"
            ],
            confidence="HIGH"
        )

    # Membership and identity
    if " in " in orig and " not in " in mut:
        return SemanticMutantGuidance(
            mutant_id=mutant_id,
            mutation_type=m_type,
            line_number=line_no,
            original_expression=orig_expr,
            mutated_expression=mut_expr,
            behavioral_distinction="Membership test inverted from 'in' to 'not in'.",
            suggested_inputs=[
                "Test target item present in collection",
                "Test target item absent from collection"
            ],
            confidence="HIGH"
        )
    if " not in " in orig and " in " in mut:
        return SemanticMutantGuidance(
            mutant_id=mutant_id,
            mutation_type=m_type,
            line_number=line_no,
            original_expression=orig_expr,
            mutated_expression=mut_expr,
            behavioral_distinction="Membership test inverted from 'not in' to 'in'.",
            suggested_inputs=[
                "Test target item absent from collection",
                "Test target item present in collection"
            ],
            confidence="HIGH"
        )

    # General relational polarity flip: > to <=, < to >=
    distinction = f"Comparison operator polarity inverted from '{orig}' to '{mut}'."
    return SemanticMutantGuidance(
        mutant_id=mutant_id,
        mutation_type=m_type,
        line_number=line_no,
        original_expression=orig_expr,
        mutated_expression=mut_expr,
        behavioral_distinction=distinction,
        suggested_inputs=[
            "Test values satisfying the original condition",
            "Test values satisfying the inverted condition",
            "Test equality threshold where LHS == RHS"
        ],
        confidence="HIGH"
    )


def _guidance_for_off_by_one(
    mutant_id: str,
    m_type: str,
    line_no: int,
    orig_expr: Optional[str],
    mut_expr: Optional[str]
) -> SemanticMutantGuidance:
    return SemanticMutantGuidance(
        mutant_id=mutant_id,
        mutation_type=m_type,
        line_number=line_no,
        original_expression=orig_expr,
        mutated_expression=mut_expr,
        behavioral_distinction="Numeric comparison threshold shifted by an off-by-one constant offset (n to n+1 or n-1).",
        suggested_inputs=[
            "Assert behavior on input matching the original threshold value exactly",
            "Assert behavior on shifted threshold values (offset by +1 and -1)"
        ],
        confidence="HIGH",
        uncertainty_note="Ensure test input exercises the specific comparison branch rather than an earlier guard."
    )


def _guidance_for_arithmetic(
    mutant_id: str,
    m_type: str,
    line_no: int,
    orig_expr: Optional[str],
    mut_expr: Optional[str]
) -> SemanticMutantGuidance:
    orig = orig_expr or ""
    mut = mut_expr or ""

    if "+" in orig and "-" in mut:
        return SemanticMutantGuidance(
            mutant_id=mutant_id,
            mutation_type=m_type,
            line_number=line_no,
            original_expression=orig_expr,
            mutated_expression=mut_expr,
            behavioral_distinction="Addition operator swapped with subtraction ('+' -> '-').",
            suggested_inputs=[
                "Test operands where the second operand is non-zero (b != 0), where a + b != a - b",
                "Include negative or positive values to verify algebraic sign",
                "Avoid b = 0 where a + 0 == a - 0 creates coincidental survival"
            ],
            confidence="HIGH"
        )
    elif "-" in orig and "+" in mut:
        return SemanticMutantGuidance(
            mutant_id=mutant_id,
            mutation_type=m_type,
            line_number=line_no,
            original_expression=orig_expr,
            mutated_expression=mut_expr,
            behavioral_distinction="Subtraction operator swapped with addition ('-' -> '+').",
            suggested_inputs=[
                "Test operands where the second operand is non-zero (b != 0), where a - b != a + b",
                "Avoid b = 0 where a - 0 == a + 0 creates coincidental survival"
            ],
            confidence="HIGH"
        )
    elif ("*" in orig and ("//" in mut or "/" in mut)) or (("//" in orig or "/" in orig) and "*" in mut):
        return SemanticMutantGuidance(
            mutant_id=mutant_id,
            mutation_type=m_type,
            line_number=line_no,
            original_expression=orig_expr,
            mutated_expression=mut_expr,
            behavioral_distinction="Multiplication swapped with division operator (or vice versa).",
            suggested_inputs=[
                "Test operands with factors greater than 1 (avoid multiplying/dividing by 1 where a * 1 == a / 1)",
                "Test fractional or non-integer quotients to detect floor-division truncations"
            ],
            confidence="HIGH"
        )
    elif "%" in orig:
        return SemanticMutantGuidance(
            mutant_id=mutant_id,
            mutation_type=m_type,
            line_number=line_no,
            original_expression=orig_expr,
            mutated_expression=mut_expr,
            behavioral_distinction="Modulo remainder operator swapped with multiplication ('%' -> '*').",
            suggested_inputs=[
                "Test dividend greater than divisor producing a non-zero remainder",
                "Avoid divisor = 1 where a % 1 is always 0"
            ],
            confidence="HIGH"
        )

    return SemanticMutantGuidance(
        mutant_id=mutant_id,
        mutation_type=m_type,
        line_number=line_no,
        original_expression=orig_expr,
        mutated_expression=mut_expr,
        behavioral_distinction=f"Binary arithmetic operator swapped from '{orig}' to '{mut}'.",
        suggested_inputs=[
            "Assert precise computed numerical results for non-trivial inputs",
            "Avoid identity operands (0 for add/sub, 1 for mult/div) that allow mutated operators to evaluate identically"
        ],
        confidence="HIGH"
    )


def _guidance_for_logical(
    mutant_id: str,
    m_type: str,
    line_no: int,
    orig_expr: Optional[str],
    mut_expr: Optional[str]
) -> SemanticMutantGuidance:
    orig = orig_expr or ""
    mut = mut_expr or ""

    if "and" in orig and "or" in mut:
        return SemanticMutantGuidance(
            mutant_id=mutant_id,
            mutation_type=m_type,
            line_number=line_no,
            original_expression=orig_expr,
            mutated_expression=mut_expr,
            behavioral_distinction="Logical conjunction ('and') swapped with disjunction ('or'). Mutated code improperly accepts when only one operand is True.",
            suggested_inputs=[
                "Test mixed truth combinations: (True, False) and (False, True) where 'and' is False but 'or' is True",
                "Avoid (True, True) and (False, False) where 'and' and 'or' produce identical evaluations"
            ],
            confidence="HIGH"
        )
    elif "or" in orig and "and" in mut:
        return SemanticMutantGuidance(
            mutant_id=mutant_id,
            mutation_type=m_type,
            line_number=line_no,
            original_expression=orig_expr,
            mutated_expression=mut_expr,
            behavioral_distinction="Logical disjunction ('or') swapped with conjunction ('and'). Mutated code improperly fails when only one operand is True.",
            suggested_inputs=[
                "Test mixed truth combinations: (True, False) and (False, True) where 'or' is True but 'and' is False"
            ],
            confidence="HIGH"
        )

    return SemanticMutantGuidance(
        mutant_id=mutant_id,
        mutation_type=m_type,
        line_number=line_no,
        original_expression=orig_expr,
        mutated_expression=mut_expr,
        behavioral_distinction=f"Logical connective mutated from '{orig}' to '{mut}'.",
        suggested_inputs=["Test inputs with divergent truth values across the compound condition"],
        confidence="HIGH"
    )


def _guidance_for_math_func(
    mutant_id: str,
    m_type: str,
    line_no: int,
    orig_expr: Optional[str],
    mut_expr: Optional[str]
) -> SemanticMutantGuidance:
    orig = orig_expr or ""
    mut = mut_expr or ""

    if "round" in orig:
        return SemanticMutantGuidance(
            mutant_id=mutant_id,
            mutation_type=m_type,
            line_number=line_no,
            original_expression=orig_expr,
            mutated_expression=mut_expr,
            behavioral_distinction="Floating-point precision rounding argument decremented (e.g. round(x, 2) -> round(x, 1)).",
            suggested_inputs=[
                "Test floating-point values where the removed decimal digit is non-zero (e.g. 10.05 or 12.49) to detect truncated cents/precision"
            ],
            confidence="HIGH"
        )
    elif "abs" in orig:
        return SemanticMutantGuidance(
            mutant_id=mutant_id,
            mutation_type=m_type,
            line_number=line_no,
            original_expression=orig_expr,
            mutated_expression=mut_expr,
            behavioral_distinction="Absolute value function call stripped ('abs(x)' -> 'x').",
            suggested_inputs=[
                "Test strictly negative numeric inputs (x < 0) where x != abs(x)",
                "Avoid non-negative values (x >= 0) where abs(x) == x causes coincidental survival"
            ],
            confidence="HIGH"
        )

    return SemanticMutantGuidance(
        mutant_id=mutant_id,
        mutation_type=m_type,
        line_number=line_no,
        original_expression=orig_expr,
        mutated_expression=mut_expr,
        behavioral_distinction=f"Math function call mutated from '{orig}' to '{mut}'.",
        suggested_inputs=["Assert exact mathematical outputs sensitive to function stripping or precision changes"],
        confidence="MEDIUM"
    )


def _guidance_for_cond_inv(
    mutant_id: str,
    m_type: str,
    line_no: int,
    orig_expr: Optional[str],
    mut_expr: Optional[str]
) -> SemanticMutantGuidance:
    return SemanticMutantGuidance(
        mutant_id=mutant_id,
        mutation_type=m_type,
        line_number=line_no,
        original_expression=orig_expr,
        mutated_expression=mut_expr,
        behavioral_distinction="Conditional test inverted with 'not' ('if cond' -> 'if not cond'). Reverses branch selection.",
        suggested_inputs=[
            "Test inputs that satisfy the original condition and assert expected if-branch execution",
            "Test inputs that falsify the condition and assert alternate/else-branch execution"
        ],
        confidence="HIGH"
    )


def _guidance_for_return_val(
    mutant_id: str,
    m_type: str,
    line_no: int,
    orig_expr: Optional[str],
    mut_expr: Optional[str]
) -> SemanticMutantGuidance:
    return SemanticMutantGuidance(
        mutant_id=mutant_id,
        mutation_type=m_type,
        line_number=line_no,
        original_expression=orig_expr,
        mutated_expression=mut_expr,
        behavioral_distinction=f"Return value expression mutated from '{orig_expr}' to '{mut_expr}'.",
        suggested_inputs=[
            "Assert exact return value equality rather than merely checking truthiness or non-None"
        ],
        confidence="HIGH"
    )


def _guidance_for_const_val(
    mutant_id: str,
    m_type: str,
    line_no: int,
    orig_expr: Optional[str],
    mut_expr: Optional[str]
) -> SemanticMutantGuidance:
    return SemanticMutantGuidance(
        mutant_id=mutant_id,
        mutation_type=m_type,
        line_number=line_no,
        original_expression=orig_expr,
        mutated_expression=mut_expr,
        behavioral_distinction=f"Constant literal mutated from '{orig_expr}' to '{mut_expr}'.",
        suggested_inputs=[
            "Assert output or internal state specifically dependent on the altered constant value"
        ],
        confidence="HIGH"
    )


def _guidance_for_except_handler(
    mutant_id: str,
    m_type: str,
    line_no: int,
    orig_expr: Optional[str],
    mut_expr: Optional[str]
) -> SemanticMutantGuidance:
    return SemanticMutantGuidance(
        mutant_id=mutant_id,
        mutation_type=m_type,
        line_number=line_no,
        original_expression=orig_expr,
        mutated_expression=mut_expr,
        behavioral_distinction=f"Exception catch handler swapped from '{orig_expr}' to '{mut_expr}'.",
        suggested_inputs=[
            "Trigger the original exception type and assert that it is handled gracefully without unhandled crash"
        ],
        confidence="HIGH"
    )


def derive_guidance_for_surviving_mutants(
    mutants: List[MutantRecord],
    target_code: Optional[str] = None
) -> List[SemanticMutantGuidance]:
    """
    Batch helper to derive semantic guidance for a list of surviving mutants.
    """
    return [derive_semantic_guidance(m, target_code=target_code) for m in mutants]


def format_guidance_for_critic(guidances: List[Union[SemanticMutantGuidance, Dict[str, Any]]]) -> str:
    """
    Formats a list of semantic guidances into structured text for Critic agent prompts.
    Supports both SemanticMutantGuidance instances and dictionary representations.
    """
    if not guidances:
        return "No surviving mutants. All AST mutants killed."

    parts = [
        f"### Semantic Guidance for {len(guidances)} Surviving Mutant(s):",
        "Target the following specific behavioral differences in your assertions:"
    ]
    for i, g in enumerate(guidances, start=1):
        if isinstance(g, dict):
            orig_s = f"'{g.get('original_expression')}'" if g.get("original_expression") else "original"
            mut_s = f"'{g.get('mutated_expression')}'" if g.get("mutated_expression") else "mutant"
            lines = [
                f"{i}. [{g.get('mutant_id', 'MUT_UNKNOWN')}] Line {g.get('line_number', 1)} ({g.get('mutation_type', 'UNKNOWN')}): {orig_s} -> {mut_s}",
                f"  - Distinction: {g.get('behavioral_distinction', '')}",
            ]
            if g.get("suggested_inputs"):
                lines.append(f"  - Suggested verification: {'; '.join(g.get('suggested_inputs', []))}")
            if g.get("uncertainty_note"):
                lines.append(f"  - Note ({g.get('confidence', 'HIGH')}): {g.get('uncertainty_note')}")
            parts.append("\n".join(lines))
        else:
            parts.append(f"{i}. {g.to_directive_text()}")
    return "\n\n".join(parts)


def format_guidance_for_generator(guidances: List[Union[SemanticMutantGuidance, Dict[str, Any]]]) -> str:
    """
    Formats a list of semantic guidances into structured text for Test Generator agent prompts.
    Supports both SemanticMutantGuidance instances and dictionary representations.
    """
    if not guidances:
        return ""
    parts = [
        f"### Surviving Mutant Semantic Guidance ({len(guidances)} Faults to Kill):"
    ]
    for g in guidances:
        if isinstance(g, dict):
            orig = f"'{g.get('original_expression')}'" if g.get("original_expression") else "original"
            mut = f"'{g.get('mutated_expression')}'" if g.get("mutated_expression") else "mutated"
            m_id = g.get("mutant_id", "MUT_UNKNOWN")
            l_no = g.get("line_number", 1)
            m_type = g.get("mutation_type", "UNKNOWN")
            b_dist = g.get("behavioral_distinction", "")
            s_inputs = g.get("suggested_inputs", [])
            item = [
                f"- [{m_id}] Line {l_no} ({m_type}): {orig} -> {mut}",
                f"  Fault mechanism: {b_dist}",
            ]
            if s_inputs:
                item.append(f"  Recommended input/boundary: {'; '.join(s_inputs)}")
            parts.append("\n".join(item))
        else:
            orig = f"'{g.original_expression}'" if g.original_expression else "original"
            mut = f"'{g.mutated_expression}'" if g.mutated_expression else "mutated"
            item = [
                f"- [{g.mutant_id}] Line {g.line_number} ({g.mutation_type}): {orig} -> {mut}",
                f"  Fault mechanism: {g.behavioral_distinction}",
            ]
            if g.suggested_inputs:
                item.append(f"  Recommended input/boundary: {'; '.join(g.suggested_inputs)}")
            parts.append("\n".join(item))
    return "\n\n".join(parts)
