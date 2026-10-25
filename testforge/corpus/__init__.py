"""
testforge.corpus - Evaluation Corpus & Defect Manifest Module for TestForge (GAP-04).
"""

from testforge.corpus.models import (
    CorpusFixture,
    DefectVariant,
    DefectDetectionReport,
    FixtureEvaluationResult,
    compute_sha256,
)
from testforge.corpus.manager import (
    CORPUS_REGISTRY,
    get_corpus_fixtures,
    get_fixture,
    evaluate_fixture,
    evaluate_entire_corpus,
    export_corpus_manifest_csv,
    export_defect_manifest_csv,
    export_benchmark_corpus_results_json,
)
from testforge.corpus.runner import (
    StrategyRunRecord,
    StrategyStatisticalSummary,
    CorpusBenchmarkReport,
    CorpusBenchmarkRunner,
    export_strategy_comparison_csv,
    export_raw_run_results_json,
)

__all__ = [
    "CorpusFixture",
    "DefectVariant",
    "DefectDetectionReport",
    "FixtureEvaluationResult",
    "compute_sha256",
    "CORPUS_REGISTRY",
    "get_corpus_fixtures",
    "get_fixture",
    "evaluate_fixture",
    "evaluate_entire_corpus",
    "export_corpus_manifest_csv",
    "export_defect_manifest_csv",
    "export_benchmark_corpus_results_json",
    "StrategyRunRecord",
    "StrategyStatisticalSummary",
    "CorpusBenchmarkReport",
    "CorpusBenchmarkRunner",
    "export_strategy_comparison_csv",
    "export_raw_run_results_json",
]
