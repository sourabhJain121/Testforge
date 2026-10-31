def make_multiplier(factor: float):
    """Outer enclosing function."""
    def intermediate(offset: float):
        """Intermediate closure."""
        def inner(value: float) -> float:
            """Innermost function."""
            return (value + offset) * factor
        return inner
    return intermediate
