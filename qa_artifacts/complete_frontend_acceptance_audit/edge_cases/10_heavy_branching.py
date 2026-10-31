def classify_tax_bracket(income: float, filing_status: str, has_dependents: bool, is_senior: bool) -> float:
    if income < 0:
        return 0.0
    rate = 0.10
    if filing_status == "single":
        if income > 100000:
            rate = 0.32
        elif income > 50000:
            rate = 0.22
        elif income > 20000:
            rate = 0.12
    elif filing_status == "married_joint":
        if income > 200000:
            rate = 0.32
        elif income > 100000:
            rate = 0.22
        elif income > 40000:
            rate = 0.12
    elif filing_status == "head_of_household":
        if income > 150000:
            rate = 0.32
        elif income > 75000:
            rate = 0.22
        elif income > 30000:
            rate = 0.12
    else:
        rate = 0.25

    if has_dependents and rate > 0.12:
        rate -= 0.02
    if is_senior and rate > 0.10:
        rate -= 0.01

    return round(rate, 2)
