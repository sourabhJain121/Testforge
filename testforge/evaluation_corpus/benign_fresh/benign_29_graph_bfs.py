from collections import deque
from typing import Dict, List, Set, Optional

def shortest_path_bfs(graph: Dict[str, List[str]], start: str, goal: str) -> Optional[List[str]]:
    queue = deque([[start]])
    visited: Set[str] = {start}
    while queue:
        path = queue.popleft()
        node = path[-1]
        if node == goal:
            return path
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])
    return None
