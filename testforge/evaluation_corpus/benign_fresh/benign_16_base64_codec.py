import base64

def encode_base64(raw_text: str) -> str:
    raw_bytes = raw_text.encode('utf-8')
    return base64.b64encode(raw_bytes).decode('ascii')
