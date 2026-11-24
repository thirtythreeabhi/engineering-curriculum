"""
Exercise 1.5: Timing-Safe JWT Creation and Constant-Time Verification

Problem:
Standard string comparison (==) terminates early on the first non-matching byte,
introducing a timing side-channel that allows attackers to iteratively forge valid
signatures.

Implement a timing-safe JWT verifier from scratch that:
1. Encodes header, payload, and HMAC-SHA256 signature using base64url.
2. Verifies the signature using hmac.compare_digest() for constant-time comparison.
3. Enforces token expiration (exp) and rejects tampered or expired tokens.
"""

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional, Tuple


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def b64url_decode(s: str) -> bytes:
    padding = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + padding)


def create_token(payload: Dict[str, Any], secret_key: str, expires_in_sec: int = 3600) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    body = payload.copy()
    body["exp"] = int(time.time()) + expires_in_sec

    encoded_header = b64url_encode(json.dumps(header).encode("utf-8"))
    encoded_payload = b64url_encode(json.dumps(body).encode("utf-8"))

    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    encoded_signature = b64url_encode(signature)

    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"


def verify_token(token: str, secret_key: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    parts = token.split(".")
    if len(parts) != 3:
        return False, None, "Malformed JWT structure"

    encoded_header, encoded_payload, encoded_signature = parts
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    expected_signature = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()

    provided_signature = b64url_decode(encoded_signature)

    # Constant-time comparison: prevents timing attacks
    if not hmac.compare_digest(expected_signature, provided_signature):
        return False, None, "Invalid cryptographic signature"

    payload = json.loads(b64url_decode(encoded_payload).decode("utf-8"))
    if time.time() > payload.get("exp", 0):
        return False, None, "Token has expired"

    return True, payload, "Valid"


if __name__ == "__main__":
    print("==> Running Exercise 1.5: Timing-Safe JWT Verification...")
    secret = "my-high-entropy-production-secret-32b"

    # Test 1: Valid token
    token = create_token({"sub": "user_123", "role": "admin"}, secret, expires_in_sec=60)
    valid, payload, msg = verify_token(token, secret)
    assert valid is True
    assert payload["sub"] == "user_123"

    # Test 2: Forged token signature
    tampered = token[:-4] + "AAAA"
    valid, _, msg = verify_token(tampered, secret)
    assert valid is False
    assert "Invalid cryptographic signature" in msg

    # Test 3: Expired token
    expired_token = create_token({"sub": "user_123"}, secret, expires_in_sec=-10)
    valid, _, msg = verify_token(expired_token, secret)
    assert valid is False
    assert "Token has expired" in msg

    print("[PASS] Exercise 1.5 verified.")
