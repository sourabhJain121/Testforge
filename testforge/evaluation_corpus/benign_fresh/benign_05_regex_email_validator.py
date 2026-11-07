import re

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

def is_valid_email(address: str) -> bool:
    if not address or len(address) > 254:
        return False
    return bool(EMAIL_REGEX.match(address.strip()))
