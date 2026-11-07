from collections import Counter
from typing import List, Tuple

def top_n_frequent_words(words: List[str], n: int = 5) -> List[Tuple[str, int]]:
    normalized = [w.strip().lower() for w in words if w.strip()]
    counts = Counter(normalized)
    return counts.most_common(n)
