"""
Auth service — password hashing, JWT issuance, token verification.

Security choices (Section 9.1):
- Passwords: argon2 via passlib (more memory-hard than bcrypt; spec says
  "bcrypt/argon2" — argon2 is the stronger default choice).
- JWT access tokens: short-lived (15 min, configurable).
- Refresh tokens: long-lived (30 days), stored as a hash in the DB so
  they can be revoked server-side at any time (e.g. driver deactivation).
- Rate limiting on /auth/login and /auth/password-reset/* is implemented
  at the router layer (slowapi), not here.
"""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.auth import InviteToken, RefreshToken
from app.models.driver import Driver, DriverRole
from app.models.admin import AdminUser

# ── Password hashing ──────────────────────────────────────────────────────────
# argon2 is the primary scheme; bcrypt kept as deprecated fallback so old
# bcrypt hashes can still be verified and transparently re-hashed on login.
_pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
)


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def password_needs_rehash(hashed: str) -> bool:
    """Returns True if the hash was created with a deprecated scheme (e.g. bcrypt)."""
    return _pwd_context.needs_update(hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────
_ALGORITHM = "HS256"


def _now_utc() -> datetime:
    return datetime.now(UTC)


def create_access_token(
    subject_id: str,
    subject_type: Literal["driver", "admin"],
    role: str,
    permission_role: str | None = None,
) -> tuple[str, datetime]:
    """
    Returns (encoded_jwt, expires_at).

    Payload:
      sub  — subject UUID
      typ  — "driver" or "admin"
      role — driver licence role or admin permission_role
    """
    settings = get_settings()
    expires_at = _now_utc() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": str(subject_id),
        "typ": subject_type,
        "role": role,
        "exp": expires_at,
        "iat": _now_utc(),
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=_ALGORITHM)
    return token, expires_at


def decode_access_token(token: str) -> dict:
    """
    Raises JWTError on invalid/expired tokens.
    Callers should catch JWTError and return 401.
    """
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[_ALGORITHM])


# ── Refresh tokens ────────────────────────────────────────────────────────────

def _hash_token(raw: str) -> str:
    """SHA-256 of the raw token — stored in the DB, never the raw value."""
    return hashlib.sha256(raw.encode()).hexdigest()


def create_refresh_token(
    db: Session,
    *,
    driver_id: str | None = None,
    admin_user_id: str | None = None,
) -> str:
    """
    Generates a cryptographically random refresh token, stores its hash,
    and returns the raw token (returned once, never stored).
    """
    assert bool(driver_id) ^ bool(admin_user_id), (
        "Exactly one of driver_id or admin_user_id must be set."
    )
    settings = get_settings()
    raw = secrets.token_urlsafe(48)
    expires_at = _now_utc() + timedelta(days=settings.jwt_refresh_token_expire_days)
    db.add(RefreshToken(
        token_hash=_hash_token(raw),
        driver_id=uuid.UUID(driver_id) if driver_id else None,
        admin_user_id=uuid.UUID(admin_user_id) if admin_user_id else None,
        expires_at=expires_at,
    ))
    # Caller must commit.
    return raw


def verify_refresh_token(db: Session, raw: str) -> RefreshToken | None:
    """
    Returns the RefreshToken row if valid and unexpired, None otherwise.
    Does NOT revoke — caller decides whether to rotate or reject.
    """
    token = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == _hash_token(raw),
            RefreshToken.is_revoked.is_(False),
            RefreshToken.expires_at > _now_utc(),
        )
        .first()
    )
    return token


def revoke_refresh_token(db: Session, raw: str) -> None:
    token = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == _hash_token(raw))
        .first()
    )
    if token:
        token.is_revoked = True


def revoke_all_driver_tokens(db: Session, driver_id: str) -> int:
    """
    Revokes all active refresh tokens for a driver.
    Called by POST /drivers/{id}/deactivate (Section 14.2).
    Returns the number of tokens revoked.
    """
    result = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.driver_id == uuid.UUID(driver_id),
            RefreshToken.is_revoked.is_(False),
        )
        .all()
    )
    for token in result:
        token.is_revoked = True
    return len(result)


# ── Invite tokens ─────────────────────────────────────────────────────────────

def create_invite_token(
    db: Session,
    *,
    email: str,
    full_name: str,
    role_id: str,
    depot_id: str | None,
    created_by: str,
    expires_in_days: int = 7,
) -> str:
    """
    Creates an invite token. Returns raw token (one-time, not stored).
    """
    raw = secrets.token_urlsafe(32)
    expires_at = _now_utc() + timedelta(days=expires_in_days)
    db.add(InviteToken(
        token_hash=_hash_token(raw),
        email=email,
        full_name=full_name,
        role_id=uuid.UUID(role_id),
        depot_id=uuid.UUID(depot_id) if depot_id else None,
        created_by=uuid.UUID(created_by),
        expires_at=expires_at,
    ))
    return raw


def consume_invite_token(db: Session, raw: str) -> InviteToken | None:
    """
    Returns and marks-used a valid, unused, unexpired invite token.
    Returns None if not found, already used, or expired.
    """
    token = (
        db.query(InviteToken)
        .filter(
            InviteToken.token_hash == _hash_token(raw),
            InviteToken.is_used.is_(False),
            InviteToken.expires_at > _now_utc(),
        )
        .first()
    )
    if token:
        token.is_used = True
    return token


# ── Login helpers ─────────────────────────────────────────────────────────────

def authenticate_driver(db: Session, email: str, password: str) -> Driver | None:
    """Returns Driver if credentials are valid, None otherwise."""
    driver = db.query(Driver).filter(Driver.email == email).first()
    if not driver or not verify_password(password, driver.password_hash):
        return None
    # Transparently re-hash if using a deprecated scheme (e.g. bcrypt → argon2)
    if password_needs_rehash(driver.password_hash):
        driver.password_hash = hash_password(password)
    return driver


def authenticate_admin(db: Session, email: str, password: str) -> AdminUser | None:
    """Returns AdminUser if credentials are valid, None otherwise."""
    admin = db.query(AdminUser).filter(AdminUser.email == email).first()
    if not admin or not verify_password(password, admin.password_hash):
        return None
    if password_needs_rehash(admin.password_hash):
        admin.password_hash = hash_password(password)
    return admin
