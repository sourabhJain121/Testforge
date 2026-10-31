import pytest
from target import calculate_item_discount, estimate_freight_cost, calculate_customs_duty, validate_tracking_number, compute_sla_deadline_hours, process_bulk_order, ShippingTier, WarehouseInventory

def test_calculate_item_discount_nominal():
    result = calculate_item_discount(100.0, 2, 'REGULAR')
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_item_discount_invalid_unit_price_raises_ValueError():
    with pytest.raises(ValueError):
        calculate_item_discount(0.0, 2, 'REGULAR')
def test_calculate_item_discount_invalid_quantity_raises_ValueError():
    with pytest.raises(ValueError):
        calculate_item_discount(100.0, 0, 'REGULAR')
def test_calculate_item_discount_threshold_unit_price_0_1():
    result = calculate_item_discount(0.1, 2, 'REGULAR')
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_item_discount_threshold_quantity_1():
    result = calculate_item_discount(100.0, 1, 'REGULAR')
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_item_discount_threshold_quantity_2():
    result = calculate_item_discount(100.0, 2, 'REGULAR')
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_item_discount_threshold_quantity_50():
    result = calculate_item_discount(100.0, 50, 'REGULAR')
    assert result == pytest.approx(0.2, rel=1e-3)
def test_calculate_item_discount_threshold_quantity_49():
    result = calculate_item_discount(100.0, 49, 'REGULAR')
    assert result == pytest.approx(0.12, rel=1e-3)
def test_calculate_item_discount_threshold_quantity_51():
    result = calculate_item_discount(100.0, 51, 'REGULAR')
    assert result == pytest.approx(0.2, rel=1e-3)
def test_calculate_item_discount_threshold_quantity_20():
    result = calculate_item_discount(100.0, 20, 'REGULAR')
    assert result == pytest.approx(0.12, rel=1e-3)
def test_calculate_item_discount_threshold_quantity_19():
    result = calculate_item_discount(100.0, 19, 'REGULAR')
    assert result == pytest.approx(0.05, rel=1e-3)
def test_calculate_item_discount_threshold_quantity_21():
    result = calculate_item_discount(100.0, 21, 'REGULAR')
    assert result == pytest.approx(0.12, rel=1e-3)
def test_calculate_item_discount_threshold_quantity_5():
    result = calculate_item_discount(100.0, 5, 'REGULAR')
    assert result == pytest.approx(0.05, rel=1e-3)
def test_calculate_item_discount_threshold_quantity_4():
    result = calculate_item_discount(100.0, 4, 'REGULAR')
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_item_discount_threshold_quantity_6():
    result = calculate_item_discount(100.0, 6, 'REGULAR')
    assert result == pytest.approx(0.05, rel=1e-3)
def test_estimate_freight_cost_nominal():
    result = estimate_freight_cost(10.0, 10.0, False)
    assert result == pytest.approx(21.3, rel=1e-3)
def test_estimate_freight_cost_invalid_weight_kg_raises_ValueError():
    with pytest.raises(ValueError):
        estimate_freight_cost(0.0, 10.0, False)
def test_estimate_freight_cost_invalid_distance_km_raises_ValueError():
    with pytest.raises(ValueError):
        estimate_freight_cost(10.0, 0.0, False)
def test_estimate_freight_cost_threshold_weight_kg_0_1():
    result = estimate_freight_cost(0.1, 10.0, False)
    assert result == pytest.approx(12.89, rel=1e-3)
def test_estimate_freight_cost_threshold_weight_kg_5000_0():
    result = estimate_freight_cost(5000.0, 10.0, False)
    assert result == pytest.approx(4262.8, rel=1e-3)
def test_estimate_freight_cost_threshold_weight_kg_4999_0():
    result = estimate_freight_cost(4999.0, 10.0, False)
    assert result == pytest.approx(4261.95, rel=1e-3)
def test_estimate_freight_cost_threshold_distance_km_0_1():
    result = estimate_freight_cost(10.0, 0.1, False)
    assert result == pytest.approx(20.51, rel=1e-3)
def test_estimate_freight_cost_threshold_distance_km_25000_0():
    result = estimate_freight_cost(10.0, 25000.0, False)
    assert result == pytest.approx(2020.5, rel=1e-3)
def test_estimate_freight_cost_threshold_distance_km_24999_0():
    result = estimate_freight_cost(10.0, 24999.0, False)
    assert result == pytest.approx(2020.42, rel=1e-3)
def test_estimate_freight_cost_branch_is_hazardous_True():
    result = estimate_freight_cost(10.0, 10.0, True)
    assert result == pytest.approx(71.3, rel=1e-3)
def test_estimate_freight_cost_branch_is_hazardous_False():
    result = estimate_freight_cost(10.0, 10.0, False)
    assert result == pytest.approx(21.3, rel=1e-3)
def test_calculate_customs_duty_nominal():
    result = calculate_customs_duty(10.0, 'US', 'test')
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_customs_duty_invalid_country_code_raises_ValueError():
    with pytest.raises(ValueError):
        calculate_customs_duty(10.0, 'INVALID_PARAM_INPUT', 'test')
def test_calculate_customs_duty_threshold_declared_value_0_0():
    result = calculate_customs_duty(0.0, 'US', 'test')
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_customs_duty_threshold_declared_value_0_1():
    result = calculate_customs_duty(0.1, 'US', 'test')
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_customs_duty_threshold_declared_value_800_0():
    result = calculate_customs_duty(800.0, 'US', 'test')
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_customs_duty_threshold_declared_value_799_0():
    result = calculate_customs_duty(799.0, 'US', 'test')
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_customs_duty_threshold_declared_value_801_0():
    result = calculate_customs_duty(801.0, 'US', 'test')
    assert result == pytest.approx(20.03, rel=1e-3)
def test_validate_tracking_number_nominal():
    result = validate_tracking_number('TRK-EXP-123456-4')
    assert result is True
def test_validate_tracking_number_guard_tracking_code_returns_constant():
    result = validate_tracking_number('INVALID-TRACK-CODE')
    assert result is False
def test_compute_sla_deadline_hours_nominal():
    result = compute_sla_deadline_hours(2, 2)
    assert result == 36
def test_compute_sla_deadline_hours_invalid_priority_raises_ValueError():
    with pytest.raises(ValueError):
        compute_sla_deadline_hours(0, 2)
def test_compute_sla_deadline_hours_invalid_transit_days_raises_ValueError():
    with pytest.raises(ValueError):
        compute_sla_deadline_hours(2, 0)
def test_compute_sla_deadline_hours_threshold_priority_1():
    result = compute_sla_deadline_hours(1, 2)
    assert result == 24
def test_compute_sla_deadline_hours_threshold_priority_2():
    result = compute_sla_deadline_hours(2, 2)
    assert result == 36
def test_compute_sla_deadline_hours_threshold_priority_5():
    result = compute_sla_deadline_hours(5, 2)
    assert result == 72
def test_compute_sla_deadline_hours_threshold_priority_4():
    result = compute_sla_deadline_hours(4, 2)
    assert result == 60
def test_compute_sla_deadline_hours_threshold_transit_days_1():
    result = compute_sla_deadline_hours(2, 1)
    assert result == 18
def test_compute_sla_deadline_hours_threshold_transit_days_2():
    result = compute_sla_deadline_hours(2, 2)
    assert result == 36
def test_compute_sla_deadline_hours_threshold_transit_days_30():
    result = compute_sla_deadline_hours(2, 30)
    assert result == 540
def test_compute_sla_deadline_hours_threshold_transit_days_29():
    result = compute_sla_deadline_hours(2, 29)
    assert result == 522
def test_compute_sla_deadline_hours_lookup_priority_1():
    result = compute_sla_deadline_hours(1, 2)
    assert result == 24
def test_compute_sla_deadline_hours_lookup_priority_2():
    result = compute_sla_deadline_hours(2, 2)
    assert result == 36
def test_compute_sla_deadline_hours_lookup_priority_3():
    result = compute_sla_deadline_hours(3, 2)
    assert result == 48
def test_compute_sla_deadline_hours_lookup_priority_4():
    result = compute_sla_deadline_hours(4, 2)
    assert result == 60
def test_compute_sla_deadline_hours_lookup_priority_5():
    result = compute_sla_deadline_hours(5, 2)
    assert result == 72
def test_process_bulk_order_nominal():
    result = process_bulk_order([{'unit_price': 50.0, 'quantity': 2, 'weight_kg': 1.0}], 'REGULAR', False)
    assert isinstance(result, dict)
    assert result['status'] == 'PROCESSED'
    assert result['item_count'] == 2
    assert result['final_total'] == pytest.approx(133.7, rel=1e-3)
def test_process_bulk_order_invalid_order_items_raises_TypeError():
    with pytest.raises(TypeError):
        process_bulk_order('not_a_list_error', 'REGULAR', False)
def test_process_bulk_order_branch_express_shipping_True():
    result = process_bulk_order([{'unit_price': 50.0, 'quantity': 2, 'weight_kg': 1.0}], 'REGULAR', True)
    assert isinstance(result, dict)
    assert result['status'] == 'PROCESSED'
    assert result['item_count'] == 2
    assert result['final_total'] == pytest.approx(153.7, rel=1e-3)
def test_process_bulk_order_branch_express_shipping_False():
    result = process_bulk_order([{'unit_price': 50.0, 'quantity': 2, 'weight_kg': 1.0}], 'REGULAR', False)
    assert isinstance(result, dict)
    assert result['status'] == 'PROCESSED'
    assert result['item_count'] == 2
    assert result['final_total'] == pytest.approx(133.7, rel=1e-3)
def test_WarehouseInventory_get_available_stock_nominal():
    obj = WarehouseInventory({'SKU-001': 20})
    result = obj.get_available_stock('SKU-001')
    assert result == 20
def test_WarehouseInventory_reserve_stock_nominal():
    obj = WarehouseInventory({'SKU-001': 20})
    result = obj.reserve_stock('SKU-001', 2)
    assert result is True
def test_WarehouseInventory_release_stock_nominal():
    obj = WarehouseInventory({'SKU-001': 20})
    result = obj.release_stock('SKU-001', 2)
    assert result is False
def test_WarehouseInventory_restock_needed_nominal():
    obj = WarehouseInventory({'SKU-001': 20})
    result = obj.restock_needed('SKU-001', 2)
    assert result is False
def test_WarehouseInventory_state_and_methods():
    obj = WarehouseInventory({'SKU-001': 20})
    res_get_available_stock = obj.get_available_stock('SKU-001')
    assert res_get_available_stock == 20
    res_reserve_stock = obj.reserve_stock('SKU-001', 2)
    assert res_reserve_stock is True
    res_release_stock = obj.release_stock('SKU-001', 2)
    assert res_release_stock is True
    res_restock_needed = obj.restock_needed('SKU-001', 2)
    assert res_restock_needed is False
def test_WarehouseInventory_reserve_stock_invalid_quantity_raises_ValueError():
    obj = WarehouseInventory({'SKU-001': 20})
    with pytest.raises(ValueError):
        obj.reserve_stock('SKU-001', 0)
def test_WarehouseInventory_reserve_stock_threshold_quantity_1():
    obj = WarehouseInventory({'SKU-001': 20})
    result = obj.reserve_stock('SKU-001', 1)
    assert result is True
def test_WarehouseInventory_release_stock_invalid_quantity_raises_ValueError():
    obj = WarehouseInventory({'SKU-001': 20})
    with pytest.raises(ValueError):
        obj.release_stock('SKU-001', 0)
def test_WarehouseInventory_release_stock_threshold_quantity_1():
    obj = WarehouseInventory({'SKU-001': 20})
    result = obj.release_stock('SKU-001', 1)
    assert result is False