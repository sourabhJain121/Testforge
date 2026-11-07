"""
tests/test_evaluation_corpus_hardening.py

Regression test suite verifying Stage 0.5 corpus hardening and guardrails performance:
- 100% detection rate on 30 malicious Python vectors across 5 categories
- 0% false positive rate on 40 fresh real-world benign OSS patterns
- 0% false positive rate on 20 held-out benign files
- 100% detection rate on 20 public prompt injection attacks
- 100% defusal rate on indirect prompt injections embedded in comments
- Integrity of qa_artifacts/SECURITY_EVALUATION_REPORT.json
"""

import json
from pathlib import Path

import pytest

from testforge.prompt_guard import inspect_source_for_indirect_injections
from testforge.security import SecurityGuardrail, SecurityPolicy

CORPUS_ROOT = Path("testforge/evaluation_corpus")


@pytest.fixture
def strict_guardrail():
    return SecurityGuardrail(policy=SecurityPolicy.default_strict())


def test_malicious_corpus_100_percent_detection(strict_guardrail):
    """Verify that all 30 malicious files are intercepted and blocked by AST inspection."""
    mal_dir = CORPUS_ROOT / "malicious"
    assert mal_dir.is_dir(), "Malicious evaluation corpus directory must exist"
    
    mal_files = sorted(list(mal_dir.glob("*.py")))
    assert len(mal_files) == 30, f"Expected 30 malicious samples, found {len(mal_files)}"

    blocked_files = []
    for f in mal_files:
        code = f.read_text(encoding="utf-8")
        res = strict_guardrail.inspect_code_ast(code)
        if not res.allowed or len(res.violations) > 0:
            blocked_files.append(f.name)

    assert len(blocked_files) == 30, (
        f"Expected all 30 malicious files blocked, but {30 - len(blocked_files)} escaped: "
        f"{set(f.name for f in mal_files) - set(blocked_files)}"
    )


def test_fresh_benign_corpus_zero_false_positives(strict_guardrail):
    """Verify that 40 real-world fresh benign patterns yield 0 false positives."""
    ben_dir = CORPUS_ROOT / "benign_fresh"
    assert ben_dir.is_dir(), "Benign fresh corpus directory must exist"

    ben_files = sorted(list(ben_dir.glob("*.py")))
    assert len(ben_files) == 40, f"Expected 40 benign fresh samples, found {len(ben_files)}"

    for f in ben_files:
        code = f.read_text(encoding="utf-8")
        res = strict_guardrail.inspect_code_ast(code)
        assert res.allowed is True, (
            f"Benign file '{f.name}' was falsely blocked with violations: "
            f"{[v.rule_id + ': ' + v.message for v in res.violations]}"
        )
        assert len(res.violations) == 0


def test_held_out_benign_corpus_zero_false_positives(strict_guardrail):
    """Verify that 20 held-out benign samples yield 0 false positives."""
    held_dir = CORPUS_ROOT / "benign_heldout"
    assert held_dir.is_dir(), "Held-out benign corpus directory must exist"

    held_files = sorted(list(held_dir.glob("*.py")))
    assert len(held_files) == 20, f"Expected 20 held-out samples, found {len(held_files)}"

    for f in held_files:
        code = f.read_text(encoding="utf-8")
        res = strict_guardrail.inspect_code_ast(code)
        assert res.allowed is True, f"Held-out file '{f.name}' was falsely blocked"
        assert len(res.violations) == 0


def test_prompt_injections_100_percent_direct_detection(strict_guardrail):
    """Verify that all 20 public prompt injection samples are identified by direct prompt inspection."""
    inj_dir = CORPUS_ROOT / "prompt_injections"
    assert inj_dir.is_dir(), "Prompt injections directory must exist"

    inj_files = sorted(list(inj_dir.glob("*.txt")))
    assert len(inj_files) == 20, f"Expected 20 prompt injection files, found {len(inj_files)}"

    for f in inj_files:
        text = f.read_text(encoding="utf-8").strip()
        res = strict_guardrail.inspect_prompt(text)
        assert not res.allowed or len(res.findings) > 0, (
            f"Prompt injection '{f.name}' was not detected: '{text}'"
        )


def test_prompt_injections_100_percent_indirect_defusal(strict_guardrail):
    """Verify that all 20 prompt injections embedded as comments in code are neutralized by AST inspection."""
    inj_dir = CORPUS_ROOT / "prompt_injections"
    inj_files = sorted(list(inj_dir.glob("*.txt")))

    for f in inj_files:
        text = f.read_text(encoding="utf-8").strip()
        commented = "\n".join(f"# {line}" for line in text.splitlines())
        code = f"{commented}\ndef calc(x: int) -> int:\n    return x * 10\n"
        res = inspect_source_for_indirect_injections(code, guardrail=strict_guardrail)
        assert res.has_injection is True, f"Indirect injection not detected for '{f.name}'"
        assert "[DEFUSED_PROMPT_INJECTION" in res.defused_text


def test_security_evaluation_report_artifact_integrity():
    """Verify that the generated SECURITY_EVALUATION_REPORT.json exists and contains verified metrics."""
    report_file = Path("qa_artifacts/SECURITY_EVALUATION_REPORT.json")
    assert report_file.exists(), "SECURITY_EVALUATION_REPORT.json must exist in qa_artifacts/"

    data = json.loads(report_file.read_text(encoding="utf-8"))
    summary = data["summary"]

    assert summary["true_positive_rate_pct"] == 100.0
    assert summary["malicious_detected"] == 30
    assert summary["benign_fresh_false_positive_rate_pct"] == 0.0
    assert summary["benign_fresh_false_positives"] == 0
    assert summary["benign_heldout_false_positive_rate_pct"] == 0.0
    assert summary["prompt_injections_direct_detection_rate_pct"] == 100.0
    assert summary["prompt_injections_indirect_defusal_rate_pct"] == 100.0
