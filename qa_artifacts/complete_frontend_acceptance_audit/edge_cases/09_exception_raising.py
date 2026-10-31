class CustomDomainError(Exception):
    pass

def validate_user_age(age: int) -> bool:
    if not isinstance(age, int):
        raise TypeError("Age must be an integer")
    if age < 0:
        raise ValueError("Age cannot be negative")
    if age > 150:
        raise CustomDomainError("Age exceeds biological plausibility limit")
    return age >= 18
