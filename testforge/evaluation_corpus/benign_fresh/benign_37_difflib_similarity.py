import difflib

def compute_text_similarity(a: str, b: str) -> float:
    matcher = difflib.SequenceMatcher(None, a, b)
    return round(matcher.ratio(), 4)
