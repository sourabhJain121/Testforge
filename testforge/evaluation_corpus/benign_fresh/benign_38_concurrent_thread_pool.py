from concurrent.futures import ThreadPoolExecutor
from typing import List, Callable, Any

def parallel_map_worker(items: List[Any], transform: Callable[[Any], Any]) -> List[Any]:
    with ThreadPoolExecutor(max_workers=4) as executor:
        return list(executor.map(transform, items))
