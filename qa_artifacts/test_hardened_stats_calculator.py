import pytest
from target import calculate_mean, calculate_variance, calculate_stddev, calculate_median, calculate_z_scores, calculate_summary_stats

def test_calculate_mean_nominal():
    result = calculate_mean([10.0, 20.0, 30.0, 40.0, 50.0])
    assert result == pytest.approx(30.0, rel=1e-3)
def test_calculate_mean_extreme_values_empty_list_raises_ValueError():
    with pytest.raises(ValueError):
        calculate_mean([])
def test_calculate_mean_extreme_values_single_element_list():
    result = calculate_mean([10.0])
    assert result == pytest.approx(10.0, rel=1e-3)
def test_calculate_variance_nominal():
    result = calculate_variance([10.0, 20.0, 30.0, 40.0, 50.0], 2)
    assert result == pytest.approx(333.3333, rel=1e-3)
def test_calculate_variance_extreme_values_empty_list_raises_ValueError():
    with pytest.raises(ValueError):
        calculate_variance([], 2)
def test_calculate_variance_extreme_values_single_element_list_raises_ValueError():
    with pytest.raises(ValueError):
        calculate_variance([10.0], 2)
def test_calculate_variance_extreme_ddof_zero():
    result = calculate_variance([10.0, 20.0, 30.0, 40.0, 50.0], 0)
    assert result == pytest.approx(200.0, rel=1e-3)
def test_calculate_variance_extreme_ddof_negative_one():
    result = calculate_variance([10.0, 20.0, 30.0, 40.0, 50.0], -1)
    assert result == pytest.approx(166.6667, rel=1e-3)
def test_calculate_variance_extreme_ddof_negative_large():
    result = calculate_variance([10.0, 20.0, 30.0, 40.0, 50.0], -100)
    assert result == pytest.approx(9.5238, rel=1e-3)
def test_calculate_variance_extreme_ddof_large_positive_raises_ValueError():
    with pytest.raises(ValueError):
        calculate_variance([10.0, 20.0, 30.0, 40.0, 50.0], 10000)
def test_calculate_stddev_nominal():
    result = calculate_stddev([10.0, 20.0, 30.0, 40.0, 50.0], 2)
    assert result == pytest.approx(18.2574, rel=1e-3)
def test_calculate_stddev_extreme_values_empty_list_raises_ValueError():
    with pytest.raises(ValueError):
        calculate_stddev([], 2)
def test_calculate_stddev_extreme_values_single_element_list_raises_ValueError():
    with pytest.raises(ValueError):
        calculate_stddev([10.0], 2)
def test_calculate_stddev_extreme_ddof_zero():
    result = calculate_stddev([10.0, 20.0, 30.0, 40.0, 50.0], 0)
    assert result == pytest.approx(14.1421, rel=1e-3)
def test_calculate_stddev_extreme_ddof_negative_one():
    result = calculate_stddev([10.0, 20.0, 30.0, 40.0, 50.0], -1)
    assert result == pytest.approx(12.9099, rel=1e-3)
def test_calculate_stddev_extreme_ddof_negative_large():
    result = calculate_stddev([10.0, 20.0, 30.0, 40.0, 50.0], -100)
    assert result == pytest.approx(3.0861, rel=1e-3)
def test_calculate_stddev_extreme_ddof_large_positive_raises_ValueError():
    with pytest.raises(ValueError):
        calculate_stddev([10.0, 20.0, 30.0, 40.0, 50.0], 10000)
def test_calculate_median_nominal():
    result = calculate_median([10.0, 20.0, 30.0, 40.0, 50.0])
    assert result == pytest.approx(30.0, rel=1e-3)
def test_calculate_median_extreme_values_empty_list_raises_ValueError():
    with pytest.raises(ValueError):
        calculate_median([])
def test_calculate_median_extreme_values_single_element_list():
    result = calculate_median([10.0])
    assert result == pytest.approx(10.0, rel=1e-3)
def test_calculate_z_scores_nominal():
    result = calculate_z_scores([10.0, 20.0, 30.0, 40.0, 50.0])
    assert result == [-1.2649, -0.6325, 0.0, 0.6325, 1.2649]
def test_calculate_z_scores_extreme_values_empty_list_raises_ValueError():
    with pytest.raises(ValueError):
        calculate_z_scores([])
def test_calculate_z_scores_extreme_values_single_element_list_raises_ValueError():
    with pytest.raises(ValueError):
        calculate_z_scores([10.0])
def test_calculate_z_scores_property_idempotent():
    """[Property Invariant] Idempotence invariant: fn(fn(x)) == fn(x). property_confidence="HIGH"."""
    first = calculate_z_scores([10.0, 20.0, 30.0, 40.0, 50.0])
    second = calculate_z_scores(first)
    assert second == first
def test_calculate_summary_stats_nominal():
    result = calculate_summary_stats([10.0, 20.0, 30.0, 40.0, 50.0])
    assert isinstance(result, dict)
def test_calculate_summary_stats_extreme_values_empty_list_raises_ValueError():
    with pytest.raises(ValueError):
        calculate_summary_stats([])
def test_calculate_summary_stats_extreme_values_single_element_list():
    result = calculate_summary_stats([10.0])
    assert isinstance(result, dict)