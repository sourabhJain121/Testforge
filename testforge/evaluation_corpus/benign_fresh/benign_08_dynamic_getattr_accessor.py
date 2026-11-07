from typing import Any, Optional

def safe_get_property(instance: Any, prop_name: str, fallback: Optional[Any] = None) -> Any:
    if hasattr(instance, prop_name):
        return getattr(instance, prop_name)
    return fallback
