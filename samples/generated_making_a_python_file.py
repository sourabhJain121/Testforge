"""
Shopping Cart and Discount Engine Module.

This module provides a robust, thread-safe, and highly customizable shopping
cart system with dynamic coupon discount application, tax calculation, and 
boundary condition handling. Standard library `decimal.Decimal` is used for 
all monetary calculations to prevent floating-point precision issues.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple


# Currency & Numerical Precision Utilities
MONEY_PRECISION = Decimal("0.01")
PERCENT_PRECISION = Decimal("0.0001")


def quantize_money(amount: Decimal | float | int | str) -> Decimal:
    """Quantize an input value into standard 2-decimal place currency standard."""
    if not isinstance(amount, Decimal):
        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError) as err:
            raise ValueError(f"Invalid monetary value: {amount}") from err
    return amount.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)


def quantize_rate(rate: Decimal | float | int | str) -> Decimal:
    """Quantize a percentage or rate value to 4-decimal place precision."""
    if not isinstance(rate, Decimal):
        try:
            rate = Decimal(str(rate))
        except (InvalidOperation, TypeError, ValueError) as err:
            raise ValueError(f"Invalid rate/percentage value: {rate}") from err
    return rate.quantize(PERCENT_PRECISION, rounding=ROUND_HALF_UP)


# Exceptions
class CartException(Exception):
    """Base exception for cart operations."""


class InvalidQuantityError(CartException):
    """Raised when an invalid item quantity is provided."""


class ProductNotFoundError(CartException):
    """Raised when an operation targets a product not in the cart."""


class CouponValidationError(CartException):
    """Raised when a coupon fails validation rules."""


# Enums
class DiscountType(Enum):
    """Supported types of coupon discounts."""
    PERCENTAGE_CART = auto()
    FIXED_CART = auto()
    PERCENTAGE_PRODUCTS = auto()
    FIXED_PRODUCTS = auto()


# Domain Models
@dataclass(frozen=True)
class Product:
    """Represents a product in the catalog.

    Attributes:
        id: Unique product identifier.
        name: Name of the product.
        price: Unit price (must be non-negative).
        tax_rate: Applicable tax rate as a decimal (e.g., 0.07 for 7%).
        category: Optional category classification.
    """
    id: str
    name: str
    price: Decimal
    tax_rate: Decimal = field(default_factory=lambda: Decimal("0.00"))
    category: Optional[str] = None

    def __post_init__(self) -> object:
        # Immutable dataclass workaround for post-init attribute quantization
        object.__setattr__(self, "price", quantize_money(self.price))
        object.__setattr__(self, "tax_rate", quantize_rate(self.tax_rate))

        if self.price < Decimal("0.00"):
            raise ValueError(f"Product price cannot be negative: {self.price}")
        if self.tax_rate < Decimal("0.00"):
            raise ValueError(f"Product tax rate cannot be negative: {self.tax_rate}")
        if not self.id or not self.id.strip():
            raise ValueError("Product ID cannot be empty.")


@dataclass
class Coupon:
    """Represents a discount coupon with boundary restrictions.

    Attributes:
        code: Unique uppercase coupon code.
        discount_type: Type of discount logic to apply.
        discount_value: Value of the discount (percentage e.g. 0.15 or fixed e.g. 10.00).
        min_cart_subtotal: Minimum cart subtotal required to apply.
        min_item_quantity: Minimum total quantity of cart items required.
        applicable_product_ids: Specific product IDs this coupon applies to.
        applicable_categories: Specific categories this coupon applies to.
        expiration_date: UTC datetime after which coupon is invalid.
        max_discount_amount: Cap on maximum allowable discount amount.
        is_stackable: Whether this coupon can be combined with other coupons.
        usage_limit: Maximum global redemptions allowed for coupon.
        usage_count: Current number of times coupon has been redeemed.
    """
    code: str
    discount_type: DiscountType
    discount_value: Decimal
    min_cart_subtotal: Decimal = Decimal("0.00")
    min_item_quantity: int = 0
    applicable_product_ids: Optional[Set[str]] = None
    applicable_categories: Optional[Set[str]] = None
    expiration_date: Optional[datetime] = None
    max_discount_amount: Optional[Decimal] = None
    is_stackable: bool = True
    usage_limit: Optional[int] = None
    usage_count: int = 0

    def __post_init__(self) -> None:
        self.code = self.code.strip().upper()
        if not self.code:
            raise ValueError("Coupon code cannot be empty.")

        if self.discount_type in (DiscountType.PERCENTAGE_CART, DiscountType.PERCENTAGE_PRODUCTS):
            self.discount_value = quantize_rate(self.discount_value)
            if not (Decimal("0.00") < self.discount_value <= Decimal("1.00")):
                raise ValueError(f"Percentage discount must be between 0.00 and 1.00: {self.discount_value}")
        else:
            self.discount_value = quantize_money(self.discount_value)
            if self.discount_value <= Decimal("0.00"):
                raise ValueError(f"Fixed discount value must be strictly positive: {self.discount_value}")

        self.min_cart_subtotal = quantize_money(self.min_cart_subtotal)
        if self.max_discount_amount is not None:
            self.max_discount_amount = quantize_money(self.max_discount_amount)
            if self.max_discount_amount <= Decimal("0.00"):
                raise ValueError("max_discount_amount must be greater than 0.")

        if self.min_cart_subtotal < Decimal("0.00"):
            raise ValueError("Minimum cart subtotal cannot be negative.")
        if self.min_item_quantity < 0:
            raise ValueError("Minimum item quantity cannot be negative.")
        if self.usage_limit is not None and self.usage_limit < 0:
            raise ValueError("Usage limit cannot be negative.")

    def is_expired(self, current_time: Optional[datetime] = None) -> bool:
        """Check if coupon has passed its expiration datetime."""
        if self.expiration_date is None:
            return False
        now = current_time or datetime.now(timezone.utc)
        if self.expiration_date.tzinfo is None:
            # Assume UTC if naive datetime provided
            return now >= self.expiration_date.replace(tzinfo=timezone.utc)
        return now >= self.expiration_date

    def is_limit_exceeded(self) -> bool:
        """Check if coupon usage limit has been reached."""
        if self.usage_limit is None:
            return False
        return self.usage_count >= self.usage_limit


@dataclass(frozen=True)
class AppliedDiscount:
    """Details of a single discount applied to the cart calculation."""
    coupon_code: str
    discount_type: DiscountType
    amount: Decimal
    description: str


@dataclass(frozen=True)
class CartSummary:
    """Immutable representation of calculated shopping cart totals."""
    subtotal: Decimal
    discount_total: Decimal
    taxable_subtotal: Decimal
    tax_total: Decimal
    grand_total: Decimal
    applied_discounts: List[AppliedDiscount]
    item_count: int


# Shopping Cart Implementation
class ShoppingCart:
    """Shopping cart managing products, quantity updates, dynamic pricing, and coupons."""

    def __init__(self) -> None:
        self._items: Dict[str, Dict[str, object]] = {}
        self._coupons: Dict[str, Coupon] = {}

    @property
    def items(self) -> Dict[str, Dict[str, object]]:
        """Return shallow copy of items in cart."""
        return {pid: dict(data) for pid, data in self._items.items()}

    @property
    def coupons(self) -> List[Coupon]:
        """Return list of coupons attached to cart."""
        return list(self._coupons.values())

    def add_item(self, product: Product, quantity: int = 1) -> None:
        """Add product to cart or increment quantity if already present."""
        if not isinstance(quantity, int) or quantity <= 0:
            raise InvalidQuantityError(f"Quantity must be a positive integer. Got: {quantity}")

        pid = product.id
        if pid in self._items:
            current_qty = self._items[pid]["quantity"]
            self._items[pid]["quantity"] = current_qty + quantity
        else:
            self._items[pid] = {
                "product": product,
                "quantity": quantity
            }

    def update_quantity(self, product_id: str, quantity: int) -> None:
        """Update product quantity in cart. If quantity is 0, item is removed."""
        if product_id not in self._items:
            raise ProductNotFoundError(f"Product ID '{product_id}' not found in cart.")

        if not isinstance(quantity, int) or quantity < 0:
            raise InvalidQuantityError(f"Quantity must be a non-negative integer. Got: {quantity}")

        if quantity == 0:
            self.remove_item(product_id)
        else:
            self._items[product_id]["quantity"] = quantity

    def remove_item(self, product_id: str) -> None:
        """Remove a product completely from cart."""
        if product_id not in self._items:
            raise ProductNotFoundError(f"Product ID '{product_id}' not in cart.")
        del self._items[product_id]

    def clear(self) -> None:
        """Empty cart items and clear applied coupons."""
        self._items.clear()
        self._coupons.clear()

    def apply_coupon(self, coupon: Coupon, current_time: Optional[datetime] = None) -> None:
        """Validate and attach a coupon to the shopping cart."""
        code = coupon.code

        if coupon.is_expired(current_time):
            raise CouponValidationError(f"Coupon '{code}' is expired.")

        if coupon.is_limit_exceeded():
            raise CouponValidationError(f"Coupon '{code}' has reached its usage limit.")

        # Stacking logic rules
        if not coupon.is_stackable:
            if len(self._coupons) > 0 and not (len(self._coupons) == 1 and code in self._coupons):
                raise CouponValidationError(
                    f"Non-stackable coupon '{code}' cannot be applied alongside existing coupons."
                )
        else:
            for existing in self._coupons.values():
                if not existing.is_stackable and existing.code != code:
                    raise CouponValidationError(
                        f"Cannot add stackable coupon '{code}' because non-stackable coupon "
                        f"'{existing.code}' is active."
                    )

        # Store coupon
        self._coupons[code] = coupon

    def remove_coupon(self, coupon_code: str) -> bool:
        """Remove coupon by code. Returns True if removed, False if not present."""
        code = coupon_code.strip().upper()
        if code in self._coupons:
            del self._coupons[code]
            return True
        return False

    def get_total_item_count(self) -> int:
        """Calculate total number of individual items in the cart."""
        return sum(item_data["quantity"] for item_data in self._items.values())

    def get_subtotal(self) -> Decimal:
        """Calculate gross subtotal without coupons or taxes."""
        subtotal = Decimal("0.00")
        for item_data in self._items.values():
            product: Product = item_data["product"]
            quantity: int = item_data["quantity"]
            subtotal += product.price * Decimal(quantity)
        return quantize_money(subtotal)

    def _validate_coupon_conditions(self, coupon: Coupon, subtotal: Decimal, total_qty: int) -> None:
        """Verify dynamic state conditions for a coupon (e.g. min spend/quantity)."""
        if subtotal < coupon.min_cart_subtotal:
            raise CouponValidationError(
                f"Coupon '{coupon.code}' requires a minimum subtotal of ${coupon.min_cart_subtotal:.2f}. "
                f"Current subtotal: ${subtotal:.2f}"
            )
        if total_qty < coupon.min_item_quantity:
            raise CouponValidationError(
                f"Coupon '{coupon.code}' requires a minimum item count of {coupon.min_item_quantity}. "
                f"Current count: {total_qty}"
            )

    def calculate_totals(self, current_time: Optional[datetime] = None) -> CartSummary:
        """Perform comprehensive tax and discount calculation for current cart state.

        Returns:
            CartSummary containing full financial details.
        
        Raises:
            CouponValidationError: If an applied coupon fails live constraints.
        """
        subtotal = self.get_subtotal()
        total_qty = self.get_total_item_count()

        if subtotal == Decimal("0.00") or not self._items:
            return CartSummary(
                subtotal=Decimal("0.00"),
                discount_total=Decimal("0.00"),
                taxable_subtotal=Decimal("0.00"),
                tax_total=Decimal("0.00"),
                grand_total=Decimal("0.00"),
                applied_discounts=[],
                item_count=0,
            )

        # Track mutable prices per product line item for tax and discount distribution
        # Line price = product.price * quantity
        line_item_balances: Dict[str, Decimal] = {
            pid: data["product"].price * Decimal(data["quantity"])
            for pid, data in self._items.items()
        }

        applied_discounts: List[AppliedDiscount] = []

        # Validate and apply coupons in defined order (Product-specific first, then Cart-level)
        sorted_coupons = sorted(
            self._coupons.values(),
            key=lambda c: 0 if c.discount_type in (DiscountType.PERCENTAGE_PRODUCTS, DiscountType.FIXED_PRODUCTS) else 1
        )

        for coupon in sorted_coupons:
            if coupon.is_expired(current_time):
                raise CouponValidationError(f"Coupon '{coupon.code}' has expired.")
            if coupon.is_limit_exceeded():
                raise CouponValidationError(f"Coupon '{coupon.code}' limit exceeded.")

            self._validate_coupon_conditions(coupon, subtotal, total_qty)

            coupon_discount = Decimal("0.00")

            if coupon.discount_type == DiscountType.PERCENTAGE_PRODUCTS:
                coupon_discount = self._apply_product_percentage_discount(coupon, line_item_balances)
            elif coupon.discount_type == DiscountType.FIXED_PRODUCTS:
                coupon_discount = self._apply_product_fixed_discount(coupon, line_item_balances)
            elif coupon.discount_type == DiscountType.PERCENTAGE_CART:
                coupon_discount = self._apply_cart_percentage_discount(coupon, line_item_balances)
            elif coupon.discount_type == DiscountType.FIXED_CART:
                coupon_discount = self._apply_cart_fixed_discount(coupon, line_item_balances)

            coupon_discount = quantize_money(coupon_discount)
            
            if coupon_discount > Decimal("0.00"):
                applied_discounts.append(
                    AppliedDiscount(
                        coupon_code=coupon.code,
                        discount_type=coupon.discount_type,
                        amount=coupon_discount,
                        description=f"Discount from coupon code: {coupon.code}"
                    )
                )

        total_discount = sum((d.amount for d in applied_discounts), Decimal("0.00"))
        total_discount = min(total_discount, subtotal)  # Safety boundary check

        # Calculate taxes on post-discount line item balances
        tax_total = Decimal("0.00")
        taxable_subtotal = Decimal("0.00")

        for pid, item_data in self._items.items():
            product: Product = item_data["product"]
            post_discount_line_price = max(Decimal("0.00"), line_item_balances[pid])

            if product.tax_rate > Decimal("0.00"):
                taxable_subtotal += post_discount_line_price
                line_tax = quantize_money(post_discount_line_price * product.tax_rate)
                tax_total += line_tax

        taxable_subtotal = quantize_money(taxable_subtotal)
        tax_total = quantize_money(tax_total)
        grand_total = quantize_money(subtotal - total_discount + tax_total)

        return CartSummary(
            subtotal=subtotal,
            discount_total=total_discount,
            taxable_subtotal=taxable_subtotal,
            tax_total=tax_total,
            grand_total=grand_total,
            applied_discounts=applied_discounts,
            item_count=total_qty,
        )

    def _is_product_eligible(self, product: Product, coupon: Coupon) -> bool:
        """Determine if a product satisfies coupon product/category constraints."""
        if coupon.applicable_product_ids is not None:
            if product.id not in coupon.applicable_product_ids:
                return False
        if coupon.applicable_categories is not None:
            if product.category not in coupon.applicable_categories:
                return False
        return True

    def _apply_product_percentage_discount(self, coupon: Coupon, balances: Dict[str, Decimal]) -> Decimal:
        """Apply percentage discount to matching product lines."""
        total_applied = Decimal("0.00")
        for pid, balance in balances.items():
            product: Product = self._items[pid]["product"]
            if balance > Decimal("0.00") and self._is_product_eligible(product, coupon):
                line_discount = balance * coupon.discount_value
                balances[pid] -= line_discount
                total_applied += line_discount

        if coupon.max_discount_amount is not None and total_applied > coupon.max_discount_amount:
            # Re-adjust balance proportional reduction if cap exceeded
            cap = coupon.max_discount_amount
            excess = total_applied - cap
            # Give back the excess proportionally
            for pid, balance in balances.items():
                product: Product = self._items[pid]["product"]
                if self._is_product_eligible(product, coupon):
                    line_discount = self._items[pid]["product"].price * Decimal(self._items[pid]["quantity"]) * coupon.discount_value
                    rebound = (line_discount / total_applied) * excess
                    balances[pid] += rebound
            total_applied = cap

        return total_applied

    def _apply_product_fixed_discount(self, coupon: Coupon, balances: Dict[str, Decimal]) -> Decimal:
        """Apply fixed unit discount to matching products."""
        total_applied = Decimal("0.00")
        for pid, balance in balances.items():
            product: Product = self._items[pid]["product"]
            qty: int = self._items[pid]["quantity"]
            if balance > Decimal("0.00") and self._is_product_eligible(product, coupon):
                line_discount = min(balance, coupon.discount_value * Decimal(qty))
                balances[pid] -= line_discount
                total_applied += line_discount

        if coupon.max_discount_amount is not None and total_applied > coupon.max_discount_amount:
            cap = coupon.max_discount_amount
            excess = total_applied - cap
            # Refund excess proportionally
            for pid in balances:
                product: Product = self._items[pid]["product"]
                if self._is_product_eligible(product, coupon):
                    portion = (balances[pid] / total_applied) if total_applied > 0 else Decimal("0.00")
                    balances[pid] += excess * portion
            total_applied = cap

        return total_applied

    def _apply_cart_percentage_discount(self, coupon: Coupon, balances: Dict[str, Decimal]) -> Decimal:
        """Apply percentage discount to entire remaining cart balance."""
        current_balance_sum = sum(balances.values())
        if current_balance_sum <= Decimal("0.00"):
            return Decimal("0.00")

        calculated_discount = current_balance_sum * coupon.discount_value

        if coupon.max_discount_amount is not None:
            calculated_discount = min(calculated_discount, coupon.max_discount_amount)

        calculated_discount = min(calculated_discount, current_balance_sum)

        # Distribute discount proportionally across all items with remaining balance
        for pid, bal in list(balances.items()):
            if bal > Decimal("0.00"):
                ratio = bal / current_balance_sum
                balances[pid] -= calculated_discount * ratio

        return calculated_discount

    def _apply_cart_fixed_discount(self, coupon: Coupon, balances: Dict[str, Decimal]) -> Decimal:
        """Apply fixed monetary discount to overall cart balance."""
        current_balance_sum = sum(balances.values())
        if current_balance_sum <= Decimal("0.00"):
            return Decimal("0.00")

        calculated_discount = min(coupon.discount_value, current_balance_sum)

        if coupon.max_discount_amount is not None:
            calculated_discount = min(calculated_discount, coupon.max_discount_amount)

        # Proportional reduction across lines
        for pid, bal in list(balances.items()):
            if bal > Decimal("0.00"):
                ratio = bal / current_balance_sum
                balances[pid] -= calculated_discount * ratio

        return calculated_discount