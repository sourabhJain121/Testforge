"""
tests/test_agentic_rag.py

Automated test suite verifying Handout Feature F1:
Agentic RAG ("Test Knowledge Base") and Mutant Memory Subsystem.
"""

import os
import shutil
import tempfile

import pytest

from testforge.agents import TestGeneratorAgent
from testforge.rag.knowledge_retriever import (
    AgenticKnowledgeRetriever,
    RetrievalResult,
)
from testforge.rag.mutant_memory import MutantMemoryStore
from testforge.rag.vector_store import (
    TestForgeVectorStore,
    _cosine_similarity,
    _tokenize_and_vectorize,
)
from testforge.reflection_agent import ReflectionRepairAgent


@pytest.fixture
def temp_rag_dir():
    temp_dir = tempfile.mkdtemp(prefix="testforge_rag_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestVectorStore:
    def test_vectorization_and_cosine_similarity(self):
        vec1 = _tokenize_and_vectorize("pytest approx floating point comparison")
        vec2 = _tokenize_and_vectorize("pytest approx math calculation")
        vec3 = _tokenize_and_vectorize("database sql connection query")

        sim_high = _cosine_similarity(vec1, vec2)
        sim_low = _cosine_similarity(vec1, vec3)

        assert sim_high > sim_low
        assert sim_high > 0.3
        assert sim_low < 0.2

    def test_vector_store_partitions_and_defaults(self, temp_rag_dir):
        store = TestForgeVectorStore(persist_dir=temp_rag_dir)

        # Default recipes seeded in testing_patterns
        assert store.count("testing_patterns") >= 4
        assert store.count("repo_context") == 0
        assert store.count("mutant_memory") == 0

        # Query default testing recipes
        res = store.search("testing_patterns", "pytest approx float", top_k=2)
        assert len(res) > 0
        assert "approx" in res[0]["text"]
        assert res[0]["score"] > 0.3

    def test_vector_store_crud_and_persistence(self, temp_rag_dir):
        store1 = TestForgeVectorStore(persist_dir=temp_rag_dir)
        doc_id = store1.add_document(
            collection_name="repo_context",
            text="def calculate_tax(amount: float) -> float: return amount * 0.2",
            metadata={"file": "tax.py", "function": "calculate_tax"},
        )
        assert doc_id.startswith("doc_")
        assert store1.count("repo_context") == 1

        # Re-initialize store from disk
        store2 = TestForgeVectorStore(persist_dir=temp_rag_dir)
        assert store2.count("repo_context") == 1
        found = store2.search("repo_context", "calculate_tax amount", top_k=1)
        assert len(found) == 1
        assert found[0]["metadata"]["function"] == "calculate_tax"

        # Clear collection
        store2.clear("repo_context")
        assert store2.count("repo_context") == 0


class TestAgenticKnowledgeRetriever:
    def test_gating_decision(self):
        retriever = AgenticKnowledgeRetriever()

        # Trivial queries bypassed
        assert not retriever.should_retrieve("")
        assert not retriever.should_retrieve("   ")
        assert not retriever.should_retrieve("pass")
        assert not retriever.should_retrieve("test")
        assert not retriever.should_retrieve("...")

        # Meaningful queries accepted
        assert retriever.should_retrieve("pytest.approx boundary testing")
        assert retriever.should_retrieve("operator <=")
        assert retriever.should_retrieve("ZeroDivisionError exception handling")

    def test_query_reformulation(self):
        retriever = AgenticKnowledgeRetriever()

        # Diff syntax reformulation
        ref_rel = retriever.reformulate_query("- if x <= 0:\n+ if x < 0:", category="comparison_operator")
        assert "comparison" in ref_rel or "relational" in ref_rel
        assert "boundary" in ref_rel

        ref_raise = retriever.reformulate_query("+ raise ValueError('invalid')", category="exception_guard")
        assert "exception" in ref_raise or "raises" in ref_raise

    def test_chunk_relevance_grading(self):
        retriever = AgenticKnowledgeRetriever()
        chunk = {
            "score": 0.5,
            "text": "def test_tax():\n    assert calculate_tax(10.0) == 2.0\n",
            "metadata": {
                "operator_type": "comparison_operator",
                "category": "testing_patterns",
            },
        }

        grade_high = retriever.grade_chunk_relevance(chunk, "comparison_operator boundary test")
        grade_low = retriever.grade_chunk_relevance(chunk, "database network socket")

        assert grade_high > grade_low
        assert grade_high >= 0.5

    def test_retrieval_loop(self, temp_rag_dir):
        store = TestForgeVectorStore(persist_dir=temp_rag_dir)
        retriever = AgenticKnowledgeRetriever(vector_store=store)

        # Retrieve testing pattern with auto-reformulation if needed
        res: RetrievalResult = retriever.retrieve(
            query="floating point precision delta math",
            collection_name="testing_patterns",
            top_k=2,
            min_score=0.2,
        )

        assert not res.skipped_trivial
        assert len(res.chunks) > 0
        assert res.relevance_score > 0.0
        assert "approx" in res.chunks[0]["text"]


class TestMutantMemoryStore:
    def test_record_and_query_fix(self, temp_rag_dir):
        store = TestForgeVectorStore(persist_dir=temp_rag_dir)
        memory = MutantMemoryStore(vector_store=store)

        diff_sample = "- if val <= 0:\n+ if val < 0:"
        killing_patch = (
            "def test_boundary_zero():\n"
            "    with pytest.raises(ValueError):\n"
            "        target_function(0)\n"
        )

        doc_id = memory.record_successful_fix(
            operator_name="RELATIONAL_OPERATOR_REPLACEMENT",
            mutant_diff=diff_sample,
            killing_test_code=killing_patch,
            target_callable="target_function",
        )
        assert doc_id.startswith("doc_")
        assert memory.count() == 1

        # Query similar fix
        fix = memory.query_similar_fix(
            operator_name="RELATIONAL_OPERATOR_REPLACEMENT",
            mutant_diff="if val <= 0 boundary condition",
            min_score=0.2,
        )
        assert fix is not None
        assert fix["killing_test_code"] == killing_patch.strip()
        assert fix["target_callable"] == "target_function"
        assert fix["score"] > 0.2

        # Unrelated query returns None
        unrelated = memory.query_similar_fix(
            operator_name="STRING_MUTATION",
            mutant_diff="return 'hello world'",
            min_score=0.5,
        )
        assert unrelated is None


class TestAgentIntegrations:
    def test_reflection_repair_with_mutant_memory(self, temp_rag_dir):
        store = TestForgeVectorStore(persist_dir=temp_rag_dir)
        memory = MutantMemoryStore(vector_store=store)

        # Pre-seed a known fix in memory
        memory.record_successful_fix(
            operator_name="RELATIONAL_OPERATOR_REPLACEMENT",
            mutant_diff="- if x < 10:\n+ if x <= 10:",
            killing_test_code="def test_x_at_ten(): assert target(10) is False",
            target_callable="target",
        )

        agent = ReflectionRepairAgent(mutant_memory=memory)
        assert agent.mutant_memory is not None

        # Execute ToT search with a matching surviving mutant
        surviving_mutant = {
            "mutant_id": "MUT_01",
            "operator": "RELATIONAL_OPERATOR_REPLACEMENT",
            "diff": "- if x < 10:\n+ if x <= 10:",
            "line_number": 4,
        }

        tot_res = agent.repair_with_tree_of_thought(
            surviving_mutants=[surviving_mutant],
            target_source_code="def target(x): return x < 10",
        )

        assert "selected_branch" in tot_res
        assert tot_res["recalled_fix"] is not None
        assert "test_x_at_ten" in tot_res["recalled_fix"]["killing_test_code"]

    def test_generator_agent_with_rag_and_memory(self, temp_rag_dir):
        store = TestForgeVectorStore(persist_dir=temp_rag_dir)
        retriever = AgenticKnowledgeRetriever(vector_store=store)
        memory = MutantMemoryStore(vector_store=store)

        memory.record_successful_fix(
            operator_name="RELATIONAL_OPERATOR_REPLACEMENT",
            mutant_diff="val <= 10",
            killing_test_code="def test_boundary(): assert target(10) == True",
        )

        agent = TestGeneratorAgent(
            api_key="",
            mutant_memory=memory,
            rag_retriever=retriever,
        )
        assert agent.mutant_memory is not None
        assert agent.rag_retriever is not None

        # Generate test prompt with surviving diff
        suite = agent.generate_tests(
            source_code="def target(x):\n    return x > 0\n",
            surviving_diffs=["- return x > 0\n+ return x >= 0"],
        )
        assert "def test_" in suite
