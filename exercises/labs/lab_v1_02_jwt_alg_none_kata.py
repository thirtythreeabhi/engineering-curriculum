"""
Lab V1-02 (Volume 1 Ch 6 - Auth & Security):
JWT `alg: none` & Key-Confusion Debugging Kata

Instructions:
This JWT verifier was generated with a classic security vulnerability:
1. It reads `encoded_header` only to ignore `alg` completely (allowing `alg: none`
   and `RS256` key-confusion tokens to bypass or trick verification).
2. It crashes with uncaught `binascii.Error` or `json.JSONDecodeError` on malformed inputs.

Your task:
- Implement the `TODO`s in `verify_jwt_hs256` to:
  1. Decode the header safely (catching base64/UTF-8/JSON errors).
  2. Enforce `header.get("alg") == "HS256"` and `header.get("typ") == "JWT"`.
  3. Decode the signature and payload safely and check `exp`.

Run this file directly to test your fix:
    python3 exercises/labs/lab_v1_02_jwt_alg_none_kata.py

Reference solution:
- exercises/volume1/ex05_jwt_timing_safe_verifier.py
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
    padding = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + padding)


def verify_jwt_hs256(token: str, secret_key: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    parts = token.split(".")
    if len(parts) != 3:
        return False, None, "Malformed JWT structure"

    encoded_header, encoded_payload, encoded_signature = parts

    # TODO 1: Safely base64url-decode and JSON-parse `encoded_header`.
    #         Return `(False, None, "Malformed JWT header")` on decode/JSON errors.
    # TODO 2: Validate `header.get("alg") == "HS256"` and `header.get("typ") == "JWT"`.
    #         Explicitly reject `alg: none` or `RS256` BEFORE trusting any signature!
    header = json.loads(b64url_decode(encoded_header).decode("utf-8"))
    if header.get("alg") == "none":
        # BUG: Accidentally trusts `alg: none` without verifying signature!
        payload = json.loads(b64url_decode(encoded_payload).decode("utf-8"))
        return True, payload, "Unsecured alg:none accepted (BUG!)"

    # TODO 3: Safely decode `encoded_signature` and `encoded_payload` without raising
    #         uncaught binascii.Error / ValueError / json.JSONDecodeError.
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    expected_sig = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    provided_sig = b64url_decode(encoded_signature)

    if not hmac.compare_digest(expected_sig, provided_sig):
        return False, None, "Invalid signature"

    payload = json.loads(b64url_decode(encoded_payload).decode("utf-8"))
    if time.time() > payload.get("exp", 0):
        return False, None, "Token expired"

    return True, payload, "Valid"


if __name__ == "__main__":
    print("==> Running Lab V1-02: JWT alg:none & Malformed Input Kata...")
    secret = "lab-secret-key-32-bytes-minimum!"

    # Construct valid HS256 token
    h_ok = b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    p_ok = b64url_encode(json.dumps({"sub": "alice", "exp": int(time.time()) + 120}).encode())
    s_ok = b64url_encode(hmac.new(secret.encode(), f"{h_ok}.{p_ok}".encode(), hashlib.sha256).digest())
    ok, data, _ = verify_jwt_hs256(f"{h_ok}.{p_ok}.{s_ok}", secret)
    assert ok is True and data is not None and data["sub"] == "alice"

    # Attack 1: alg=none unsigned token MUST be rejected
    h_none = b64url_encode(json.dumps({"alg": "none", "typ": "JWT"}).encode())
    ok, _, msg = verify_jwt_hs256(f"{h_none}.{p_ok}.", secret)
    assert ok is False, f"[FAIL] alg:none token was accepted! ({msg})"

    # Attack 2: RS256 signed with public/shared string MUST be rejected
    h_rs = b64url_encode(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    s_rs = b64url_encode(hmac.new(secret.encode(), f"{h_rs}.{p_ok}".encode(), hashlib.sha256).digest())
    ok, _, msg = verify_jwt_hs256(f"{h_rs}.{p_ok}.{s_rs}", secret)
    assert ok is False, f"[FAIL] RS256 token was accepted by HS256 verifier! ({msg})"

    # Attack 3: Malformed base64 / invalid JSON MUST return False cleanly, never raise
    try:
        ok, _, _ = verify_jwt_hs256("!!!bad_b64!!!.e30.AAAA", secret)
        assert ok is False
    except Exception as exc:
        raise AssertionError(f"[FAIL] Unhandled exception on malformed base64: {exc!r}")

    print("[PASS] Lab V1-02 completed!")
