"""
testforge/rag/vector_store.py

Local Vector Store and Embedding Retrieval Engine for TestForge (Handout Feature F1).
Provides collection partitioning across testing patterns, repository context,
and historical mutant memory with persistent storage and zero hard external dependencies.
"""

from __future__ import annotations
import os
import re
import math
import json
import time
import uuid
import pathlib
import logging
import collections
from typing import List, Dict, Any, Optional, Set

logger = logging.getLogger("testforge.rag.vector_store")

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
DEFAULT_PERSIST_DIR = BASE_DIR / "qa_artifacts" / "knowledge_base"


def _tokenize_and_vectorize(text: str) -> Dict[str, float]:
    """
    Computes a normalized TF-IDF / bi-gram token frequency vector for text chunks.
    Ensures deterministic, fast cosine similarity calculation without external models.
    """
    clean_text = text.lower()
    tokens = re.findall(r"[a-z0-9_]+", clean_text)
    if not tokens:
        return {}

    counts = collections.Counter(tokens)

    # Add word bi-grams for semantic phrase matching (e.g., "pytest_approx", "boundary_inversion")
    for i in range(len(tokens) - 1):
        bigram = f"{tokens[i]}_{tokens[i+1]}"
        counts[bigram] += 1

    # Length normalization for cosine similarity
    norm = math.sqrt(sum(v * v for v in counts.values()))
    if norm == 0.0:
        return {}
    return {k: v / norm for k, v in counts.items()}


def _cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """Calculates dot product between two normalized sparse vectors."""
    if not vec1 or not vec2:
        return 0.0
    common_keys = set(vec1.keys()) & set(vec2.keys())
    return sum(vec1[k] * vec2[k] for k in common_keys)


class TestForgeVectorStore:
    """
    Local partitioned vector store managing document chunks across:
      - 'testing_patterns': Standard testing recipes and assertions
      - 'repo_context': Target signatures, call graphs, docstrings
      - 'mutant_memory': Historical pairs of mutant diffs and winning test patches
    """
    __test__ = False

    SUPPORTED_COLLECTIONS: Set[str] = {"testing_patterns", "repo_context", "mutant_memory"}

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        use_chroma: bool = False,
    ):
        self.persist_dir = pathlib.Path(persist_dir) if persist_dir else DEFAULT_PERSIST_DIR
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.use_chroma = use_chroma
        self.chroma_client = None

        # In-memory document storage: {collection_name: {doc_id: doc_dict}}
        self._collections: Dict[str, Dict[str, Dict[str, Any]]] = {
            col: {} for col in self.SUPPORTED_COLLECTIONS
        }

        # Attempt ChromaDB initialization if requested
        if self.use_chroma:
            try:
                import chromadb
                self.chroma_client = chromadb.PersistentClient(path=str(self.persist_dir / "chroma"))
                logger.info("TestForgeVectorStore: Initialized ChromaDB persistent client.")
            except Exception as exc:
                logger.warning(f"ChromaDB initialization failed: {exc}. Using deterministic local store fallback.")
                self.chroma_client = None

        # Load persisted local data from disk
        self._load_from_disk()

        # Pre-seed default testing recipes if testing_patterns is empty
        if not self._collections["testing_patterns"]:
            self._seed_default_testing_patterns()

    def _get_collection_file(self, collection_name: str) -> pathlib.Path:
        return self.persist_dir / f"{collection_name}.json"

    def _load_from_disk(self) -> None:
        """Loads serialized collections from local disk JSON files."""
        for col in self.SUPPORTED_COLLECTIONS:
            fp = self._get_collection_file(col)
            if fp.exists():
                try:
                    data = json.loads(fp.read_text(encoding="utf-8"))
                    for doc in data:
                        doc_id = doc["doc_id"]
                        text = doc["text"]
                        metadata = doc.get("metadata", {})
                        vector = _tokenize_and_vectorize(text)
                        self._collections[col][doc_id] = {
                            "doc_id": doc_id,
                            "text": text,
                            "metadata": metadata,
                            "vector": vector,
                            "created_at": doc.get("created_at", time.time()),
                        }
                    logger.debug(f"Loaded {len(data)} documents into collection '{col}'.")
                except Exception as exc:
                    logger.warning(f"Failed to read vector collection {col}: {exc}")

    def _save_collection_to_disk(self, collection_name: str) -> None:
        """Persists collection items to JSON on disk."""
        fp = self._get_collection_file(collection_name)
        try:
            records = [
                {
                    "doc_id": d["doc_id"],
                    "text": d["text"],
                    "metadata": d["metadata"],
                    "created_at": d.get("created_at", time.time()),
                }
                for d in self._collections[collection_name].values()
            ]
            fp.write_text(json.dumps(records, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.warning(f"Failed to write vector collection {collection_name} to disk: {exc}")

    def add_document(
        self,
        collection_name: str,
        text: str,
        doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Adds a document chunk with metadata to the specified collection."""
        if collection_name not in self.SUPPORTED_COLLECTIONS:
            self._collections[collection_name] = {}

        eff_id = doc_id or f"doc_{uuid.uuid4().hex[:8]}"
        meta = metadata or {}
        meta.setdefault("created_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

        vector = _tokenize_and_vectorize(text)
        self._collections[collection_name][eff_id] = {
            "doc_id": eff_id,
            "text": text,
            "metadata": meta,
            "vector": vector,
            "created_at": time.time(),
        }

        # Chroma sync if enabled
        if self.chroma_client:
            try:
                col = self.chroma_client.get_or_create_collection(name=collection_name)
                col.add(
                    documents=[text],
                    metadatas=[{k: str(v) for k, v in meta.items()}],
                    ids=[eff_id],
                )
            except Exception as exc:
                logger.debug(f"Chroma add error: {exc}")

        self._save_collection_to_disk(collection_name)
        return eff_id

    def add_documents(
        self,
        collection_name: str,
        docs: List[Dict[str, Any]],
    ) -> List[str]:
        """Batch ingestion of document chunks into collection."""
        added_ids = []
        for d in docs:
            doc_id = d.get("doc_id")
            text = d.get("text", "")
            meta = d.get("metadata", {})
            added_ids.append(self.add_document(collection_name, text=text, doc_id=doc_id, metadata=meta))
        return added_ids

    def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 3,
        min_score: float = 0.05,
    ) -> List[Dict[str, Any]]:
        """
        Executes semantic cosine similarity search against the designated collection partition.
        Returns top_k matches exceeding min_score.
        """
        if collection_name not in self._collections:
            return []

        col_docs = self._collections[collection_name]
        if not col_docs or not query.strip():
            return []

        query_vec = _tokenize_and_vectorize(query)
        if not query_vec:
            return []

        scored_results: List[Dict[str, Any]] = []
        for doc in col_docs.values():
            sim = _cosine_similarity(query_vec, doc["vector"])
            if sim >= min_score:
                scored_results.append({
                    "doc_id": doc["doc_id"],
                    "text": doc["text"],
                    "metadata": doc["metadata"],
                    "score": round(sim, 4),
                })

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]

    def count(self, collection_name: str) -> int:
        """Returns the number of documents in the collection."""
        return len(self._collections.get(collection_name, {}))

    def get_collection(self, collection_name: str) -> List[Dict[str, Any]]:
        """Retrieves all documents stored in the given collection."""
        return list(self._collections.get(collection_name, {}).values())

    def clear(self, collection_name: Optional[str] = None) -> None:
        """Clears specified collection or all collections."""
        cols = [collection_name] if collection_name else list(self.SUPPORTED_COLLECTIONS)
        for col in cols:
            if col in self._collections:
                self._collections[col].clear()
                self._save_collection_to_disk(col)

    def _seed_default_testing_patterns(self) -> None:
        """Seeds the testing_patterns collection with essential testing recipes."""
        recipes = [
            {
                "doc_id": "pattern_approx_floats",
                "text": (
                    "# Floating Point Approximate Comparison Recipe\n"
                    "import pytest\n"
                    "def test_floating_point_precision():\n"
                    "    # Uses pytest.approx to handle IEEE 754 precision inaccuracies\n"
                    "    result = calculate_discount(100.0)\n"
                    "    assert result == pytest.approx(90.0, rel=1e-3, abs=1e-4)\n"
                ),
                "metadata": {
                    "category": "floating_point",
                    "pattern_name": "pytest.approx",
                    "operator_type": "MATH_FUNC",
                    "source": "pytest_docs",
                },
            },
            {
                "doc_id": "pattern_exception_guards",
                "text": (
                    "# Negative Test Exception Guard Recipe\n"
                    "import pytest\n"
                    "def test_negative_input_exception():\n"
                    "    # Asserts that invalid domain arguments raise expected ValueError or TypeError\n"
                    "    with pytest.raises((ValueError, TypeError), match='.*invalid.*'):\n"
                    "        process_transaction(-1)\n"
                ),
                "metadata": {
                    "category": "exception_guard",
                    "pattern_name": "pytest.raises",
                    "operator_type": "NEGATIVE_INPUT",
                    "source": "pytest_docs",
                },
            },
            {
                "doc_id": "pattern_boundary_off_by_one",
                "text": (
                    "# Boundary Testing for Relational Threshold Off-By-One Inversions\n"
                    "import pytest\n"
                    "def test_boundary_threshold_triplet():\n"
                    "    # Evaluates exact threshold boundary T and adjacent neighbors T-1, T, T+1\n"
                    "    # Prevents '<' vs '<=' and '>' vs '>=' boundary escapes\n"
                    "    assert check_threshold(99) is False\n"
                    "    assert check_threshold(100) is True\n"
                    "    assert check_threshold(101) is True\n"
                ),
                "metadata": {
                    "category": "boundary_testing",
                    "pattern_name": "boundary_triplet",
                    "operator_type": "BOUNDARY_SWAP",
                    "source": "qa_best_practices",
                },
            },
            {
                "doc_id": "pattern_parameterized_matrix",
                "text": (
                    "# Parameterized Test Matrix Recipe for Domain Permutations\n"
                    "import pytest\n"
                    "@pytest.mark.parametrize('input_val, expected', [\n"
                    "    (0, 0),\n"
                    "    (50, 50),\n"
                    "    (100, 95.0),\n"
                    "    (200, 180.0),\n"
                    "])\n"
                    "def test_discount_matrix(input_val, expected):\n"
                    "    assert calculate_discount(input_val) == pytest.approx(expected, rel=1e-3)\n"
                ),
                "metadata": {
                    "category": "parameterized",
                    "pattern_name": "pytest.mark.parametrize",
                    "operator_type": "COMP_OP",
                    "source": "pytest_docs",
                },
            },
        ]
        self.add_documents("testing_patterns", recipes)
        logger.info(f"TestForgeVectorStore: Pre-seeded {len(recipes)} testing pattern recipes.")
