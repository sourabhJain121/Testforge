"""
samples/sealed_eval/markdown_parser.py

Domain: Text Processing & Parsing
Lightweight tokenizer and AST extractor for Markdown content.
"""

import re
from typing import List, Dict, Any, Optional


def parse_headers(text: str) -> List[Dict[str, Any]]:
    """Extracts markdown headers (# H1, ## H2, etc.) with level and text."""
    if not text:
        return []

    headers = []
    lines = text.splitlines()
    for line_idx, line in enumerate(lines, 1):
        match = re.match(r"^(#{1,6})\s+(.*)$", line.strip())
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            headers.append({
                "level": level,
                "title": title,
                "line": line_idx
            })
    return headers


def parse_links(text: str) -> List[Dict[str, str]]:
    """Extracts standard inline markdown links: [anchor text](https://url)."""
    if not text:
        return []

    pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    matches = re.findall(pattern, text)
    links = []
    for anchor, target in matches:
        clean_anchor = anchor.strip()
        clean_target = target.strip()
        if clean_anchor and clean_target:
            links.append({
                "text": clean_anchor,
                "url": clean_target
            })
    return links


def count_words_and_blocks(text: str) -> Dict[str, int]:
    """Calculates word count, paragraph count, and code block counts."""
    if not text or not text.strip():
        return {"words": 0, "paragraphs": 0, "code_blocks": 0}

    code_blocks = len(re.findall(r"```[\s\S]*?```", text))
    clean_text = re.sub(r"```[\s\S]*?```", " ", text)

    paragraphs = [p.strip() for p in clean_text.split("\n\n") if p.strip()]
    words = re.findall(r"\b\w+\b", clean_text)

    return {
        "words": len(words),
        "paragraphs": len(paragraphs),
        "code_blocks": code_blocks
    }


def extract_checklist_items(text: str) -> Dict[str, List[str]]:
    """Extracts GitHub-flavored markdown task lists (- [ ] pending, - [x] done)."""
    if not text:
        return {"completed": [], "pending": []}

    completed: List[str] = []
    pending: List[str] = []

    for line in text.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("- [x]") or trimmed.startswith("- [X]"):
            item = trimmed[5:].strip()
            if item:
                completed.append(item)
        elif trimmed.startswith("- [ ]"):
            item = trimmed[5:].strip()
            if item:
                pending.append(item)

    return {"completed": completed, "pending": pending}
