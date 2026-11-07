"""
samples/inventory_ledger.py - Warehouse Inventory Ledger & Two-Phase Reservation System.
License: MIT
Author: TestForge Benchmark Suite
LOC: ~120 lines
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple


class ReservationStatus(Enum):
    PENDING = auto()
    COMMITTED = auto()
    CANCELLED = auto()
    EXPIRED = auto()


@dataclass
class ReservationRecord:
    reservation_id: str
    sku: str
    quantity: int
    expires_at: float
    status: ReservationStatus = ReservationStatus.PENDING


@dataclass
class ItemStock:
    sku: str
    on_hand: int = 0
    reserved: int = 0

    @property
    def available(self) -> int:
        return self.on_hand - self.reserved


class InventoryLedger:
    """
    Two-phase transactional inventory management ledger:
    - Step 1: Reserve stock with a time-to-live (TTL).
    - Step 2: Commit reservation (deducts stock) or cancel/expire (releases reserved count).
    Guarantees non-negative available stock and audit trail integrity.
    """

    def __init__(self, default_ttl_seconds: float = 300.0):
        self.default_ttl = default_ttl_seconds
        self._stock: Dict[str, ItemStock] = {}
        self._reservations: Dict[str, ReservationRecord] = {}
        self._audit_log: List[str] = []

    def restock(self, sku: str, quantity: int) -> int:
        if not sku or not sku.strip():
            raise ValueError("SKU cannot be empty")
        if quantity <= 0:
            raise ValueError(f"Restock quantity must be positive, got {quantity}")

        stock = self._stock.setdefault(sku, ItemStock(sku=sku))
        stock.on_hand += quantity
        self._audit_log.append(f"RESTOCK:{sku}:{quantity}:ON_HAND={stock.on_hand}")
        return stock.on_hand

    def get_stock(self, sku: str) -> Tuple[int, int, int]:
        """Returns (on_hand, reserved, available)."""
        stock = self._stock.get(sku)
        if not stock:
            return 0, 0, 0
        return stock.on_hand, stock.reserved, stock.available

    def create_reservation(
        self,
        reservation_id: str,
        sku: str,
        quantity: int,
        current_time: float,
        ttl_seconds: Optional[float] = None
    ) -> bool:
        if not reservation_id or reservation_id in self._reservations:
            return False
        if quantity <= 0:
            return False

        stock = self._stock.get(sku)
        if not stock or stock.available < quantity:
            return False

        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        rec = ReservationRecord(
            reservation_id=reservation_id,
            sku=sku,
            quantity=quantity,
            expires_at=current_time + ttl,
            status=ReservationStatus.PENDING,
        )
        stock.reserved += quantity
        self._reservations[reservation_id] = rec
        self._audit_log.append(f"RESERVE:{reservation_id}:{sku}:{quantity}")
        return True

    def commit_reservation(self, reservation_id: str, current_time: float) -> bool:
        rec = self._reservations.get(reservation_id)
        if not rec or rec.status != ReservationStatus.PENDING:
            return False

        if current_time > rec.expires_at:
            self._expire_reservation(rec)
            return False

        stock = self._stock.get(rec.sku)
        if not stock or stock.on_hand < rec.quantity or stock.reserved < rec.quantity:
            return False

        stock.on_hand -= rec.quantity
        stock.reserved -= rec.quantity
        rec.status = ReservationStatus.COMMITTED
        self._audit_log.append(f"COMMIT:{reservation_id}:{rec.sku}:{rec.quantity}")
        return True

    def cancel_reservation(self, reservation_id: str) -> bool:
        rec = self._reservations.get(reservation_id)
        if not rec or rec.status != ReservationStatus.PENDING:
            return False

        stock = self._stock.get(rec.sku)
        if stock:
            stock.reserved = max(0, stock.reserved - rec.quantity)
        rec.status = ReservationStatus.CANCELLED
        self._audit_log.append(f"CANCEL:{reservation_id}:{rec.sku}:{rec.quantity}")
        return True

    def _expire_reservation(self, rec: ReservationRecord) -> None:
        stock = self._stock.get(rec.sku)
        if stock:
            stock.reserved = max(0, stock.reserved - rec.quantity)
        rec.status = ReservationStatus.EXPIRED
        self._audit_log.append(f"EXPIRE:{rec.reservation_id}:{rec.sku}")

    def sweep_expired(self, current_time: float) -> int:
        expired_count = 0
        for rec in list(self._reservations.values()):
            if rec.status == ReservationStatus.PENDING and current_time > rec.expires_at:
                self._expire_reservation(rec)
                expired_count += 1
        return expired_count
