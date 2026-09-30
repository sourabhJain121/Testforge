"""
classifier.py - Lightweight Neural Mutant Difficulty Classifier in MLX.

Author: Shreshth & Sourabh
Course: CSE3101 - Agentic AI

Runs natively on Apple Silicon GPU via Apple MLX (`Device(gpu, 0)`).
Predicts whether a mutant is 'trivial' or 'subtle/hard' based on AST context
and diffusion features, allowing the Test Generator Agent to allocate dynamic token
budget to tough mutants.
"""

from __future__ import annotations
import math
import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
from typing import List, Dict, Tuple
from testforge.state import MutantRecord


class MutantDifficultyClassifier(nn.Module):
    """
    MLP model executed directly on Apple Silicon GPU via Metal shaders in MLX.
    Features:
      - one-hot mutation type (4)
      - normalized line number (1)
      - diff size in tokens/chars (1)
      - AST depth / complexity proxy (2)
    Total input dimension = 8 -> Hidden 16 -> Output 2 (0: easy, 1: hard)
    """
    def __init__(self, input_dim: int = 8, hidden_dim: int = 16, num_classes: int = 2):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, num_classes)

    def __call__(self, x: mx.array) -> mx.array:
        x = self.relu(self.fc1(x))
        x = self.fc2(x)
        return x


def extract_features(mutant: MutantRecord, total_lines: int = 50) -> List[float]:
    """
    Extracts deterministic vector representation for an AST mutant.
    """
    type_map = {
        "COMP_OP": [1.0, 0.0, 0.0, 0.0],
        "BOUNDARY_SWAP": [1.0, 0.0, 0.0, 0.0],
        "ARITH_OP": [0.0, 1.0, 0.0, 0.0],
        "MATH_FUNC": [0.0, 1.0, 0.0, 0.0],
        "COND_INV": [0.0, 0.0, 1.0, 0.0],
        "LOGICAL_CONN": [0.0, 0.0, 1.0, 0.0],
        "RETURN_VAL": [0.0, 0.0, 0.0, 1.0],
        "OFF_BY_ONE": [0.5, 0.5, 0.0, 0.0]
    }
    vec = list(type_map.get(mutant.mutation_type, [0.0, 0.0, 0.0, 0.0]))
    
    # Normalized line number
    norm_line = min(1.0, mutant.line_number / max(1, total_lines))
    vec.append(norm_line)
    
    # Diff length
    diff_len = min(1.0, len(mutant.unified_diff) / 500.0)
    vec.append(diff_len)
    
    # Heuristic complexity proxy
    has_arith = 1.0 if mutant.mutation_type in ("ARITH_OP", "COMP_OP", "BOUNDARY_SWAP", "OFF_BY_ONE", "MATH_FUNC") else 0.0
    vec.append(has_arith)
    vec.append(1.0 if mutant.mutation_type in ("COND_INV", "LOGICAL_CONN") else 0.0)
    
    return vec


class MutantTriageModel:
    """
    Handles local model training and inference on Apple Silicon GPU.
    """
    def __init__(self):
        self.model = MutantDifficultyClassifier()
        # Initialize weights
        mx.eval(self.model.parameters())

    def train_on_history(self, dataset: List[Tuple[List[float], int]], epochs: int = 30, lr: float = 0.02) -> float:
        """
        Trains the classifier locally on past iteration outcomes (e.g. killed vs survived).
        """
        if not dataset:
            return 0.0

        X_raw = [item[0] for item in dataset]
        y_raw = [item[1] for item in dataset]

        X = mx.array(X_raw, dtype=mx.float32)
        y = mx.array(y_raw, dtype=mx.int32)

        optimizer = optim.Adam(learning_rate=lr)

        def loss_fn(model, x_in, y_in):
            logits = model(x_in)
            return nn.losses.cross_entropy(logits, y_in, reduction="mean")

        loss_and_grad_fn = nn.value_and_grad(self.model, loss_fn)

        final_loss = 0.0
        for _ in range(epochs):
            loss, grads = loss_and_grad_fn(self.model, X, y)
            optimizer.update(self.model, grads)
            mx.eval(self.model.parameters(), optimizer.state)
            final_loss = loss.item()

        return final_loss

    def predict_difficulty(self, mutants: List[MutantRecord]) -> List[str]:
        """
        Returns classification: 'HIGH_PRIORITY_HARD' or 'STANDARD'
        """
        if not mutants:
            return []

        features = [extract_features(m) for m in mutants]
        X = mx.array(features, dtype=mx.float32)
        logits = self.model(X)
        predictions = mx.argmax(logits, axis=-1).tolist()

        return ["HIGH_PRIORITY_HARD" if p == 1 else "STANDARD" for p in predictions]
