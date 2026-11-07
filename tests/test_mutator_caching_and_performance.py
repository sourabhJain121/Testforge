"""
tests/test_mutator_caching_and_performance.py

Verifies AST mutant compilation caching, state isolation across model copies,
and execution performance.
"""

import time

import pytest

from testforge.mutator import ASTMutator

SAMPLE_CODE = """
def calculate_discount(price: float, is_vip: bool) -> float:
    if price > 100:
        if is_vip:
            return price * 0.8
        return price * 0.9
    return price
"""


class TestMutatorCachingAndPerformance:
    def setup_method(self):
        ASTMutator.clear_cache()

    def test_mutator_caching_and_cache_hit_consistency(self):
        """Verifies that calling mutate twice returns identical records and hits cache."""
        mutants_first = ASTMutator.mutate(SAMPLE_CODE)
        assert len(mutants_first) > 0

        # Cache should now have 1 entry
        assert len(ASTMutator._MUTANT_CACHE) == 1

        mutants_second = ASTMutator.mutate(SAMPLE_CODE)
        assert len(mutants_second) == len(mutants_first)
        for m1, m2 in zip(mutants_first, mutants_second):
            assert m1.mutant_id == m2.mutant_id
            assert m1.mutated_code_snippet == m2.mutated_code_snippet

    def test_cached_mutants_are_isolated_copies(self):
        """Modifying a returned MutantRecord must not contaminate the internal cache."""
        mutants = ASTMutator.mutate(SAMPLE_CODE)
        first_mutant = mutants[0]
        original_status = first_mutant.status
        first_mutant.status = "KILLED"

        # Subsequent fetch from cache must have original pristine status
        mutants_fresh = ASTMutator.mutate(SAMPLE_CODE)
        assert mutants_fresh[0].status == original_status
        assert mutants_fresh[0].status != "KILLED"

    def test_cache_keys_differentiate_target_lines(self):
        """Mutations on restricted lines should use distinct cache entries."""
        all_mutants = ASTMutator.mutate(SAMPLE_CODE)
        line_restricted = ASTMutator.mutate(SAMPLE_CODE, target_lines=[3])

        assert len(ASTMutator._MUTANT_CACHE) == 2
        assert len(line_restricted) <= len(all_mutants)

    def test_clear_cache_empties_registry(self):
        """Calling clear_cache empties the internal storage."""
        ASTMutator.mutate(SAMPLE_CODE)
        assert len(ASTMutator._MUTANT_CACHE) > 0
        ASTMutator.clear_cache()
        assert len(ASTMutator._MUTANT_CACHE) == 0

    def test_caching_speedup_is_significant(self):
        """Verifies that repeated cache retrieval is substantially faster than cold AST parsing."""
        ASTMutator.clear_cache()
        # Cold pass
        t0 = time.perf_counter()
        ASTMutator.mutate(SAMPLE_CODE)
        t_cold = time.perf_counter() - t0

        # Warm passes (10 iterations)
        t1 = time.perf_counter()
        for _ in range(10):
            ASTMutator.mutate(SAMPLE_CODE)
        t_warm_avg = (time.perf_counter() - t1) / 10.0

        # Cache hit should be faster than cold compilation pass
        assert t_warm_avg < t_cold

