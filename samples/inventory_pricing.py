"""
samples/inventory_pricing.py - Realistic e-commerce tiered discount and bulk inventory pricing engine.
"""

def compute_inventory_order(base_price: float, quantity: int, customer_tier: str, express_shipping: bool) -> float:
    """
    Computes total order price with multi-tiered discounts, volume cutoffs, and shipping fees.
    
    Rules:
      - base_price must be > 0 and quantity must be > 0.
      - Tier 'PLATINUM': 25% discount.
      - Tier 'GOLD': 15% discount.
      - Tier 'SILVER': 5% discount.
      - Other tiers: 0% discount.
      - Bulk incentive: If quantity >= 50, extra $2.00 off per item.
      - Express shipping: $25.00 flat fee, unless pre-discount subtotal >= 500.00 (then free).
      - Returns rounded total to 2 decimal places.
    """
    if base_price <= 0.0 or quantity <= 0:
        return 0.0

    subtotal = base_price * quantity

    # Determine tier percentage
    if customer_tier == "PLATINUM":
        tier_discount = 0.25
    elif customer_tier == "GOLD":
        tier_discount = 0.15
    elif customer_tier == "SILVER":
        tier_discount = 0.05
    else:
        tier_discount = 0.0

    discounted_subtotal = subtotal * (1.0 - tier_discount)

    # Bulk discount
    if quantity >= 50:
        discounted_subtotal = discounted_subtotal - (quantity * 2.0)

    # Shipping computation
    shipping_cost = 0.0
    if express_shipping:
        if subtotal < 500.0:
            shipping_cost = 25.0
        else:
            shipping_cost = 0.0

    total = discounted_subtotal + shipping_cost
    return round(max(0.0, total), 2)
