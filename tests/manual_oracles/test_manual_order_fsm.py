"""
MANUAL ORACLES: SAMPLES/ORDER_FSM.PY
Classification: MANUAL (Hand-written, Human-Authored Oracles)
Provenance: Authored during Phase 2 FSM state-space analysis to kill 60 state dictionary,
audit trail, and invalid transition mutants across deep lifecycle stages.
Rule: This file is tracked separately from autonomous pipeline synthesis.
"""

import pytest

from samples.order_fsm import OrderFSM, validate_transition


def test_manual_init_mutant_110():
    """[MANUAL ORACLE] Asserts initial state parameter binding."""
    fsm = OrderFSM(initial_state='PAID')
    assert fsm.state == 'PAID'


def test_manual_init_mutant_111():
    """[MANUAL ORACLE] Asserts initial history tuple construction."""
    fsm = OrderFSM()
    assert fsm.history == [('INITIAL', 'CREATED', 'SYSTEM')]


def test_manual_validate_transition_valid_transition():
    """[MANUAL ORACLE] Validates legal transition tuple return."""
    assert validate_transition('CREATED', 'PENDING_PAYMENT', 'CUSTOMER', 100.0) == (True, None)


def test_manual_validate_transition_invalid_source_state():
    """[MANUAL ORACLE] Validates error on unknown source state."""
    assert validate_transition('INVALID_STATE', 'PENDING_PAYMENT', 'CUSTOMER', 100.0) == (False, "Unknown source state 'INVALID_STATE'")


def test_manual_validate_transition_invalid_target_state():
    """[MANUAL ORACLE] Validates error on unknown target state."""
    assert validate_transition('CREATED', 'INVALID_STATE', 'CUSTOMER', 100.0) == (False, "Unknown target state 'INVALID_STATE'")


def test_manual_validate_transition_illegal_transition():
    """[MANUAL ORACLE] Validates rejection of illegal direct skip."""
    assert validate_transition('CREATED', 'PAID', 'CUSTOMER', 100.0) == (False, "Illegal transition from 'CREATED' to 'PAID'")


def test_manual_validate_transition_admin_required_state():
    """[MANUAL ORACLE] Validates role authorization checks."""
    assert validate_transition('PAID', 'REFUNDED', 'CUSTOMER', 100.0) == (False, "State 'REFUNDED' requires administrative privileges")


def test_manual_order_fsm_complete_lifecycle_regression():
    """[MANUAL ORACLE] Complete forward FSM path: CREATED -> PENDING_PAYMENT -> PAID -> PROCESSING -> SHIPPED -> DELIVERED -> COMPLETED."""
    fsm = OrderFSM(order_id="ORD-999", amount=250.0, initial_state="CREATED")
    assert fsm.state == "CREATED"
    assert not fsm.is_terminal()
    
    ok, st = fsm.transition("PENDING_PAYMENT", user_role="CUSTOMER")
    assert ok and st == "PENDING_PAYMENT"
    
    ok, st = fsm.transition("PAID", user_role="CUSTOMER")
    assert ok and st == "PAID"
    
    ok, st = fsm.transition("PROCESSING", user_role="MERCHANT")
    assert ok and st == "PROCESSING"
    
    ok, st = fsm.transition("SHIPPED", user_role="MERCHANT")
    assert ok and st == "SHIPPED"
    
    ok, st = fsm.transition("DELIVERED", user_role="MERCHANT")
    assert ok and st == "DELIVERED"
    
    ok, st = fsm.transition("COMPLETED", user_role="CUSTOMER")
    assert ok and st == "COMPLETED"
    assert fsm.is_terminal()


def test_manual_order_fsm_refund_and_cancel_regression():
    """[MANUAL ORACLE] Return, refund, and cancellation branch transitions."""
    fsm = OrderFSM(initial_state="SHIPPED")
    ok, st = fsm.transition("RETURNED", user_role="CUSTOMER")
    assert ok and st == "RETURNED"
    ok, st = fsm.transition("REFUNDED", user_role="ADMIN")
    assert ok and st == "REFUNDED"
    assert fsm.is_terminal()
    
    fsm2 = OrderFSM(initial_state="PROCESSING")
    ok, st = fsm2.transition("CANCELLED", user_role="ADMIN")
    assert ok and st == "CANCELLED"
    assert fsm2.is_terminal()


def test_manual_order_fsm_audit_trail_formatting_regression():
    """[MANUAL ORACLE] Audit trail string formatting and ordering."""
    fsm = OrderFSM(order_id="ORD-001", amount=100.0, initial_state="CREATED")
    fsm.transition("PENDING_PAYMENT", user_role="CUSTOMER")
    trail = fsm.get_audit_trail()
    assert trail == ["INITIAL->CREATED by SYSTEM", "CREATED->PENDING_PAYMENT by CUSTOMER"]
