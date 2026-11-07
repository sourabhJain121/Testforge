import time
from functools import wraps
from typing import Callable, Any

def retry_on_exception(retries: int = 3, delay_sec: float = 0.5):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_err = None
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as err:
                    last_err = err
                    time.sleep(delay_sec)
            raise last_err
        return wrapper
    return decorator
