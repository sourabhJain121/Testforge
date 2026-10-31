from typing import Dict, List, Optional, Union, Tuple, Any, Callable

def transform_records(
    records: List[Dict[str, Union[str, int, float]]],
    predicate: Optional[Callable[[Dict[str, Any]], bool]] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    result = []
    dropped = 0
    for r in records:
        if predicate is None or predicate(r):
            result.append(dict(r))
        else:
            dropped += 1
    return result, dropped
