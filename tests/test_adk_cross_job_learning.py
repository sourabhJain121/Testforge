"""
tests/test_adk_cross_job_learning.py

Test suite verifying Google ADK Cross-Job Memory Learning, DatabaseSessionService,
and InMemoryMemoryService integration (Sub-Task 3.1).
"""

import json
import os

import pytest

from testforge.adk_cross_job_memory import ADKCrossJobLearningOrchestrator


@pytest.mark.anyio
async def test_adk_cross_job_learning_flow(tmp_path):
    db_file = tmp_path / "test_adk_sessions.db"
    db_url = f"sqlite:///{db_file}"

    orchestrator = ADKCrossJobLearningOrchestrator(
        db_url=db_url,
        app_name="testforge_test",
        user_id="qa_tester",
    )

    # 1. Job 1: Cold start
    rec1 = await orchestrator.execute_job(
        target_path="samples/discount.py",
        session_id="job_cold_1",
        use_cross_job_memory=False,
    )
    assert rec1.iterations_run == 3
    assert rec1.reflection_turns == 2
    assert rec1.memories_retrieved == 0
    assert rec1.killed_mutants == 19
    assert rec1.final_adjusted_mutation_score == 100.0

    # 2. Job 2: Warm start
    rec2 = await orchestrator.execute_job(
        target_path="samples/discount.py",
        session_id="job_warm_2",
        use_cross_job_memory=True,
    )
    assert rec2.iterations_run == 1
    assert rec2.reflection_turns == 0
    assert rec2.memories_retrieved >= 2
    assert rec2.killed_mutants == 19
    assert rec2.final_adjusted_mutation_score == 100.0

    # 3. Evidence comparison
    evidence_path = tmp_path / "EVIDENCE.json"
    evidence = orchestrator.save_evidence(str(evidence_path))
    assert os.path.exists(evidence_path)

    impact = evidence["cross_job_learning_impact"]
    assert impact["turn_reduction"] == 2
    assert impact["turn_reduction_percent"] == 66.67
    assert impact["reflection_turn_reduction"] == 2
    assert impact["memory_reuse_verified"] is True


@pytest.mark.anyio
async def test_database_session_service_sqlite_persistence(tmp_path):
    db_file = tmp_path / "sqlite_test.db"
    db_url = f"sqlite:///{db_file}"

    orchestrator = ADKCrossJobLearningOrchestrator(
        db_url=db_url,
        app_name="testforge_test",
        user_id="qa_tester",
    )

    await orchestrator.execute_job(
        target_path="samples/discount.py",
        session_id="job_session_check",
        use_cross_job_memory=False,
    )

    # Verify session can be retrieved from database
    retrieved = await orchestrator.session_service.get_session(
        app_name="testforge_test",
        user_id="qa_tester",
        session_id="job_session_check",
    )
    assert retrieved is not None
    assert retrieved.id == "job_session_check"
    assert retrieved.state["target_name"] == "discount.py"
    assert len(retrieved.events) >= 2


@pytest.mark.anyio
async def test_adk_memory_service_query_filtering(tmp_path):
    db_file = tmp_path / "filter_test.db"
    orchestrator = ADKCrossJobLearningOrchestrator(
        db_url=f"sqlite:///{db_file}",
        app_name="testforge_filter",
        user_id="tester",
    )

    # Run Job 1 to index memory
    await orchestrator.execute_job(
        target_path="samples/discount.py",
        session_id="job_seed_memory",
        use_cross_job_memory=False,
    )

    # Query matching keywords
    matching_res = await orchestrator.memory_service.search_memory(
        app_name="testforge_filter",
        user_id="tester",
        query="boundary price",
    )
    assert len(matching_res.memories) > 0

    # Query completely unrelated keywords
    unrelated_res = await orchestrator.memory_service.search_memory(
        app_name="testforge_filter",
        user_id="tester",
        query="quantum mechanics cryptography nonexistingkeyword",
    )
    assert len(unrelated_res.memories) == 0
