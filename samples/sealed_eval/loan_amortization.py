"""
samples/sealed_eval/loan_amortization.py

Domain: Finance
Calculates loan repayments, interest breakdowns, and amortization schedules.
"""

from typing import Dict, List, Any


def calculate_monthly_payment(principal: float, annual_rate: float, term_months: int) -> float:
    """
    Calculates monthly payment using fixed-rate amortization formula:
    M = P * [r(1+r)^n] / [(1+r)^n - 1]
    """
    if principal <= 0.0:
        raise ValueError("Principal must be greater than zero.")
    if annual_rate < 0.0:
        raise ValueError("Annual interest rate cannot be negative.")
    if term_months <= 0:
        raise ValueError("Term in months must be greater than zero.")

    if annual_rate == 0.0:
        return round(principal / term_months, 2)

    monthly_rate = annual_rate / 12.0
    factor = (1.0 + monthly_rate) ** term_months
    payment = principal * (monthly_rate * factor) / (factor - 1.0)
    return round(payment, 2)


def generate_amortization_schedule(
    principal: float, annual_rate: float, term_months: int
) -> List[Dict[str, Any]]:
    """
    Generates monthly amortization schedule with balance, principal, and interest breakdown.
    """
    if principal <= 0.0 or term_months <= 0:
        return []

    monthly_payment = calculate_monthly_payment(principal, annual_rate, term_months)
    monthly_rate = annual_rate / 12.0 if annual_rate > 0.0 else 0.0

    schedule: List[Dict[str, Any]] = []
    balance = principal

    for month in range(1, term_months + 1):
        interest_payment = round(balance * monthly_rate, 2)
        principal_payment = round(monthly_payment - interest_payment, 2)

        # Handle final month residual
        if month == term_months or principal_payment > balance:
            principal_payment = round(balance, 2)
            monthly_payment = round(principal_payment + interest_payment, 2)
            balance = 0.0
        else:
            balance = round(balance - principal_payment, 2)

        schedule.append({
            "month": month,
            "payment": monthly_payment,
            "principal_portion": principal_payment,
            "interest_portion": interest_payment,
            "remaining_balance": max(0.0, balance),
        })

    return schedule


def calculate_total_interest(principal: float, annual_rate: float, term_months: int) -> float:
    """Calculates total interest paid over the life of the loan."""
    if principal <= 0.0 or annual_rate <= 0.0 or term_months <= 0:
        return 0.0
    schedule = generate_amortization_schedule(principal, annual_rate, term_months)
    total_interest = sum(entry["interest_portion"] for entry in schedule)
    return round(total_interest, 2)
