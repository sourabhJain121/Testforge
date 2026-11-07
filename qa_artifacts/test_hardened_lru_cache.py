import pytest
from target import Node, LRUCache

def test_LRUCache_get_nominal():
    obj = LRUCache(2)
    result = obj.get('key_1')
    assert result is None
def test_LRUCache_put_nominal():
    obj = LRUCache(2)
    result = obj.put('key_1', 1)
    assert result is None
def test_LRUCache_size_nominal():
    obj = LRUCache(2)
    result = obj.size()
    assert result == 0
def test_LRUCache_clear_nominal():
    obj = LRUCache(2)
    result = obj.clear()
    assert result is None
def test_LRUCache_get_hit_ratio_nominal():
    obj = LRUCache(2)
    result = obj.get_hit_ratio()
    assert result == pytest.approx(0.0, rel=1e-3)