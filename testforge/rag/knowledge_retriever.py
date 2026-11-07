"""
testforge/rag/knowledge_retriever.py

Agentic Knowledge Retriever with Query Reformulation, Chunk Grading, and Fallback.
Part of Handout Feature F1: Agentic RAG System for TestForge.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from testforge.rag.vector_store import TestForgeVectorStore

logger = logging.getLogger("testforge.rag.knowledge_retriever")


class RetrievalResult(BaseModel):
    """Structured result returned by the Agentic Knowledge Retriever."""
    chunks: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved and graded document chunks")
    query_used: str = Field(default="", description="Effective query string executed against vector store")
    reformulated: bool = Field(default=False, description="Whether query reformulation was triggered")
    relevance_score: float = Field(default=0.0, description="Highest relevance score among retrieved chunks")
    skipped_trivial: bool = Field(default=False, description="Whether retrieval was bypassed due to triviality")

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)


class AgenticKnowledgeRetriever:
    """
    Intelligent retrieval controller enforcing:
      1. Trivial Query Gating (skip trivial queries to save overhead)
      2. Semantic Query Reformulation (rewrite raw code diffs to canonical keyword concepts)
      3. Chunk Relevance Grading (score and filter out irrelevant knowledge chunks)
    """

    # Mapping of raw code diff tokens to canonical semantic search keywords
    DIFF_REFORMULATION_PATTERNS = [
        (r"(?:==|!=|<=|>=|<|>)", "relational operator boundary inversion comparison off by one"),
        (r"(?:\*|\+|\-|\/|%)", "arithmetic operator calculation precision floating point"),
        (r"(?:raise\s+\w+|try|except)", "pytest raises exception guard negative testing validation error"),
        (r"(?:and|or|not)", "logical connective boolean condition branch inversion"),
        (r"(?:return\s+None|return\s+True|return\s+False)", "return value predicate invariant boundary"),
    ]

    def __init__(self, vector_store: Optional[TestForgeVectorStore] = None):
        self.vector_store = vector_store or TestForgeVectorStore()

    def should_retrieve(self, query: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Decision Gate: Evaluates whether retrieval should be executed or bypassed.
        Bypasses empty, whitespace, or trivial single-keyword pass-throughs.
        """
        if not query or not query.strip():
            return False
        clean = query.strip().lower()
        if clean in ("pass", "none", "true", "false", "return", "...", "test"):
            return False
        if len(clean) < 4 and not any(op in clean for op in ("<", ">", "==", "!=")):
            return False
        return True

    def reformulate_query(self, query: str, category: Optional[str] = None) -> str:
        """
        Rewrites low-scoring raw queries into semantically rich retrieval queries.
        Translates raw unified diffs or operator tags into canonical testing concepts.
        """
        reformulated_tokens = []

        # If an operator name or category is passed
        if category:
            clean_cat = category.replace("_", " ").lower()
            reformulated_tokens.append(clean_cat)

        # Match diff syntax against semantic dictionary
        for pattern, replacement in self.DIFF_REFORMULATION_PATTERNS:
            if re.search(pattern, query):
                reformulated_tokens.append(replacement)

        if reformulated_tokens:
            combined = f"{query.strip()} {' '.join(reformulated_tokens)}"
            return combined.strip()

        # Fallback keyword expansion
        return f"{query.strip()} pytest unit testing best practice recipe"

    def grade_chunk_relevance(self, chunk: Dict[str, Any], query: str) -> float:
        """
        Grades a retrieved chunk on a scale of 0.0 to 1.0 based on:
          - Vector store similarity score (50%)
          - Operator/category alignment (30%)
          - Code structure quality (20%)
        """
        base_score = float(chunk.get("score", 0.0))
        meta = chunk.get("metadata", {})
        text = chunk.get("text", "")

        alignment_boost = 0.0
        query_lower = query.lower()

        # Check operator match
        op = str(meta.get("operator_type", "")).lower()
        if op and (op in query_lower or op.replace("_", " ") in query_lower or any(t in query_lower for t in op.split("_") if len(t) > 2)):
            alignment_boost += 0.25

        # Check category match
        cat = str(meta.get("category", "")).lower()
        if cat and (cat in query_lower or cat.replace("_", " ") in query_lower or any(t in query_lower for t in cat.split("_") if len(t) > 2)):
            alignment_boost += 0.15

        # Check executable code block bonus
        code_bonus = 0.1 if ("def test_" in text or "assert " in text) else 0.0

        graded_score = round(min(1.0, (base_score * 0.6) + alignment_boost + code_bonus), 3)
        return graded_score

    def retrieve(
        self,
        query: str,
        collection_name: str = "testing_patterns",
        top_k: int = 3,
        min_score: float = 0.3,
        category: Optional[str] = None,
    ) -> RetrievalResult:
        """
        Executes the full agentic retrieval loop:
          1. Gating check (should_retrieve)
          2. Primary search
          3. Query Reformulation (if initial similarity < 0.4)
          4. Chunk grading and pruning
        """
        # Step 1: Gating
        if not self.should_retrieve(query):
            return RetrievalResult(
                chunks=[],
                query_used=query,
                reformulated=False,
                relevance_score=0.0,
                skipped_trivial=True,
            )

        # Step 2: Primary Search (using a low baseline threshold to gather candidate pool)
        raw_chunks = self.vector_store.search(
            collection_name=collection_name,
            query=query,
            top_k=top_k * 2,  # Oversample for grading
            min_score=min(min_score, 0.05),
        )

        reformulated = False
        effective_query = query

        # Step 3: Query Reformulation if initial results are sparse or low-scoring
        top_initial_score = raw_chunks[0]["score"] if raw_chunks else 0.0
        if top_initial_score < 0.3:
            effective_query = self.reformulate_query(query, category=category)
            reformulated_chunks = self.vector_store.search(
                collection_name=collection_name,
                query=effective_query,
                top_k=top_k * 2,
                min_score=min(min_score, 0.05),
            )
            # Merge and deduplicate
            seen_ids = set()
            combined = []
            for ch in raw_chunks + reformulated_chunks:
                if ch["doc_id"] not in seen_ids:
                    seen_ids.add(ch["doc_id"])
                    combined.append(ch)
            raw_chunks = combined
            reformulated = True

        # Step 4: Chunk Relevance Grading & Pruning
        graded_chunks = []
        for ch in raw_chunks:
            relevance = self.grade_chunk_relevance(ch, effective_query)
            if relevance >= min_score:
                graded_item = dict(ch)
                graded_item["relevance_score"] = relevance
                graded_chunks.append(graded_item)

        graded_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
        final_chunks = graded_chunks[:top_k]

        max_rel = final_chunks[0]["relevance_score"] if final_chunks else 0.0

        return RetrievalResult(
            chunks=final_chunks,
            query_used=effective_query,
            reformulated=reformulated,
            relevance_score=max_rel,
            skipped_trivial=False,
        )
