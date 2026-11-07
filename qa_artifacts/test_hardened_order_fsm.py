import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from samples.order_fsm import validate_transition, transition_order_state, OrderFSM
from samples.order_fsm import validate_transition

def test_validate_transition_nominal():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_validate_transition_multi_arg_scenario():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_validate_transition_threshold_amount_5000_0():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', 5000.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_validate_transition_threshold_amount_4999_0():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', 4999.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_validate_transition_threshold_amount_5001_0():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', 5001.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_validate_transition_enum_user_role_admin():
    result = validate_transition('CREATED', 'CREATED', 'ADMIN', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_validate_transition_enum_user_role_support():
    result = validate_transition('CREATED', 'CREATED', 'SUPPORT', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_validate_transition_extreme_current_state_empty_string():
    result = validate_transition('', 'CREATED', 'CUSTOMER', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_validate_transition_extreme_current_state_single_char():
    result = validate_transition('a', 'CREATED', 'CUSTOMER', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_validate_transition_extreme_current_state_whitespace_string():
    result = validate_transition('   ', 'CREATED', 'CUSTOMER', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_validate_transition_extreme_next_state_empty_string():
    result = validate_transition('CREATED', '', 'CUSTOMER', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_validate_transition_extreme_next_state_single_char():
    result = validate_transition('CREATED', 'a', 'CUSTOMER', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_validate_transition_extreme_next_state_whitespace_string():
    result = validate_transition('CREATED', '   ', 'CUSTOMER', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_validate_transition_extreme_user_role_empty_string():
    result = validate_transition('CREATED', 'CREATED', '', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_validate_transition_extreme_user_role_single_char():
    result = validate_transition('CREATED', 'CREATED', 'a', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_validate_transition_extreme_user_role_whitespace_string():
    result = validate_transition('CREATED', 'CREATED', '   ', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_validate_transition_extreme_amount_zero():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', 0)
    assert isinstance(result, tuple) and len(result) == 2

def test_validate_transition_extreme_amount_negative_one():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', -1)
    assert isinstance(result, tuple) and len(result) == 2

def test_validate_transition_extreme_amount_negative_large():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', -100)
    assert isinstance(result, tuple) and len(result) == 2

def test_validate_transition_extreme_amount_large_positive():
    result = validate_transition('CREATED', 'CREATED', 'CUSTOMER', 10000)
    assert isinstance(result, tuple) and len(result) == 2

def test_transition_order_state_nominal():
    result = transition_order_state('CREATED', 'CREATED', 'CUSTOMER', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_transition_order_state_multi_arg_scenario():
    result = transition_order_state('CREATED', 'CREATED', 'CUSTOMER', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_transition_order_state_extreme_current_state_empty_string():
    result = transition_order_state('', 'CREATED', 'CUSTOMER', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_transition_order_state_extreme_current_state_single_char():
    result = transition_order_state('a', 'CREATED', 'CUSTOMER', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_transition_order_state_extreme_current_state_whitespace_string():
    result = transition_order_state('   ', 'CREATED', 'CUSTOMER', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_transition_order_state_extreme_next_state_empty_string():
    result = transition_order_state('CREATED', '', 'CUSTOMER', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_transition_order_state_extreme_next_state_single_char():
    result = transition_order_state('CREATED', 'a', 'CUSTOMER', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_transition_order_state_extreme_next_state_whitespace_string():
    result = transition_order_state('CREATED', '   ', 'CUSTOMER', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_transition_order_state_extreme_user_role_empty_string():
    result = transition_order_state('CREATED', 'CREATED', '', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_transition_order_state_extreme_user_role_single_char():
    result = transition_order_state('CREATED', 'CREATED', 'a', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_transition_order_state_extreme_user_role_whitespace_string():
    result = transition_order_state('CREATED', 'CREATED', '   ', 100.0)
    assert isinstance(result, tuple) and len(result) == 2

def test_transition_order_state_extreme_amount_zero():
    result = transition_order_state('CREATED', 'CREATED', 'CUSTOMER', 0)
    assert isinstance(result, tuple) and len(result) == 2

def test_transition_order_state_extreme_amount_negative_one():
    result = transition_order_state('CREATED', 'CREATED', 'CUSTOMER', -1)
    assert isinstance(result, tuple) and len(result) == 2

def test_transition_order_state_extreme_amount_negative_large():
    result = transition_order_state('CREATED', 'CREATED', 'CUSTOMER', -100)
    assert isinstance(result, tuple) and len(result) == 2

def test_transition_order_state_extreme_amount_large_positive():
    result = transition_order_state('CREATED', 'CREATED', 'CUSTOMER', 10000)
    assert isinstance(result, tuple) and len(result) == 2

def test_OrderFSM_can_transition_nominal():
    obj = OrderFSM('ORD-001', 100.0, 'CREATED')
    result = obj.can_transition('CREATED', 'CUSTOMER')
    assert isinstance(result, tuple) and len(result) == 2

def test_OrderFSM_transition_nominal():
    obj = OrderFSM('ORD-001', 100.0, 'CREATED')
    result = obj.transition('CREATED', 'CUSTOMER')
    assert isinstance(result, tuple) and len(result) == 2

def test_OrderFSM_is_terminal_nominal():
    obj = OrderFSM('ORD-001', 100.0, 'CREATED')
    result = obj.is_terminal()
    assert result is False

def test_OrderFSM_get_audit_trail_nominal():
    obj = OrderFSM('ORD-001', 100.0, 'CREATED')
    result = obj.get_audit_trail()
    assert isinstance(result, list) and len(result) == 1

def test_OrderFSM_state_and_methods():
    obj = OrderFSM('ORD-001', 100.0, 'CREATED')
    res_can_transition = obj.can_transition('CREATED', 'CUSTOMER')
    assert isinstance(res_can_transition, tuple) and len(res_can_transition) == 2
    res_transition = obj.transition('CREATED', 'CUSTOMER')
    assert isinstance(res_transition, tuple) and len(res_transition) == 2
    res_is_terminal = obj.is_terminal()
    assert res_is_terminal is False
    res_get_audit_trail = obj.get_audit_trail()
    assert isinstance(res_get_audit_trail, list) and len(res_get_audit_trail) == 1

def test_init_mutant_110():
    fsm = OrderFSM(initial_state='PAID')
    assert fsm.state == 'PAID'

def test_init_mutant_111():
    fsm = OrderFSM()
    assert fsm.history == [('INITIAL', 'CREATED', 'SYSTEM')]

def test_validate_transition_valid_transition():
    assert validate_transition('CREATED', 'PENDING_PAYMENT', 'CUSTOMER', 100.0) == (True, None)

def test_validate_transition_invalid_source_state():
    assert validate_transition('INVALID_STATE', 'PENDING_PAYMENT', 'CUSTOMER', 100.0) == (False, "Unknown source state 'INVALID_STATE'")

def test_validate_transition_invalid_target_state():
    assert validate_transition('CREATED', 'INVALID_STATE', 'CUSTOMER', 100.0) == (False, "Unknown target state 'INVALID_STATE'")

def test_validate_transition_illegal_transition():
    assert validate_transition('CREATED', 'PAID', 'CUSTOMER', 100.0) == (False, "Illegal transition from 'CREATED' to 'PAID'")

def test_validate_transition_admin_required_state():
    assert validate_transition('PAID', 'REFUNDED', 'CUSTOMER', 100.0) == (False, "State 'REFUNDED' requires administrative privileges")