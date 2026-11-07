import cmath
from typing import Tuple

def solve_quadratic(a: float, b: float, c: float) -> Tuple[complex, complex]:
    if a == 0:
        raise ValueError('Coefficient a cannot be zero in a quadratic equation')
    d = (b ** 2) - (4 * a * c)
    sol1 = (-b - cmath.sqrt(d)) / (2 * a)
    sol2 = (-b + cmath.sqrt(d)) / (2 * a)
    return (sol1, sol2)
