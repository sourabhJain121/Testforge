import weakref
from typing import Any, List

class EventDispatcher:
    def __init__(self):
        self._listeners: List[weakref.ref] = []

    def register_listener(self, obj: Any) -> None:
        self._listeners.append(weakref.ref(obj))

    def get_active_count(self) -> int:
        return sum(1 for ref in self._listeners if ref() is not None)
