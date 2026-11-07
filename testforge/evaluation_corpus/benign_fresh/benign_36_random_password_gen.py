import string
import secrets

def generate_complex_passphrase(length: int = 16) -> str:
    chars = string.ascii_letters + string.digits + '!@#$%^&*()'
    return ''.join(secrets.choice(chars) for _ in range(length))
