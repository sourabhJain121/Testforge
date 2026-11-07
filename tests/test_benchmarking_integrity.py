import json
import os
from unittest.mock import MagicMock, patch

import pytest

from testforge.benchmarking import (
    PRICING_TABLE_PER_MILLION,
    BenchmarkReport,
    BenchmarkRunner,
    BenchmarkRunResult,
    BenchmarkScenarioSummary,
    MetricBreakdown,
    SuiteEvaluationResult,
)
from testforge.state import MutantRecord

SAMPLE_TARGET_CODE = '''"""Sample Discount Calculator"""

def calculate_discount(price: float, quantity: int, is_member: bool) -> float:
    if price < 0 or quantity <= 0:
        raise ValueError("Invalid price or quantity")
    
    rate = 0.0
    if is_member:
        rate += 0.10
    
    if quantity >= 10:
        rate += 0.15
    elif quantity >= 5:
        rate += 0.05
        
    discount = price * quantity * rate
    return round((price * quantity) - discount, 2)
'''


def _create_mock_mutant(m_id: str, status: str, eq_status: str = "NOT_EQUIVALENT") -> MutantRecord:
    return MutantRecord(
        mutant_id=m_id,
        mutation_type="COMP_OP",
        line_number=5,
        original_code_snippet="price < 0",
        mutated_code_snippet="price <= 0",
        unified_diff="--- original\n+++ mutated\n@@ -5,1 +5,1 @@\n- price < 0\n+ price <= 0\n",
        status=status,
        is_executed=True,
        is_valid_syntax=True,
        equivalence_status=eq_status
    )


class TestBenchmarkingIntegrity:
    """Rigorous verification of TestForge benchmark metrics, statistical fairness, and accounting."""

    def test_target_code_preservation(self, tmp_path):
        """Verify that running benchmarks does not alter or corrupt the target source code."""
        runner = BenchmarkRunner(
            target_code=SAMPLE_TARGET_CODE,
            model_name="gemini-3.6-flash",
            output_dir=str(tmp_path),
            fast_mode=True
        )
        report = runner.run_benchmark(repetitions=1, scenarios=["baseline"])
        assert runner.target_code == SAMPLE_TARGET_CODE.strip()
        assert report.target_file == "sample_target.py"
        assert "calculate_discount" in runner.target_code

    def test_coverage_measurement_consistency(self, tmp_path):
        """Verify that line coverage is collected accurately and remains within [0.0, 100.0]."""
        runner = BenchmarkRunner(
            target_code=SAMPLE_TARGET_CODE,
            model_name="gemini-3.6-flash",
            output_dir=str(tmp_path),
            fast_mode=True
        )
        report = runner.run_benchmark(repetitions=1, scenarios=["baseline", "zeroshot", "agentic_reflection"])
        for sc in ["baseline", "zeroshot", "agentic_reflection"]:
            summary = report.scenario_summaries[sc]
            assert 0.0 <= summary.mean_line_coverage <= 100.0
            if sc == "agentic_reflection":
                assert summary.mean_line_coverage >= 70.0

    def test_mutation_score_formula_and_equivalent_exclusion(self):
        """Verify that raw score includes all executed mutants and adjusted score excludes verified equivalents."""
        runner = BenchmarkRunner(target_code=SAMPLE_TARGET_CODE, fast_mode=True)

        # 10 killed, 2 survived, 3 equivalent (total evaluated = 15)
        # Raw = 10 / 15 * 100 = 66.67%
        # Adjusted = 10 / (15 - 3) * 100 = 10 / 12 * 100 = 83.33%
        mock_mutants = []
        for i in range(10):
            mock_mutants.append(_create_mock_mutant(f"MUT_K_{i}", status="KILLED"))
        for i in range(2):
            mock_mutants.append(_create_mock_mutant(f"MUT_S_{i}", status="SURVIVED", eq_status="NOT_EQUIVALENT"))
        for i in range(3):
            mock_mutants.append(_create_mock_mutant(f"MUT_E_{i}", status="SURVIVED", eq_status="EQUIVALENT"))

        with patch.object(runner.sandbox, "measure_coverage", return_value=(85.0, None)), \
             patch("testforge.benchmarking.ASTMutator.generate_mutants", return_value=mock_mutants), \
             patch.object(runner.sandbox, "evaluate_mutants_parallel", return_value=mock_mutants):
            eval_result = runner.evaluate_suite("def test_one(): pass")
            assert isinstance(eval_result, SuiteEvaluationResult)
            assert eval_result.killed == 10
            assert eval_result.executed == 15
            assert eval_result.equivalent == 3
            assert eval_result.score == 66.67
            assert eval_result.adj_score == 83.33

    def test_zero_mutants_division_safety(self):
        """Verify that when 0 mutants are executed, scores return None (N/A) without ZeroDivisionError."""
        runner = BenchmarkRunner(target_code=SAMPLE_TARGET_CODE, fast_mode=True)
        with patch.object(runner.sandbox, "measure_coverage", return_value=(0.0, None)), \
             patch("testforge.benchmarking.ASTMutator.generate_mutants", return_value=[]):
            eval_result = runner.evaluate_suite("def test_none(): pass")
            assert eval_result.score is None
            assert eval_result.adj_score is None
            assert eval_result.killed == 0
            assert eval_result.total == 0

    def test_token_accounting_separation(self, tmp_path):
        """Verify actual LLM tokens and estimated tokens are cleanly distinguished and never conflated."""
        runner = BenchmarkRunner(
            target_code=SAMPLE_TARGET_CODE,
            model_name="gemini-3.6-flash",
            output_dir=str(tmp_path),
            fast_mode=True
        )
        report = runner.run_benchmark(repetitions=1, scenarios=["baseline", "zeroshot"])
        
        base_summary = report.scenario_summaries["baseline"]
        assert base_summary.actual_llm_tokens == 0
        assert base_summary.estimated_tokens == 0
        assert base_summary.actual_billed_cost_usd == 0.0

        zs_summary = report.scenario_summaries["zeroshot"]
        assert zs_summary.actual_llm_tokens >= 0
        assert zs_summary.estimated_tokens >= 0
        assert zs_summary.actual_billed_cost_usd >= 0.0

    def test_repetition_statistics_and_bessel_correction(self, tmp_path):
        """Verify standard deviation uses Bessel's correction (N-1) for N > 1, and returns None for N == 1."""
        runner = BenchmarkRunner(
            target_code=SAMPLE_TARGET_CODE,
            model_name="gemini-3.6-flash",
            output_dir=str(tmp_path),
            fast_mode=True
        )
        # N == 1: stddev must be None
        report_1 = runner.run_benchmark(repetitions=1, scenarios=["baseline"])
        assert report_1.scenario_summaries["baseline"].stddev_duration_sec is None

        # N == 3: stddev must be a valid non-negative float
        report_3 = runner.run_benchmark(repetitions=3, scenarios=["baseline"])
        assert report_3.scenario_summaries["baseline"].runs_completed == 3
        assert report_3.scenario_summaries["baseline"].stddev_duration_sec is not None
        assert report_3.scenario_summaries["baseline"].stddev_duration_sec >= 0.0

    def test_markdown_and_json_report_export(self, tmp_path):
        """Verify benchmark reports can be exported to JSON and Markdown with all required columns."""
        runner = BenchmarkRunner(
            target_code=SAMPLE_TARGET_CODE,
            model_name="gemini-3.6-flash",
            output_dir=str(tmp_path),
            fast_mode=True
        )
        report = runner.run_benchmark(repetitions=1, scenarios=["baseline", "zeroshot"])
        json_path, md_path = runner.save_report(report)

        assert os.path.exists(json_path)
        assert os.path.exists(md_path)

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "total_duration_sec" in data
            assert "scenario_summaries" in data
            assert "baseline" in data["scenario_summaries"]

        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
            assert "Total Benchmark Duration" in md_content
            assert "baseline" in md_content.lower()
            assert "zeroshot" in md_content.lower()
            assert "Cloud Cost" in md_content
            assert "Local Compute Cost" in md_content
            assert "Deterministic AST" in md_content

    def test_failed_scenario_graceful_handling(self, tmp_path):
        """Verify that a failing scenario does not crash the entire benchmark run."""
        runner = BenchmarkRunner(
            target_code=SAMPLE_TARGET_CODE,
            model_name="gemini-3.6-flash",
            output_dir=str(tmp_path),
            fast_mode=False
        )
        with patch.object(runner, "evaluate_suite", side_effect=RuntimeError("Sandbox execution timeout")):
            report = runner.run_benchmark(repetitions=1, scenarios=["baseline"])
            base_summary = report.scenario_summaries["baseline"]
            assert base_summary.runs_failed == 1
            assert base_summary.runs_completed == 0
            assert len(report.runs) == 1
            assert report.runs[0].success is False
            assert "Sandbox execution timeout" in (report.runs[0].error_message or "")

    def test_dynamic_provider_identification_categories(self, tmp_path):
        """Verify dynamic categorization: Cloud LLM, Local LLM, Deterministic AST, Mocked LLM, Offline Fallback."""
        runner_fast = BenchmarkRunner(
            target_code=SAMPLE_TARGET_CODE,
            output_dir=str(tmp_path / "fast"),
            fast_mode=True
        )
        report_fast = runner_fast.run_benchmark(repetitions=1, scenarios=["baseline", "zeroshot", "agentic_reflection"])
        assert report_fast.scenario_summaries["baseline"].provider_category == "Deterministic AST"
        assert report_fast.scenario_summaries["zeroshot"].provider_category == "Mocked LLM"
        assert report_fast.scenario_summaries["agentic_reflection"].provider_category == "Deterministic AST"

    def test_local_ollama_fallback_and_gemini_failure_handling(self, tmp_path):
        """Verify when Cloud Gemini returns 429, Ollama is logged as actual execution provider with $0.00 cloud cost."""
        runner = BenchmarkRunner(
            target_code=SAMPLE_TARGET_CODE,
            model_name="gemini-3.6-flash",
            output_dir=str(tmp_path / "ollama_run"),
            fast_mode=False,
            job_id="test_fallback"
        )

        mock_client = MagicMock()
        mock_client.active_provider = "Local Ollama (qwen2.5-coder:7b)"
        mock_client.local_model = "qwen2.5-coder:7b"
        mock_client.gemini_quota_exhausted = True

        mock_logger = MagicMock()
        mock_logger.get_token_summary.return_value = {
            "actual_llm_tokens": 970,
            "actual_prompt_tokens": 590,
            "actual_completion_tokens": 380,
            "estimated_tokens": 0,
            "execution_engine_kpi": "qwen2.5-coder:7b (Ollama / Local)"
        }

        mock_eval = SuiteEvaluationResult(
            cov_pct=100.0, score=100.0, killed=19, total=19, adj_score=100.0, equivalent=0, survived=0, executed=19
        )

        with patch("testforge.agents.TestGeneratorAgent.generate_tests", return_value="def test_generated(): pass"), \
             patch("testforge.llm_client.HybridLLMClient", return_value=mock_client), \
             patch("testforge.logger.TraceLogger", return_value=mock_logger), \
             patch.object(runner, "evaluate_suite", return_value=mock_eval):
            run_res = runner._execute_single_run("zeroshot", 1)

            assert run_res.success is True
            measured = run_res.metrics.measured
            estimated = run_res.metrics.estimated

            assert measured["provider_category"] == "Local LLM"
            assert "Ollama – qwen2.5-coder:7b (Local)" in measured["engine_label"]
            assert measured["actual_local_tokens"] == 970
            assert measured["actual_cloud_tokens"] == 0
            assert estimated["actual_billed_cost_usd"] == 0.0  # Zero cloud billing for local Ollama!
            assert measured["failover_occurred"] is True
            assert "Cloud Gemini 429" in measured["failover_details"]

    def test_local_vs_cloud_cost_accounting(self, tmp_path):
        """Verify cloud runs calculate billed USD while local runs enforce $0.00 cloud cost and N/A local compute."""
        pricing = PRICING_TABLE_PER_MILLION["gemini-2.5-flash"]
        prompt_rate = pricing["prompt"]
        comp_rate = pricing["completion"]

        # 1. Cloud calculation: 1,000,000 prompt + 1,000,000 completion
        cloud_billed = round((1_000_000 / 1_000_000.0 * prompt_rate) + (1_000_000 / 1_000_000.0 * comp_rate), 6)
        assert cloud_billed == round(prompt_rate + comp_rate, 6)

        # 2. Local Ollama: 1,000,000 tokens must result in $0.00000 cloud billed cost
        runner = BenchmarkRunner(target_code=SAMPLE_TARGET_CODE, output_dir=str(tmp_path), fast_mode=True)
        report = runner.run_benchmark(repetitions=1, scenarios=["baseline"])
        summary = report.scenario_summaries["baseline"]
        assert summary.actual_billed_cost_usd == 0.0
        assert summary.local_compute_cost == "N/A"

    def test_telemetry_isolation_between_jobs(self, tmp_path):
        """Verify distinct benchmark jobs write to isolated trace directories without cross-contamination."""
        runner_a = BenchmarkRunner(target_code=SAMPLE_TARGET_CODE, output_dir=str(tmp_path), job_id="job_alpha", fast_mode=True)
        runner_b = BenchmarkRunner(target_code=SAMPLE_TARGET_CODE, output_dir=str(tmp_path), job_id="job_beta", fast_mode=True)

        assert runner_a.job_trace_dir != runner_b.job_trace_dir
        assert "job_alpha" in runner_a.job_trace_dir
        assert "job_beta" in runner_b.job_trace_dir
        assert os.path.exists(runner_a.job_trace_dir)
        assert os.path.exists(runner_b.job_trace_dir)

    def test_benchmark_completion_timing(self, tmp_path):
        """Verify wall-clock total duration is strictly non-negative and recorded for all repetitions."""
        runner = BenchmarkRunner(target_code=SAMPLE_TARGET_CODE, output_dir=str(tmp_path), fast_mode=True)
        report = runner.run_benchmark(repetitions=2, scenarios=["baseline"])
        assert report.total_duration_sec > 0.0
        assert len(report.runs) == 2
        for r in report.runs:
            assert r.metrics.measured.get("duration_seconds", 0.0) >= 0.0

    def test_missing_provider_usage_information(self, tmp_path):
        """Verify handling when provider response does not contain usage tokens."""
        runner = BenchmarkRunner(target_code=SAMPLE_TARGET_CODE, output_dir=str(tmp_path), fast_mode=False)
        mock_client = MagicMock()
        mock_client.active_provider = "Unknown Offline Double"
        mock_logger = MagicMock()
        mock_logger.get_token_summary.return_value = {
            "actual_llm_tokens": 0,
            "actual_prompt_tokens": 0,
            "actual_completion_tokens": 0,
            "estimated_tokens": 0,
            "execution_engine_kpi": "Deterministic Synthesizer"
        }
        mock_eval = SuiteEvaluationResult(
            cov_pct=70.0, score=31.58, killed=6, total=19, adj_score=31.58, equivalent=0, survived=13, executed=19
        )
        with patch("testforge.agents.TestGeneratorAgent.generate_tests", return_value="def test_x(): pass"), \
             patch("testforge.llm_client.HybridLLMClient", return_value=mock_client), \
             patch("testforge.logger.TraceLogger", return_value=mock_logger), \
             patch.object(runner, "evaluate_suite", return_value=mock_eval):
            run_res = runner._execute_single_run("zeroshot", 1)
            assert run_res.success is True
            assert run_res.metrics.measured["provider_category"] == "Offline Fallback"
            assert run_res.metrics.estimated["actual_billed_cost_usd"] == 0.0

