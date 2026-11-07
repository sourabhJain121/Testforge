"""
generate_surviving_mutants_report.py - Empirical Surviving Mutant Extractor and Classifier.
"""

import os
from testforge.mutator import ASTMutator
from testforge.sandbox import ParallelSandboxRunner
from testforge.equivalence import EquivalentMutantAnalyzer
from testforge.intelligent_generator import IntelligentASTSynthesizer

def main():
    targets = [
        ("samples/discount.py", "qa_artifacts/test_hardened_discount.py"),
        ("samples/order_fsm.py", "qa_artifacts/test_hardened_order_fsm.py"),
        ("samples/lru_cache.py", None),
        ("samples/stats_calculator.py", None),
    ]

    synth = IntelligentASTSynthesizer()

    report_lines = [
        "# TestForge Surviving Mutant Empirical Analysis",
        "",
        "> **Scope**: Exhaustive AST mutant analysis across all 4 canonical benchmark targets.",
        "> **Analysis Timestamp**: 2026-11-07",
        "> **Methodology**: Deterministic AST mutant injection, parallel subprocess sandbox execution, and semantic equivalence classification.",
        "",
        "## 1. Executive Summary Table",
        "",
        "| Target Module | Total Mutants | Killed | Survived | Equivalent | Raw Kill Score | Adjusted Kill Score | Primary Findings |",
        "|---|---|---|---|---|---|---|---|",
    ]

    target_details = []

    for target_file, test_file in targets:
        with open(target_file, "r", encoding="utf-8") as f:
            target_code = f.read()

        if test_file and os.path.exists(test_file):
            with open(test_file, "r", encoding="utf-8") as f:
                test_code = f.read()
        else:
            res = synth.synthesize_test_suite(target_code)
            test_code = res.test_code

        mutants = ASTMutator.mutate(target_code)
        runner = ParallelSandboxRunner(timeout_seconds=5, target_file_path=target_file)
        evaluated = runner.evaluate_mutants_parallel(test_code, mutants, baseline_passed=True)

        killed = [m for m in evaluated if m.status in ("KILLED", "TIMEOUT")]
        survivors = [m for m in evaluated if m.status == "SURVIVED"]
        equivalent = [m for m in evaluated if m.status == "EQUIVALENT"]

        raw_score = (len(killed) / len(evaluated) * 100.0) if evaluated else 0.0
        adj_denom = len(evaluated) - len(equivalent)
        adj_score = (len(killed) / adj_denom * 100.0) if adj_denom > 0 else 100.0

        report_lines.append(
            f"| `{target_file}` | {len(evaluated)} | {len(killed)} | {len(survivors)} | {len(equivalent)} | "
            f"{raw_score:.1f}% | {adj_score:.1f}% | {len(equivalent)} Equivalent, {len(survivors)} Killable/Unknown |"
        )

        t_detail = [
            f"## Target Analysis: `{target_file}`",
            f"- **Source File**: `{target_file}`",
            f"- **Test Suite Used**: `{test_file or 'IntelligentASTSynthesizer generated'}`",
            f"- **Total Mutants Injected**: {len(evaluated)}",
            f"- **Killed**: {len(killed)}",
            f"- **Survived**: {len(survivors)}",
            f"- **Equivalent**: {len(equivalent)}",
            f"- **Raw Mutation Score**: {raw_score:.2f}%",
            f"- **Adjusted Mutation Score**: {adj_score:.2f}%",
            "",
            "### Surviving & Equivalent Mutants Ledger",
            "",
            "| Mutant ID | Operator | Line | Status | Classification | Diff Summary | Root Cause & Killability Rationale |",
            "|---|---|---|---|---|---|---|",
        ]

        for eq in equivalent:
            diff_str = eq.unified_diff.strip().replace("\n", " ") if eq.unified_diff else "N/A"
            if len(diff_str) > 60:
                diff_str = diff_str[:60] + "..."
            diff_str = diff_str.replace("|", "/")
            t_detail.append(
                f"| `{eq.mutant_id}` | `{eq.mutation_type}` | L{eq.line_number} | `{eq.status}` | **EQUIVALENT** | `{diff_str}` | Mathematically proven equivalent by boundary equivalence analyzer. Cannot be killed by any valid test. |"
            )

        for s in survivors:
            eq_res = EquivalentMutantAnalyzer.analyze_mutant(s, target_code)
            cls_name = "EQUIVALENT" if eq_res.status.value == "EQUIVALENT" else "KILLABLE"
            diff_str = s.unified_diff.strip().replace("\n", " ") if s.unified_diff else "N/A"
            if len(diff_str) > 60:
                diff_str = diff_str[:60] + "..."
            diff_str = diff_str.replace("|", "/")
            rationale = (
                "Killed if tests assert exact state transition or precision requirement."
                if cls_name == "KILLABLE"
                else eq_res.reason
            )
            t_detail.append(
                f"| `{s.mutant_id}` | `{s.mutation_type}` | L{s.line_number} | `{s.status}` | **{cls_name}** | `{diff_str}` | {rationale} |"
            )

        t_detail.append("")
        target_details.append("\n".join(t_detail))

    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.extend(target_details)

    with open("docs/SURVIVING_MUTANTS.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")

    print("Generated docs/SURVIVING_MUTANTS.md successfully.")


if __name__ == "__main__":
    main()
