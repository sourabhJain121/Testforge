"""
testforge.corpus - Evaluation Corpus & Defect Manifest Module for TestForge (GAP-04).
"""

from testforge.corpus.manager import (
    CORPUS_REGISTRY,
    evaluate_entire_corpus,
    evaluate_fixture,
    export_benchmark_corpus_results_json,
    export_corpus_manifest_csv,
    export_defect_manifest_csv,
    get_corpus_fixtures,
    get_fixture,
)
from testforge.corpus.models import (
    CorpusFixture,
    DefectDetectionReport,
    DefectVariant,
    FixtureEvaluationResult,
    compute_sha256,
)
from testforge.corpus.runner import (
    CorpusBenchmarkReport,
    CorpusBenchmarkRunner,
    StrategyRunRecord,
    StrategyStatisticalSummary,
    export_raw_run_results_json,
    export_strategy_comparison_csv,
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
