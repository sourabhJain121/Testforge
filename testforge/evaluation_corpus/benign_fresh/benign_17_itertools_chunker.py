from itertools import islice
from typing import Iterator, Iterable, List, Any

def batch_iterable(iterable: Iterable[Any], batch_size: int) -> Iterator[List[Any]]:
    it = iter(iterable)
    while batch := list(islice(it, batch_size)):
        yield batch
