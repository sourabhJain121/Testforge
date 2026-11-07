import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from samples.order_fsm import validate_transition, transition_order_state, OrderFSM

def test_validate_transition_nominal():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', 100.0)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_validate_transition_multi_arg_scenario():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', 100.0)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_validate_transition_threshold_amount_5000_0():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', 5000.0)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_validate_transition_threshold_amount_4999_0():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', 4999.0)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_validate_transition_threshold_amount_5001_0():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', 5001.0)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_validate_transition_enum_user_role_admin():
    result = validate_transition('CREATED', 'CREATED', 'ADMIN', 100.0)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_validate_transition_enum_user_role_support():
    result = validate_transition('CREATED', 'CREATED', 'SUPPORT', 100.0)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_validate_transition_extreme_current_state_empty_string():
    result = validate_transition('', 'CREATED', 'CUSTOMER', 100.0)
    assert result == (False, "Unknown source state ''")
def test_validate_transition_extreme_current_state_single_char():
    result = validate_transition('a', 'CREATED', 'CUSTOMER', 100.0)
    assert result == (False, "Unknown source state 'a'")
def test_validate_transition_extreme_current_state_whitespace_string():
    result = validate_transition('   ', 'CREATED', 'CUSTOMER', 100.0)
    assert result == (False, "Unknown source state '   '")
def test_validate_transition_extreme_next_state_empty_string():
    result = validate_transition('CREATED', '', 'CUSTOMER', 100.0)
    assert result == (False, "Unknown target state ''")
def test_validate_transition_extreme_next_state_single_char():
    result = validate_transition('CREATED', 'a', 'CUSTOMER', 100.0)
    assert result == (False, "Unknown target state 'a'")
def test_validate_transition_extreme_next_state_whitespace_string():
    result = validate_transition('CREATED', '   ', 'CUSTOMER', 100.0)
    assert result == (False, "Unknown target state '   '")
def test_validate_transition_extreme_user_role_empty_string():
    result = validate_transition('CREATED', 'CREATED', '', 100.0)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_validate_transition_extreme_user_role_single_char():
    result = validate_transition('CREATED', 'CREATED', 'a', 100.0)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_validate_transition_extreme_user_role_whitespace_string():
    result = validate_transition('CREATED', 'CREATED', '   ', 100.0)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_validate_transition_extreme_amount_zero():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', 0)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_validate_transition_extreme_amount_negative_one():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', -1)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_validate_transition_extreme_amount_negative_large():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', -100)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_validate_transition_extreme_amount_large_positive():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', 10000)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_validate_transition_extreme_amount_decimal_precision_10_55():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', 10.55)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_validate_transition_extreme_amount_decimal_precision_0_05():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', 0.05)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_transition_order_state_nominal():
    result = transition_order_state('CREATED', 'CREATED', 'CUSTOMER', 100.0)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_transition_order_state_multi_arg_scenario():
    result = transition_order_state('CREATED', 'CREATED', 'CUSTOMER', 100.0)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_transition_order_state_extreme_current_state_empty_string():
    result = transition_order_state('', 'CREATED', 'CUSTOMER', 100.0)
    assert result == (False, "Unknown source state ''")
def test_transition_order_state_extreme_current_state_single_char():
    result = transition_order_state('a', 'CREATED', 'CUSTOMER', 100.0)
    assert result == (False, "Unknown source state 'a'")
def test_transition_order_state_extreme_current_state_whitespace_string():
    result = transition_order_state('   ', 'CREATED', 'CUSTOMER', 100.0)
    assert result == (False, "Unknown source state '   '")
def test_transition_order_state_extreme_next_state_empty_string():
    result = transition_order_state('CREATED', '', 'CUSTOMER', 100.0)
    assert result == (False, "Unknown target state ''")
def test_transition_order_state_extreme_next_state_single_char():
    result = transition_order_state('CREATED', 'a', 'CUSTOMER', 100.0)
    assert result == (False, "Unknown target state 'a'")
def test_transition_order_state_extreme_next_state_whitespace_string():
    result = transition_order_state('CREATED', '   ', 'CUSTOMER', 100.0)
    assert result == (False, "Unknown target state '   '")
def test_transition_order_state_extreme_user_role_empty_string():
    result = transition_order_state('CREATED', 'CREATED', '', 100.0)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_transition_order_state_extreme_user_role_single_char():
    result = transition_order_state('CREATED', 'CREATED', 'a', 100.0)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_transition_order_state_extreme_user_role_whitespace_string():
    result = transition_order_state('CREATED', 'CREATED', '   ', 100.0)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_transition_order_state_extreme_amount_zero():
    result = transition_order_state('CREATED', 'CREATED', 'CUSTOMER', 0)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_transition_order_state_extreme_amount_negative_one():
    result = transition_order_state('CREATED', 'CREATED', 'CUSTOMER', -1)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_transition_order_state_extreme_amount_negative_large():
    result = transition_order_state('CREATED', 'CREATED', 'CUSTOMER', -100)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_transition_order_state_extreme_amount_large_positive():
    result = transition_order_state('CREATED', 'CREATED', 'CUSTOMER', 10000)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_transition_order_state_extreme_amount_decimal_precision_10_55():
    result = transition_order_state('CREATED', 'CREATED', 'CUSTOMER', 10.55)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_transition_order_state_extreme_amount_decimal_precision_0_05():
    result = transition_order_state('CREATED', 'CREATED', 'CUSTOMER', 0.05)
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_OrderFSM_can_transition_nominal():
    obj = OrderFSM('ORD-001', 100.0, 'CREATED')
    result = obj.can_transition('CREATED', 'CUSTOMER')
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_OrderFSM_transition_nominal():
    obj = OrderFSM('ORD-001', 100.0, 'CREATED')
    result = obj.transition('CREATED', 'CUSTOMER')
    assert result == (False, "Illegal transition from 'CREATED' to 'CREATED'")
def test_OrderFSM_is_terminal_nominal():
    obj = OrderFSM('ORD-001', 100.0, 'CREATED')
    result = obj.is_terminal()
    assert result is False
def test_OrderFSM_get_audit_trail_nominal():
    obj = OrderFSM('ORD-001', 100.0, 'CREATED')
    result = obj.get_audit_trail()
    assert result == ['INITIAL->CREATED by SYSTEM']
def test_OrderFSM_state_and_methods():
    obj = OrderFSM('ORD-001', 100.0, 'CREATED')
    res_can_transition = obj.can_transition('CREATED', 'CUSTOMER')
    assert res_can_transition == (False, "Illegal transition from 'CREATED' to 'CREATED'")
    res_transition = obj.transition('CREATED', 'CUSTOMER')
    assert res_transition == (False, "Illegal transition from 'CREATED' to 'CREATED'")
    res_is_terminal = obj.is_terminal()
    assert res_is_terminal is False
    res_get_audit_trail = obj.get_audit_trail()
    assert res_get_audit_trail == ['INITIAL->CREATED by SYSTEM']
def test_validate_transition_valid_created_to_pending_payment():
    result = validate_transition('CREATED', 'PENDING_PAYMENT', 'CUSTOMER', 100.0)
    assert result == (True, None)
def test_validate_transition_valid_created_to_cancelled():
    result = validate_transition('CREATED', 'CANCELLED', 'ADMIN', 100.0)
    assert result == (True, None)
def test_validate_transition_valid_pending_payment_to_paid():
    result = validate_transition('PENDING_PAYMENT', 'PAID', 'CUSTOMER', 100.0)
    assert result == (True, None)
def test_validate_transition_valid_pending_payment_to_cancelled():
    result = validate_transition('PENDING_PAYMENT', 'CANCELLED', 'ADMIN', 100.0)
    assert result == (True, None)
def test_validate_transition_valid_paid_to_processing():
    result = validate_transition('PAID', 'PROCESSING', 'CUSTOMER', 100.0)
    assert result == (True, None)
def test_validate_transition_valid_paid_to_refunded():
    result = validate_transition('PAID', 'REFUNDED', 'ADMIN', 100.0)
    assert result == (True, None)
def test_validate_transition_valid_processing_to_shipped():
    result = validate_transition('PROCESSING', 'SHIPPED', 'CUSTOMER', 100.0)
    assert result == (True, None)
def test_validate_transition_valid_processing_to_cancelled():
    result = validate_transition('PROCESSING', 'CANCELLED', 'ADMIN', 100.0)
    assert result == (True, None)
def test_validate_transition_valid_shipped_to_delivered():
    result = validate_transition('SHIPPED', 'DELIVERED', 'CUSTOMER', 100.0)
    assert result == (True, None)
def test_validate_transition_valid_shipped_to_returned():
    result = validate_transition('SHIPPED', 'RETURNED', 'CUSTOMER', 100.0)
    assert result == (True, None)
def test_validate_transition_valid_delivered_to_completed():
    result = validate_transition('DELIVERED', 'COMPLETED', 'CUSTOMER', 100.0)
    assert result == (True, None)
def test_validate_transition_valid_returned_to_refunded():
    result = validate_transition('RETURNED', 'REFUNDED', 'ADMIN', 100.0)
    assert result == (True, None)
def test_validate_transition_guard_invalid_src():
    result = validate_transition('INVALID_SRC_STATE', 'CREATED', 'CUSTOMER', 100.0)
    assert result == (False, "Unknown source state 'INVALID_SRC_STATE'")
def test_validate_transition_guard_invalid_tgt():
    result = validate_transition('CREATED', 'INVALID_TGT_STATE', 'CUSTOMER', 100.0)
    assert result == (False, "Unknown target state 'INVALID_TGT_STATE'")
def test_validate_transition_guard_illegal_step():
    result = validate_transition('CREATED', 'PAID', 'CUSTOMER', 100.0)
    assert result == (False, "Illegal transition from 'CREATED' to 'PAID'")
def test_validate_transition_guard_unauthorized_role():
    result = validate_transition('CREATED', 'PENDING_PAYMENT', 'HACKER', 100.0)
    assert result == (False, "Unauthorized role 'HACKER'")
def test_validate_transition_guard_support_role_admin():
    result = validate_transition('PAID', 'REFUNDED', 'SUPPORT', 100.0)
    assert result == (True, None)
def test_validate_transition_guard_admin_cancel_customer_rejected():
    result = validate_transition('CREATED', 'CANCELLED', 'CUSTOMER', 100.0)
    assert result == (False, "State 'CANCELLED' requires administrative privileges")
def test_validate_transition_guard_admin_required_cancelled():
    result = validate_transition('PAID', 'CANCELLED', 'CUSTOMER', 100.0)
    assert result == (False, "Illegal transition from 'PAID' to 'CANCELLED'")
def test_validate_transition_guard_admin_required_refunded():
    result = validate_transition('PAID', 'REFUNDED', 'CUSTOMER', 100.0)
    assert result == (False, "State 'REFUNDED' requires administrative privileges")
def test_validate_transition_guard_high_value_customer():
    result = validate_transition('PENDING_PAYMENT', 'PAID', 'CUSTOMER', 5000.0)
    assert result == (False, 'High-value transactions require merchant or admin confirmation')
def test_validate_transition_guard_high_value_merchant():
    result = validate_transition('PENDING_PAYMENT', 'PAID', 'MERCHANT', 5000.0)
    assert result == (True, None)
def test_validate_transition_guard_high_value_customer_allowed_4999():
    result = validate_transition('PENDING_PAYMENT', 'PAID', 'CUSTOMER', 4999.0)
    assert result == (True, None)
def test_transition_order_state_valid():
    result = transition_order_state('CREATED', 'PENDING_PAYMENT', 'CUSTOMER', 100.0)
    assert result == (True, 'PENDING_PAYMENT')
def test_transition_order_state_invalid():
    result = transition_order_state('INVALID', 'PENDING_PAYMENT', 'CUSTOMER', 100.0)
    assert result == (False, "Unknown source state 'INVALID'")
def test_OrderFSM_default_parameters():
    fsm = OrderFSM()
    assert fsm.order_id == 'ORD-001'
    assert fsm.state == 'CREATED'
    assert fsm.amount == 100.0
    res_can = fsm.can_transition()
    assert res_can == (True, None)
    res_tr = fsm.transition()
    assert res_tr == (True, 'PENDING_PAYMENT')
def test_OrderFSM_custom_initial_state():
    fsm = OrderFSM(initial_state='PAID')
    assert fsm.state == 'PAID'
def test_OrderFSM_invalid_initial_state_fallback():
    fsm = OrderFSM(initial_state='NON_EXISTENT_STATE')
    assert fsm.state == 'CREATED'
def test_OrderFSM_initial_history():
    fsm = OrderFSM()
    assert fsm.history == [('INITIAL', 'CREATED', 'SYSTEM')]
def test_OrderFSM_complete_lifecycle_path():
    fsm = OrderFSM(order_id='ORD-999', amount=250.0, initial_state='CREATED')
    assert fsm.state == 'CREATED'
    assert not fsm.is_terminal()
    ok, st = fsm.transition('PENDING_PAYMENT', user_role='CUSTOMER')
    assert ok and st == 'PENDING_PAYMENT'
    ok, st = fsm.transition('PAID', user_role='CUSTOMER')
    assert ok and st == 'PAID'
    ok, st = fsm.transition('PROCESSING', user_role='MERCHANT')
    assert ok and st == 'PROCESSING'
    ok, st = fsm.transition('SHIPPED', user_role='MERCHANT')
    assert ok and st == 'SHIPPED'
    ok, st = fsm.transition('DELIVERED', user_role='MERCHANT')
    assert ok and st == 'DELIVERED'
    ok, st = fsm.transition('COMPLETED', user_role='CUSTOMER')
    assert ok and st == 'COMPLETED'
    assert fsm.is_terminal()
def test_OrderFSM_return_and_refund_lifecycle():
    fsm = OrderFSM(initial_state='SHIPPED')
    ok, st = fsm.transition('RETURNED', user_role='CUSTOMER')
    assert ok and st == 'RETURNED'
    ok, st = fsm.transition('REFUNDED', user_role='ADMIN')
    assert ok and st == 'REFUNDED'
    assert fsm.is_terminal()
def test_OrderFSM_cancellation_lifecycle():
    fsm = OrderFSM(initial_state='PROCESSING')
    ok, st = fsm.transition('CANCELLED', user_role='ADMIN')
    assert ok and st == 'CANCELLED'
    assert fsm.is_terminal()
def test_OrderFSM_audit_trail_formatting():
    fsm = OrderFSM(order_id='ORD-001', amount=100.0, initial_state='CREATED')
    fsm.transition('PENDING_PAYMENT', user_role='CUSTOMER')
    assert fsm.get_audit_trail() == ['INITIAL->CREATED by SYSTEM', 'CREATED->PENDING_PAYMENT by CUSTOMER']
def test_OrderFSM_illegal_transition_rejection():
    fsm = OrderFSM(initial_state='CREATED')
    ok, err = fsm.transition('PAID', user_role='CUSTOMER')
    assert ok is False
    assert "Illegal transition from 'CREATED' to 'PAID'" in err
def test_OrderFSM_admin_role_rejection():
    fsm = OrderFSM(initial_state='PAID')
    ok, err = fsm.transition('REFUNDED', user_role='CUSTOMER')
    assert ok is False
    assert "State 'REFUNDED' requires administrative privileges" in err