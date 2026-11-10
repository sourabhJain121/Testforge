"""
samples/jwt_validator.py - Production-grade JSON Web Token (JWT) Encoder & Validator.

Implements standard RFC 7519 HMAC-SHA256 JWT creation, decoding, expiration verification,
tampering defense, and claim boundary assertion in pure Python standard library.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, List, Optional


class JWTError(Exception):
    """Base exception for all JWT validation errors."""
    pass


class TokenExpiredError(JWTError):
    """Raised when a token's exp timestamp is in the past."""
    pass


class InvalidSignatureError(JWTError):
    """Raised when the HMAC signature does not match."""
    pass


class MalformedTokenError(JWTError):
    """Raised when the token format is syntactically invalid."""
    pass


class InvalidHeaderError(JWTError):
    """Raised when the token header is unsupported or tampered."""
    pass


def _base64url_encode(data: bytes) -> str:
    """Encodes bytes to base64url string without trailing padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(data_str: str) -> bytes:
    """Decodes base64url string with restored padding."""
    rem = len(data_str) % 4
    if rem > 0:
        data_str += "=" * (4 - rem)
    return base64.urlsafe_b64decode(data_str.encode("ascii"))


def encode_jwt(
    payload: Dict[str, Any],
    secret: str,
    algorithm: str = "HS256",
    headers: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Encodes a payload dictionary into a signed JWT string.
    """
    if algorithm != "HS256":
        raise ValueError(f"Unsupported algorithm: {algorithm}. Only HS256 is supported.")
    if not secret:
        raise ValueError("Secret key cannot be empty.")

    header_dict = {"alg": algorithm, "typ": "JWT"}
    if headers:
        header_dict.update(headers)

    header_json = json.dumps(header_dict, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

    b64_header = _base64url_encode(header_json)
    b64_payload = _base64url_encode(payload_json)

    signing_input = f"{b64_header}.{b64_payload}".encode("ascii")
    sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    b64_signature = _base64url_encode(sig)

    return f"{b64_header}.{b64_payload}.{b64_signature}"


def decode_jwt(
    token: str,
    secret: str,
    verify_exp: bool = True,
    leeway: int = 0,
    current_time: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Decodes and validates a signed JWT string against secret and temporal claims.
    """
    if not token or not isinstance(token, str):
        raise MalformedTokenError("Token must be a non-empty string.")
    if not secret:
        raise ValueError("Secret key cannot be empty.")

    parts = token.strip().split(".")
    if len(parts) != 3:
        raise MalformedTokenError(f"Token must have exactly 3 dot-separated segments, got {len(parts)}.")

    b64_header, b64_payload, b64_signature = parts

    # 1. Decode & Verify Header
    try:
        header_bytes = _base64url_decode(b64_header)
        header = json.loads(header_bytes.decode("utf-8"))
    except Exception as e:
        raise MalformedTokenError(f"Invalid header segment: {e}") from e

    if not isinstance(header, dict):
        raise InvalidHeaderError("Header must be a JSON object.")
    if header.get("alg") != "HS256":
        raise InvalidHeaderError(f"Invalid algorithm: {header.get('alg')}")
    if header.get("typ") != "JWT":
        raise InvalidHeaderError(f"Invalid token type: {header.get('typ')}")

    # 2. Decode Payload
    try:
        payload_bytes = _base64url_decode(b64_payload)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as e:
        raise MalformedTokenError(f"Invalid payload segment: {e}") from e

    if not isinstance(payload, dict):
        raise MalformedTokenError("Payload must be a JSON object.")

    # 3. Verify Signature (Constant-Time HMAC)
    try:
        sig_bytes = _base64url_decode(b64_signature)
    except Exception as e:
        raise MalformedTokenError(f"Invalid signature segment: {e}") from e

    signing_input = f"{b64_header}.{b64_payload}".encode("ascii")
    expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()

    if not hmac.compare_digest(sig_bytes, expected_sig):
        raise InvalidSignatureError("Signature mismatch: token has been tampered with or secret is wrong.")

    # 4. Verify Expiration Claims
    now = current_time if current_time is not None else int(time.time())

    if verify_exp and "exp" in payload:
        exp_val = payload["exp"]
        if not isinstance(exp_val, (int, float)):
            raise MalformedTokenError("exp claim must be a number.")
        if exp_val + leeway < now:
            raise TokenExpiredError(f"Token expired at {exp_val} (current time {now}, leeway {leeway}).")

    if "nbf" in payload:
        nbf_val = payload["nbf"]
        if not isinstance(nbf_val, (int, float)):
            raise MalformedTokenError("nbf claim must be a number.")
        if nbf_val - leeway > now:
            raise JWTError(f"Token is not yet valid (nbf {nbf_val} > now {now}).")

    return payload


def is_token_expired(token: str, current_time: Optional[int] = None) -> bool:
    """
    Checks if a token's exp claim is expired without validating signature.
    """
    if not token or "." not in token:
        return True
    parts = token.split(".")
    if len(parts) < 2:
        return True
    try:
        payload_bytes = _base64url_decode(parts[1])
        payload = json.loads(payload_bytes.decode("utf-8"))
        if "exp" not in payload:
            return False
        now = current_time if current_time is not None else int(time.time())
        return float(payload["exp"]) < now
    except Exception:
        return True


def validate_token_claims(
    payload: Dict[str, Any],
    required_claims: Optional[List[str]] = None,
) -> bool:
    """
    Validates presence and non-emptiness of required claims.
    """
    if not isinstance(payload, dict):
        return False
    if not required_claims:
        return True
    for claim in required_claims:
        if claim not in payload:
            return False
        val = payload[claim]
        if val is None or val == "":
            return False
    return True
