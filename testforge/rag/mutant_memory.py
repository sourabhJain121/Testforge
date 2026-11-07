"""
testforge/rag/mutant_memory.py

Mutant Memory Store for TestForge (Handout Feature F1).
Indexes historical surviving mutant diffs paired with the verified test patches
that killed them, enabling instant, cross-iteration recall and repair acceleration.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from testforge.rag.knowledge_retriever import AgenticKnowledgeRetriever, RetrievalResult
from testforge.rag.vector_store import TestForgeVectorStore

logger = logging.getLogger("testforge.rag.mutant_memory")


class MutantMemoryStore:
    """
    Dedicated store and retriever for historical mutant diffs and their killing test patches.
    Integrates with TestForgeVectorStore under the 'mutant_memory' partition.
    """

    def __init__(
        self,
        vector_store: Optional[TestForgeVectorStore] = None,
        retriever: Optional[AgenticKnowledgeRetriever] = None,
    ):
        self.vector_store = vector_store or TestForgeVectorStore()
        self.retriever = retriever or AgenticKnowledgeRetriever(vector_store=self.vector_store)

    def record_successful_fix(
        self,
        operator_name: str,
        mutant_diff: str,
        killing_test_code: str,
        target_callable: Optional[str] = None,
        doc_id: Optional[str] = None,
    ) -> str:
        """
        Records a successful mutant kill into the mutant_memory vector store partition.
        Pairs the operator type and unified diff with the winning test code snippet.
        """
        clean_op = str(operator_name or "UNKNOWN").strip()
        clean_diff = str(mutant_diff or "").strip()
        clean_code = str(killing_test_code or "").strip()
        callable_name = str(target_callable or "unknown").strip()

        text = (
            f"Operator: {clean_op}\n"
            f"Callable: {callable_name}\n"
            f"Mutant Diff:\n{clean_diff}\n"
            f"Killing Test Patch:\n{clean_code}"
        )

        metadata = {
            "operator_type": clean_op,
            "target_callable": callable_name,
            "mutant_diff": clean_diff,
            "killing_test_code": clean_code,
            "category": "mutant_memory",
        }

        stored_id = self.vector_store.add_document(
            collection_name="mutant_memory",
            text=text,
            doc_id=doc_id,
            metadata=metadata,
        )
        logger.info(
            f"MutantMemoryStore: Recorded winning fix [ID: {stored_id}] for operator '{clean_op}' "
            f"in callable '{callable_name}'."
        )
        return stored_id

    def query_similar_fix(
        self,
        operator_name: str,
        mutant_diff: str,
        min_score: float = 0.3,
    ) -> Optional[Dict[str, Any]]:
        """
        Queries historical mutant memory for a previously successful test patch
        targeting the same or structurally similar mutant diff.
        """
        if not operator_name and not mutant_diff:
            return None

        query_str = f"{operator_name} {mutant_diff}".strip()
        retrieval: RetrievalResult = self.retriever.retrieve(
            query=query_str,
            collection_name="mutant_memory",
            top_k=1,
            min_score=min_score,
            category=operator_name,
        )

        if not retrieval.chunks:
            return None

        best_chunk = retrieval.chunks[0]
        meta = best_chunk.get("metadata", {})
        killing_code = meta.get("killing_test_code", "")

        if not killing_code:
            return None

        return {
            "doc_id": best_chunk.get("doc_id"),
            "operator": meta.get("operator_type", operator_name),
            "target_callable": meta.get("target_callable", ""),
            "mutant_diff": meta.get("mutant_diff", mutant_diff),
            "killing_test_code": killing_code,
            "score": best_chunk.get("relevance_score", best_chunk.get("score", 0.0)),
        }

    def count(self) -> int:
        """Returns the total number of recorded mutant fixes in memory."""
        return self.vector_store.count("mutant_memory")

    def clear(self) -> None:
        """Clears all historical records in the mutant_memory partition."""
        self.vector_store.clear("mutant_memory")

    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieves all indexed mutant memory records."""
        return self.vector_store.get_collection("mutant_memory")

