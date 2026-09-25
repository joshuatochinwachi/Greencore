"""
Auth-specific models — refresh tokens and invite tokens.

RefreshToken:
- Long-lived but revocable server-side (Section 9.1).
- Revoked on driver deactivation (Section 14.2 /drivers/{id}/deactivate).
- Works for both Driver and AdminUser — linked via nullable FKs.

InviteToken:
- Created by POST /auth/invite (admin-only, Section 7.1).
- One-time use; driver sets their password on first login.
- Expires after a configurable period (default 7 days).
"""

import uuid

from sqlalchemy import Boolean, Column, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import TIMESTAMP

from app.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    # Either driver_id OR admin_user_id is set, not both.
    driver_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    admin_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("admin_users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    is_revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)

    driver = relationship("Driver", back_populates="refresh_tokens")
    admin_user = relationship("AdminUser", back_populates="refresh_tokens")


class InviteToken(Base):
    """
    One-time driver invite token. Invite-only account creation per Section 9.1:
    "no public sign-up endpoint exists at all."
    """

    __tablename__ = "invite_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("driver_roles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    depot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("depots.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_used = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
