from typing import Union

def add_numbers(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """
    Adds two numbers and returns the result.
    
    Parameters:
    a (int, float): The first number.
    b (int, float): The second number.
    
    Returns:
    int, float: The sum of the two numbers.
    
    Raises:
    TypeError: If either of the inputs is not an integer or float.
    """
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both inputs must be integers or floats.")
    
    return a + b