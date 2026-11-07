from decimal import Decimal, ROUND_HALF_UP

def calculate_sales_tax(price: str, tax_rate: str) -> Decimal:
    p = Decimal(price)
    rate = Decimal(tax_rate)
    tax = p * rate
    return tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
