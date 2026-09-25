"""
Auth router — Section 7.1 endpoints.

Endpoints:
  POST /auth/login
  POST /auth/refresh
  POST /auth/logout
  POST /auth/invite        (super_admin or ops_manager only)
  POST /auth/password-reset/request
  POST /auth/password-reset/confirm

Rate limiting on login and password-reset routes is applied via a
slowapi limiter attached in main.py.

Invite-only model: no public sign-up endpoint exists (Section 9.1).
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_admin, require_roles
from app.models.admin import AdminUser
from app.models.driver import Driver, DriverRole
from app.services.auth import (
    authenticate_admin,
    authenticate_driver,
    consume_invite_token,
    create_access_token,
    create_invite_token,
    create_refresh_token,
    hash_password,
    revoke_refresh_token,
    verify_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Request/Response schemas ──────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    expires_in: int


class LogoutRequest(BaseModel):
    refresh_token: str


class InviteRequest(BaseModel):
    email: EmailStr
    full_name: str
    role: str          # must match a DriverRole.code
    depot_id: str | None = None


class InviteResponse(BaseModel):
    invite_id: str
    status: str
    expires_at: str


class PasswordResetRequestBody(BaseModel):
    email: EmailStr


class PasswordResetConfirmBody(BaseModel):
    token: str
    new_password: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_login_response(
    db: Session,
    subject_id: str,
    subject_type: str,
    role: str,
    user_payload: dict,
) -> LoginResponse:
    settings = get_settings()
    access_token, _ = create_access_token(
        subject_id=subject_id,
        subject_type=subject_type,
        role=role,
    )
    driver_id = subject_id if subject_type == "driver" else None
    admin_id = subject_id if subject_type == "admin" else None
    refresh_raw = create_refresh_token(
        db,
        driver_id=driver_id,
        admin_user_id=admin_id,
    )
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_raw,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=user_payload,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Accepts driver or admin credentials. Tries driver first, then admin.
    Returns a generic 401 regardless of whether the email exists (prevents
    email enumeration).
    """
    _401 = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "invalid_credentials", "message": "Email or password is incorrect."},
    )

    driver = authenticate_driver(db, body.email, body.password)
    if driver:
        role_code = driver.role_ref.code if driver.role_ref else "unknown"
        return _build_login_response(
            db,
            subject_id=str(driver.id),
            subject_type="driver",
            role=role_code,
            user_payload={
                "id": str(driver.id),
                "type": "driver",
                "full_name": driver.full_name,
                "role": role_code,
            },
        )

    admin = authenticate_admin(db, body.email, body.password)
    if admin:
        return _build_login_response(
            db,
            subject_id=str(admin.id),
            subject_type="admin",
            role=admin.permission_role,
            user_payload={
                "id": str(admin.id),
                "type": "admin",
                "full_name": admin.full_name,
                "permission_role": admin.permission_role,
            },
        )

    raise _401


@router.post("/refresh", response_model=RefreshResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    """Exchanges a valid refresh token for a new access token (token rotation)."""
    token_row = verify_refresh_token(db, body.refresh_token)
    if not token_row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_refresh_token", "message": "Refresh token is invalid or expired."},
        )

    # Rotate: revoke old, issue new refresh token
    token_row.is_revoked = True

    settings = get_settings()
    if token_row.driver_id:
        driver = db.query(Driver).filter(Driver.id == token_row.driver_id).first()
        if not driver or driver.status == "inactive":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account inactive.")
        role_code = driver.role_ref.code if driver.role_ref else "unknown"
        access_token, _ = create_access_token(
            subject_id=str(driver.id), subject_type="driver", role=role_code
        )
        create_refresh_token(db, driver_id=str(driver.id))
    else:
        admin = db.query(AdminUser).filter(AdminUser.id == token_row.admin_user_id).first()
        if not admin:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not found.")
        access_token, _ = create_access_token(
            subject_id=str(admin.id), subject_type="admin", role=admin.permission_role
        )
        create_refresh_token(db, admin_user_id=str(admin.id))

    return RefreshResponse(
        access_token=access_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: LogoutRequest, db: Session = Depends(get_db)):
    """Revokes the provided refresh token. Idempotent — always 204."""
    revoke_refresh_token(db, body.refresh_token)


@router.post("/invite", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
def invite(
    body: InviteRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(require_roles("super_admin", "ops_manager")),
):
    """
    Creates an invite token for a new driver. Invite-only (Section 9.1).
    No public sign-up endpoint exists.
    """
    # Resolve role code to role_id
    role = db.query(DriverRole).filter(DriverRole.code == body.role).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_role", "message": f"Unknown driver role: {body.role}"},
        )

    raw_token = create_invite_token(
        db,
        email=str(body.email),
        full_name=body.full_name,
        role_id=str(role.id),
        depot_id=body.depot_id,
        created_by=str(admin.id),
    )

    # Calculate expiry for response (7 days default)
    expires_at = (
        datetime.now(UTC) + timedelta(days=7)
    ).isoformat()

    # TODO Phase 1: send invite email with token link instead of returning raw token.
    # For now, return it directly so the flow can be tested end-to-end.
    return InviteResponse(
        invite_id=raw_token,   # raw token is the invite_id for now
        status="pending",
        expires_at=expires_at,
    )


@router.post("/password-reset/request", status_code=status.HTTP_204_NO_CONTENT)
def password_reset_request(body: PasswordResetRequestBody, db: Session = Depends(get_db)):
    """
    Always returns 204 regardless of whether the email exists (prevents
    email enumeration). Email dispatch is a Phase 1 stub.
    """
    # TODO Phase 1: look up driver/admin by email, generate reset token, send email.
    pass


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
def password_reset_confirm(body: PasswordResetConfirmBody, db: Session = Depends(get_db)):
    """Validates reset token and sets new password. Phase 1 stub."""
    # TODO Phase 1: validate reset token, hash and save new password, invalidate token.
    pass
