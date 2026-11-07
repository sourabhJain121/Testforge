"""
accel.py - Apple Silicon & Hardware Acceleration Discovery Engine.

Optimized for:
  - Apple Silicon M-series (M1/M2/M3/M4) unified memory architecture
  - Multi-core CPU ProcessPool sizing
  - MLX (native Apple Silicon ML framework) and PyTorch MPS availability hooks

Authors: Sourabh & Shreshth
"""

from __future__ import annotations

import os
import platform
from typing import Any, Dict

import psutil


class HardwareProfile:
    def __init__(self):
        self.os_system = platform.system()
        self.machine = platform.machine()
        self.cpu_count = os.cpu_count() or 4
        self.total_memory_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
        self.is_apple_silicon = (self.os_system == "Darwin" and self.machine == "arm64")

        # Check MLX availability
        self.has_mlx = False
        try:
            import mlx.core as mx  # type: ignore
            self.has_mlx = True
        except ImportError:
            self.has_mlx = False

        # Recommended sandbox worker pool size
        # Sized to leave headroom for OS and interactive LLM processes while saturating cores
        if self.is_apple_silicon:
            # e.g., 10 cores on M2 Pro -> 8 worker processes for concurrent sandbox runs
            self.recommended_workers = max(1, min(self.cpu_count - 1, 8))
        else:
            self.recommended_workers = max(1, self.cpu_count - 1)

    def summary(self) -> Dict[str, Any]:
        return {
            "os": self.os_system,
            "architecture": self.machine,
            "cpu_cores": self.cpu_count,
            "total_ram_gb": self.total_memory_gb,
            "is_apple_silicon": self.is_apple_silicon,
            "has_mlx": self.has_mlx,
            "recommended_workers": self.recommended_workers
        }

# Global singleton profile instance
hw_profile = HardwareProfile()
