"""
Unit tests for Apple Silicon MLX GPU mutant classification & local training.

Authors: Sourabh & Shreshth
"""

import pytest

from testforge.classifier import MutantTriageModel, extract_features
from testforge.mutator import ASTMutator

SAMPLE_CODE = """
def process(a, b):
    if a > 0:
        return a + b
    return False
"""

def test_feature_extraction():
    mutants = ASTMutator.generate_mutants(SAMPLE_CODE)
    assert len(mutants) > 0
    feat = extract_features(mutants[0])
    assert len(feat) == 8
    assert all(isinstance(x, float) for x in feat)

def test_mlx_training_and_inference():
    mutants = ASTMutator.generate_mutants(SAMPLE_CODE)
    triage = MutantTriageModel()

    # Synthetic training set of (features, label: 0=killed, 1=survived)
    dataset = [
        (extract_features(m), 1 if m.mutation_type in ("COMP_OP", "ARITH_OP") else 0)
        for m in mutants
    ]

    loss = triage.train_on_history(dataset, epochs=10)
    assert isinstance(loss, float)
    assert loss >= 0.0

    predictions = triage.predict_difficulty(mutants)
    assert len(predictions) == len(mutants)
    assert all(p in ("HIGH_PRIORITY_HARD", "STANDARD") for p in predictions)
