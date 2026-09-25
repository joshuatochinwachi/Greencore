"""
Unit tests for the Auth Service — Section 9.1 and Section 14.1.
"""

import pytest
from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    create_refresh_token,
    verify_refresh_token_string,
    hash_token,
)


def test_password_hashing():
    plain = "SecurePassword123!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_access_token_creation_and_decoding():
    token = create_access_token(
        subject_id="00000000-0000-0000-0000-000000000001",
        user_type="driver",
        role="class1",
        email="driver@example.com",
    )
    assert isinstance(token, str)
    payload = decode_access_token(token)
    assert payload["sub"] == "00000000-0000-0000-0000-000000000001"
    assert payload["type"] == "driver"
    assert payload["role"] == "class1"
    assert payload["email"] == "driver@example.com"


def test_refresh_token_generation_and_hashing():
    raw_token = create_refresh_token()
    assert len(raw_token) >= 32
    assert verify_refresh_token_string(raw_token) is True
    assert verify_refresh_token_string("short") is False

    hashed = hash_token(raw_token)
    assert hashed != raw_token
    assert len(hashed) == 64  # SHA-256 hex digest
