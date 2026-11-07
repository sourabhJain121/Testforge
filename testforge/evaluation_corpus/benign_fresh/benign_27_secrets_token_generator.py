import secrets

def generate_secure_session_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)
