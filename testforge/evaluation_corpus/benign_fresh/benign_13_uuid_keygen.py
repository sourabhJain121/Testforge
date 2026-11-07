import uuid

def generate_request_correlation_id() -> str:
    return f'req_{uuid.uuid4().hex[:12]}'
