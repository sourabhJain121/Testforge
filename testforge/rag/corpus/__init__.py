"""
testforge/rag/corpus/__init__.py

Standard Heuristic Knowledge Corpus for TestForge Agentic RAG.
Contains categorized edge-case testing rules for Python AST patterns.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, List

CORPUS_DIR = pathlib.Path(__file__).resolve().parent


def load_all_corpus_documents() -> List[Dict[str, Any]]:
    """Loads all categorized heuristic testing rule documents from the corpus directory."""
    docs: List[Dict[str, Any]] = []
    for fp in sorted(CORPUS_DIR.glob("*.json")):
        try:
            items = json.loads(fp.read_text(encoding="utf-8"))
            if isinstance(items, list):
                docs.extend(items)
        except Exception:
            pass
    return docs

