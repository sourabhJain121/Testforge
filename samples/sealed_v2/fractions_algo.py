"""Pure Python Rational arithmetic algorithms from CPython fractions.py"""
import math

class FractionAlgo:
    """Pure Python rational fraction class with exact arithmetic."""
    __slots__ = ('_numerator', '_denominator')

    def __init__(self, numerator: int = 0, denominator: int = 1):
        if denominator == 0:
            raise ZeroDivisionError('Fraction(%s, 0)' % numerator)
        g = math.gcd(numerator, denominator)
        if denominator < 0:
            g = -g
        self._numerator = int(numerator // g)
        self._denominator = int(denominator // g)

    @property
    def numerator(self) -> int:
        return self._numerator

    @property
    def denominator(self) -> int:
        return self._denominator

    def add(self, other: 'FractionAlgo') -> 'FractionAlgo':
        return FractionAlgo(self._numerator * other._denominator +
                            other._numerator * self._denominator,
                            self._denominator * other._denominator)

    def sub(self, other: 'FractionAlgo') -> 'FractionAlgo':
        return FractionAlgo(self._numerator * other._denominator -
                            other._numerator * self._denominator,
                            self._denominator * other._denominator)

    def mul(self, other: 'FractionAlgo') -> 'FractionAlgo':
        return FractionAlgo(self._numerator * other._numerator,
                            self._denominator * other._denominator)

    def div(self, other: 'FractionAlgo') -> 'FractionAlgo':
        if other._numerator == 0:
            raise ZeroDivisionError('division by zero')
        return FractionAlgo(self._numerator * other._denominator,
                            self._denominator * other._numerator)

    def is_positive(self) -> bool:
        return self._numerator > 0

    def is_integer(self) -> bool:
        return self._denominator == 1
