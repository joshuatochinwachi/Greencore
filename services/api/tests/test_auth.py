"""
Unit tests for the Auth Service — Section 9.1 and Section 14.1.
"""

import secrets
import pytest
from jose import JWTError
from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    hash_token,
)


def test_password_hashing():
    plain = "SecurePassword123!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_access_token_creation_and_decoding():
    token, expires_at = create_access_token(
        subject_id="00000000-0000-0000-0000-000000000001",
        subject_type="driver",
        role="class1",
    )
    assert isinstance(token, str)
    assert expires_at is not None

    payload = decode_access_token(token)
    assert payload["sub"] == "00000000-0000-0000-0000-000000000001"
    assert payload["typ"] == "driver"
    assert payload["role"] == "class1"
    assert "exp" in payload
    assert "iat" in payload
    assert "jti" in payload


def test_invalid_token_decoding():
    with pytest.raises(JWTError):
        decode_access_token("invalid.jwt.token")


def test_token_hashing():
    raw_token = secrets.token_urlsafe(32)
    assert len(raw_token) >= 32

    hashed = hash_token(raw_token)
    assert hashed != raw_token
    assert len(hashed) == 64  # SHA-256 hex digest
    assert hash_token(raw_token) == hashed  # Deterministic hash
