from typing import Union

def multiply_numbers(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """
    Multiplies two numbers and returns the result.
    
    Parameters:
    a (int, float): The first number to multiply.
    b (int, float): The second number to multiply.
    
    Returns:
    int, float: The product of the two numbers.
    
    Raises:
    TypeError: If either of the inputs is not an integer or float.
    ValueError: If either of the inputs is negative.
    """
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both inputs must be integers or floats.")
    if a < 0 or b < 0:
        raise ValueError("Both inputs must be non-negative.")
    return a * b