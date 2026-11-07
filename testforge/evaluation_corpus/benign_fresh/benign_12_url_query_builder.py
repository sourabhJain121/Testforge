import urllib.parse
from typing import Dict, Any

def construct_api_url(base_url: str, params: Dict[str, Any]) -> str:
    query = urllib.parse.urlencode(params)
    return f'{base_url}?{query}' if query else base_url
