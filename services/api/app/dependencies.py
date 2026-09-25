"""
Shared FastAPI dependencies.

get_db       — yields a DB session per request
get_current_driver  — validates Bearer JWT, returns Driver
get_current_admin   — validates Bearer JWT, returns AdminUser
require_admin_roles — factory for role-gated admin endpoints

Section 9.1: "All admin endpoints re-verify permission_role server-side
against current DB state on every request — never trust a cached/client-
supplied role."
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.admin import AdminUser
from app.models.driver import Driver
from app.services.auth import decode_access_token

_bearer = HTTPBearer()


# ── Token extraction ──────────────────────────────────────────────────────────

def _extract_token(credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)]) -> dict:
    try:
        return decode_access_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Driver dependency ─────────────────────────────────────────────────────────

def get_current_driver(
    payload: Annotated[dict, Depends(_extract_token)],
    db: Session = Depends(get_db),
) -> Driver:
    if payload.get("typ") != "driver":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Driver token required.")
    driver = db.query(Driver).filter(Driver.id == payload["sub"]).first()
    if not driver or driver.status == "inactive":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Driver not found or inactive.")
    return driver


# ── Admin dependency ──────────────────────────────────────────────────────────

def get_current_admin(
    payload: Annotated[dict, Depends(_extract_token)],
    db: Session = Depends(get_db),
) -> AdminUser:
    if payload.get("typ") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin token required.")
    # Re-verify role from DB on every request (Section 9.1)
    admin = db.query(AdminUser).filter(AdminUser.id == payload["sub"]).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not found.")
    return admin


def require_roles(*roles: str):
    """
    Returns a dependency that raises 403 if the current admin's DB-verified
    permission_role is not in the allowed set.

    Usage:
        @router.get("/sensitive", dependencies=[Depends(require_roles("super_admin", "ops_manager"))])
    """
    def _check(admin: AdminUser = Depends(get_current_admin)) -> AdminUser:
        if admin.permission_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(roles)}.",
            )
        return admin
    return _check
