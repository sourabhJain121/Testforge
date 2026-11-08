"""
samples/sealed_eval/url_router.py

Domain: Networking & HTTP Dispatch
URL query encoding/decoding and template-based route dispatcher.
"""

import urllib.parse
from typing import Dict, List, Any, Optional, Tuple


def encode_query_params(params: Dict[str, Any]) -> str:
    """Encodes a dictionary of query parameters into a sorted URL query string."""
    if not params:
        return ""

    items: List[Tuple[str, str]] = []
    for k in sorted(params.keys()):
        val = params[k]
        if isinstance(val, (list, tuple)):
            for item in sorted(val):
                items.append((str(k), str(item)))
        else:
            items.append((str(k), str(val)))

    return urllib.parse.urlencode(items)


def decode_query_params(query_string: str) -> Dict[str, List[str]]:
    """Decodes a URL query string into a dictionary of string lists."""
    if not query_string:
        return {}

    clean_qs = query_string.lstrip("?")
    parsed = urllib.parse.parse_qs(clean_qs, keep_blank_values=True)
    return {k: list(v) for k, v in parsed.items()}


class URLRouter:
    """Matches dynamic path templates like '/api/v1/{resource}/{id}' to handlers."""

    def __init__(self):
        self._routes: List[Tuple[List[str], str]] = []

    def add_route(self, template: str, handler_name: str) -> None:
        """Registers a route template mapping to handler_name."""
        clean = template.strip("/").split("/")
        self._routes.append((clean, handler_name))

    def match(self, path: str) -> Optional[Tuple[str, Dict[str, str]]]:
        """
        Matches request path against registered templates.
        Returns (handler_name, path_parameters) or None if no route matches.
        """
        segments = path.strip("/").split("/")

        for template_parts, handler in self._routes:
            if len(template_parts) != len(segments):
                continue

            params: Dict[str, str] = {}
            matched = True

            for t_part, s_part in zip(template_parts, segments):
                if t_part.startswith("{") and t_part.endswith("}"):
                    param_name = t_part[1:-1]
                    params[param_name] = s_part
                elif t_part != s_part:
                    matched = False
                    break

            if matched:
                return handler, params

        return None
