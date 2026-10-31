"""
logistics_engine.py - Realistic Warehouse Logistics, Freight, and Order Pricing Engine.
Designed for autonomous AST analysis, mutation hardening, and property verification.
"""

from __future__ import annotations
import math
import re
from typing import List, Dict, Any, Optional


class ShippingTier:
    STANDARD = "STANDARD"
    EXPRESS = "EXPRESS"
    OVERNIGHT = "OVERNIGHT"

    RATES = {
        STANDARD: 5.00,
        EXPRESS: 15.00,
        OVERNIGHT: 35.00,
    }


class WarehouseInventory:
    """Manages warehouse stock allocations, restock thresholds, and reservations."""

    def __init__(self, initial_stock: Optional[Dict[str, int]] = None):
        self._stock: Dict[str, int] = dict(initial_stock) if initial_stock else {}
        self._reservations: Dict[str, int] = {}

    def get_available_stock(self, sku: str) -> int:
        if not sku or not isinstance(sku, str):
            raise ValueError("SKU must be a non-empty string.")
        total = self._stock.get(sku, 0)
        reserved = self._reservations.get(sku, 0)
        return max(0, total - reserved)

    def reserve_stock(self, sku: str, quantity: int) -> bool:
        if quantity <= 0:
            raise ValueError("Reservation quantity must be strictly positive.")
        available = self.get_available_stock(sku)
        if available >= quantity:
            self._reservations[sku] = self._reservations.get(sku, 0) + quantity
            return True
        return False

    def release_stock(self, sku: str, quantity: int) -> bool:
        if quantity <= 0:
            raise ValueError("Release quantity must be strictly positive.")
        reserved = self._reservations.get(sku, 0)
        if reserved >= quantity:
            self._reservations[sku] = reserved - quantity
            return True
        return False

    def restock_needed(self, sku: str, threshold: int = 10) -> bool:
        return self.get_available_stock(sku) <= threshold


def calculate_item_discount(unit_price: float, quantity: int, customer_tier: str = "REGULAR") -> float:
    """
    Computes volume and customer tier discounts with boundary checks.
    Returns unit discount rate between 0.00 and 0.40.
    """
    if unit_price <= 0.0:
        raise ValueError("Unit price must be strictly positive.")
    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")

    valid_tiers = {"REGULAR", "SILVER", "GOLD", "PLATINUM"}
    tier_upper = customer_tier.upper().strip() if customer_tier else "REGULAR"
    if tier_upper not in valid_tiers:
        raise ValueError(f"Invalid customer tier: {customer_tier}. Must be one of {valid_tiers}")

    discount = 0.0

    # Volume tier calculation (boundary conditions at 5, 20, 50)
    if quantity >= 50:
        discount += 0.20
    elif quantity >= 20:
        discount += 0.12
    elif quantity >= 5:
        discount += 0.05

    # Customer loyalty tier calculation
    if tier_upper == "PLATINUM":
        discount += 0.15
    elif tier_upper == "GOLD":
        discount += 0.10
    elif tier_upper == "SILVER":
        discount += 0.05

    # Hard cap on discount rate: maximum 35%
    return min(0.35, round(discount, 2))


def estimate_freight_cost(weight_kg: float, distance_km: float, is_hazardous: bool = False) -> float:
    """
    Calculates estimated freight transit fee based on distance, weight, and hazard classification.
    """
    if weight_kg <= 0.0 or weight_kg > 5000.0:
        raise ValueError("Weight must be between 0.01 kg and 5000.0 kg.")
    if distance_km <= 0.0 or distance_km > 25000.0:
        raise ValueError("Distance must be between 0.1 km and 25000.0 km.")

    # Base formula: $12 flat handling + $0.85/kg + $0.08/km
    base_fee = 12.00 + (weight_kg * 0.85) + (distance_km * 0.08)

    # Hazardous materials surcharge: 40% additional fee with $50 minimum surcharge
    if is_hazardous:
        hazard_fee = max(50.00, base_fee * 0.40)
        base_fee += hazard_fee

    return round(base_fee, 2)


def calculate_customs_duty(declared_value: float, country_code: str, exemption_code: Optional[str] = None) -> float:
    """
    Calculates international customs tariff based on 2-letter ISO country code.
    """
    if declared_value < 0.0:
        raise ValueError("Declared value cannot be negative.")
    if not country_code or len(country_code.strip()) != 2:
        raise ValueError("Country code must be a 2-character ISO code.")

    cc = country_code.upper().strip()
    if exemption_code and exemption_code.strip().upper() == "DIPLOMATIC":
        return 0.00

    tariff_rates = {
        "US": 0.025,
        "CA": 0.030,
        "GB": 0.045,
        "DE": 0.050,
        "JP": 0.035,
        "AU": 0.040,
        "IN": 0.075,
    }

    if cc not in tariff_rates:
        raise KeyError(f"Unsupported destination customs territory: {cc}")

    rate = tariff_rates[cc]
    # $800 de minimis threshold for US
    if cc == "US" and declared_value <= 800.00:
        return 0.00

    return round(declared_value * rate, 2)


def validate_tracking_number(tracking_code: str) -> bool:
    """
    Validates carrier tracking code syntax: TRK-[A-Z]{3}-[0-9]{6}-[0-9]
    Includes modulo-7 check digit verification.
    """
    if not tracking_code or not isinstance(tracking_code, str):
        return False

    pattern = r"^TRK-([A-Z]{3})-(\d{6})-(\d)$"
    match = re.match(pattern, tracking_code.strip())
    if not match:
        return False

    _, digits_str, check_digit_str = match.groups()
    num = int(digits_str)
    expected_check = num % 7
    return int(check_digit_str) == expected_check


def compute_sla_deadline_hours(priority: int, transit_days: int) -> int:
    """
    Calculates guaranteed delivery window in total operational hours.
    Priority: 1 (Urgent) to 5 (Economy).
    """
    if priority < 1 or priority > 5:
        raise ValueError("Priority must be an integer between 1 and 5.")
    if transit_days < 1 or transit_days > 30:
        raise ValueError("Transit days must be between 1 and 30.")

    # Base 24 hours per transit day, reduced by priority factor
    multiplier = {1: 0.5, 2: 0.75, 3: 1.0, 4: 1.25, 5: 1.5}[priority]
    hours = math.ceil((transit_days * 24) * multiplier)
    return max(12, hours)


def process_bulk_order(order_items: List[Dict[str, Any]], customer_tier: str = "REGULAR", express_shipping: bool = False) -> Dict[str, Any]:
    """
    Processes a complete order package, calculates line item totals, discounts, freight, and tax.
    """
    if not isinstance(order_items, list):
        raise TypeError("Order items must be a list of item dictionaries.")
    if not order_items:
        return {
            "item_count": 0,
            "subtotal": 0.0,
            "total_discount": 0.0,
            "shipping_fee": 0.0,
            "final_total": 0.0,
            "status": "EMPTY_ORDER",
        }

    subtotal = 0.0
    total_discount = 0.0
    total_weight = 0.0

    for idx, item in enumerate(order_items):
        if not isinstance(item, dict):
            raise TypeError(f"Item at index {idx} is not a valid dictionary.")
        if "unit_price" not in item or "quantity" not in item:
            raise KeyError(f"Item at index {idx} missing required unit_price or quantity.")

        price = float(item["unit_price"])
        qty = int(item["quantity"])
        weight = float(item.get("weight_kg", 0.5))

        line_gross = price * qty
        discount_rate = calculate_item_discount(price, qty, customer_tier)
        line_discount = line_gross * discount_rate

        subtotal += line_gross
        total_discount += line_discount
        total_weight += (weight * qty)

    discounted_subtotal = subtotal - total_discount
    shipping_fee = estimate_freight_cost(max(0.5, total_weight), 250.0, is_hazardous=False)
    if express_shipping:
        shipping_fee += 20.00

    final_total = round(discounted_subtotal + shipping_fee, 2)

    return {
        "item_count": sum(int(it["quantity"]) for it in order_items),
        "gross_subtotal": round(subtotal, 2),
        "total_discount": round(total_discount, 2),
        "discounted_subtotal": round(discounted_subtotal, 2),
        "shipping_fee": round(shipping_fee, 2),
        "final_total": final_total,
        "status": "PROCESSED",
    }

