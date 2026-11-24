"""
Exercise 1.5: Timing-Safe JWT Creation and Constant-Time Verification

Problem:
Standard string comparison (==) terminates early on the first non-matching byte,
introducing a timing side-channel that allows attackers to iteratively forge valid
signatures. In addition, failing to validate the JWT header's `alg` field exposes
applications to `alg: none` signature-stripping and RS256->HS256 key-confusion attacks.

Implement a timing-safe JWT verifier from scratch that:
1. Encodes header, payload, and HMAC-SHA256 signature using base64url.
2. Validates header `typ == "JWT"` and strictly enforces `alg == "HS256"` (rejecting `alg: none` and `RS256`).
3. Handles malformed base64 and invalid JSON cleanly without unhandled exceptions.
4. Verifies the signature using hmac.compare_digest() for constant-time comparison.
5. Enforces token expiration (exp) and rejects tampered or expired tokens.
"""

import base64
import binascii
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional, Tuple


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def b64url_decode(s: str) -> bytes:
    if not isinstance(s, str) or not s:
        raise ValueError("Empty base64url segment")
    padding = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + padding)


def create_token(payload: Dict[str, Any], secret_key: str, expires_in_sec: int = 3600) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    body = payload.copy()
    body["exp"] = int(time.time()) + expires_in_sec

    encoded_header = b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = b64url_encode(json.dumps(body, separators=(",", ":")).encode("utf-8"))

    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    encoded_signature = b64url_encode(signature)

    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"


def verify_token(token: str, secret_key: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    if not isinstance(token, str):
        return False, None, "Malformed JWT structure"

    parts = token.split(".")
    if len(parts) != 3:
        return False, None, "Malformed JWT structure"

    encoded_header, encoded_payload, encoded_signature = parts

    # 1. Decode and strictly validate JWT header BEFORE trusting signature scheme
    try:
        header_bytes = b64url_decode(encoded_header)
        header = json.loads(header_bytes.decode("utf-8"))
    except (binascii.Error, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return False, None, "Malformed JWT header"

    if not isinstance(header, dict):
        return False, None, "Malformed JWT header"

    alg = header.get("alg")
    typ = header.get("typ")
    if not isinstance(alg, str) or alg != "HS256":
        return False, None, f"Unsupported or rejected JWT algorithm: {alg!r}"
    if typ != "JWT":
        return False, None, f"Invalid JWT type: {typ!r}"

    # 2. Decode signature and perform constant-time HMAC-SHA256 verification
    try:
        provided_signature = b64url_decode(encoded_signature)
    except (binascii.Error, ValueError):
        return False, None, "Malformed JWT signature encoding"

    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    expected_signature = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()

    if not hmac.compare_digest(expected_signature, provided_signature):
        return False, None, "Invalid cryptographic signature"

    # 3. Decode payload and enforce numeric expiration claim
    try:
        payload_bytes = b64url_decode(encoded_payload)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (binascii.Error, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return False, None, "Malformed JWT payload"

    if not isinstance(payload, dict):
        return False, None, "Malformed JWT payload"

    exp = payload.get("exp")
    if isinstance(exp, bool) or not isinstance(exp, (int, float)):
        return False, None, "Missing or invalid exp claim"
    if time.time() > exp:
        return False, None, "Token has expired"

    return True, payload, "Valid"


if __name__ == "__main__":
    print("==> Running Exercise 1.5: Timing-Safe JWT Verification...")
    secret = "my-high-entropy-production-secret-32b"

    # Test 1: Valid token
    token = create_token({"sub": "user_123", "role": "admin"}, secret, expires_in_sec=60)
    valid, payload, msg = verify_token(token, secret)
    assert valid is True
    assert payload is not None and payload["sub"] == "user_123"

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

    # Test 4: Reject alg: none signature-stripping attack (even if signed with secret or empty sig)
    none_header = b64url_encode(json.dumps({"alg": "none", "typ": "JWT"}).encode("utf-8"))
    future_payload = b64url_encode(json.dumps({"sub": "admin", "exp": int(time.time()) + 300}).encode("utf-8"))
    none_sig_input = f"{none_header}.{future_payload}".encode("utf-8")
    none_forged_sig = b64url_encode(hmac.new(secret.encode("utf-8"), none_sig_input, hashlib.sha256).digest())
    valid, _, msg = verify_token(f"{none_header}.{future_payload}.{none_forged_sig}", secret)
    assert valid is False and "Unsupported or rejected JWT algorithm" in msg

    valid, _, msg = verify_token(f"{none_header}.{future_payload}.", secret)
    assert valid is False

    # Test 5: Reject RS256 key-confusion token
    rs_header = b64url_encode(json.dumps({"alg": "RS256", "typ": "JWT"}).encode("utf-8"))
    rs_sig_input = f"{rs_header}.{future_payload}".encode("utf-8")
    rs_confused_sig = b64url_encode(hmac.new(secret.encode("utf-8"), rs_sig_input, hashlib.sha256).digest())
    valid, _, msg = verify_token(f"{rs_header}.{future_payload}.{rs_confused_sig}", secret)
    assert valid is False and "RS256" in msg

    # Test 6: Malformed base64 and invalid JSON handled cleanly
    valid, _, msg = verify_token("!!!invalid_b64!!!.e30.AAAA", secret)
    assert valid is False and "Malformed JWT header" in msg

    bad_json_header = b64url_encode(b"{not-valid-json")
    valid, _, msg = verify_token(f"{bad_json_header}.{future_payload}.AAAA", secret)
    assert valid is False and "Malformed JWT header" in msg

    bad_json_payload = b64url_encode(b"{not-valid-json")
    good_header = b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode("utf-8"))
    bad_sig_input = f"{good_header}.{bad_json_payload}".encode("utf-8")
    bad_sig = b64url_encode(hmac.new(secret.encode("utf-8"), bad_sig_input, hashlib.sha256).digest())
    valid, _, msg = verify_token(f"{good_header}.{bad_json_payload}.{bad_sig}", secret)
    assert valid is False and "Malformed JWT payload" in msg

    print("[PASS] Exercise 1.5 verified.")
