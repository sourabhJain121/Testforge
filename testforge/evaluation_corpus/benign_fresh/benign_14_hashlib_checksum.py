import hashlib

def compute_sha256_hash(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()
