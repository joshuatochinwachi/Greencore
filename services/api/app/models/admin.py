"""
AdminUser and AuditLogEntry models — Section 8.

Key points from Section 9.5:
- AuditLogEntry is READ-ONLY. No admin role, including super_admin, can
  delete audit entries. Enforced by: no DELETE endpoint in the API for this
  table, and the DB user used by the app should have INSERT/SELECT only on
  audit_log_entries (recommend a separate DB role).
- Every admin write to driver/route/hours data must produce exactly one
  AuditLogEntry. This is implemented via a single reusable service function
  (app/services/audit.py), not repeated per-endpoint.
"""

import uuid

from sqlalchemy import Column, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import TIMESTAMP

from app.database import Base


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    permission_role = Column(
        Enum(
            "super_admin", "ops_manager", "route_manager", "payroll_hr", "read_only",
            name="admin_role_enum",
        ),
        nullable=False,
        default="read_only",
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    audit_log_entries = relationship("AuditLogEntry", back_populates="admin_user")
    announcements = relationship("Announcement", back_populates="sender")
    refresh_tokens = relationship("RefreshToken", back_populates="admin_user")

    def __repr__(self) -> str:
        return f"<AdminUser {self.email} ({self.permission_role})>"


class AuditLogEntry(Base):
    """
    Immutable audit trail. See Section 9.5.

    before_value / after_value contain ONLY the changed fields, not the full
    entity. See Section 17.4 acceptance criteria: "recording the before and
    after state of the changed fields only, not the entire route object."
    """

    __tablename__ = "audit_log_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    entity_type = Column(String(100), nullable=False)  # e.g. "driver", "route", "shift"
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    before_value = Column(JSONB, nullable=True)
    after_value = Column(JSONB, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    admin_user = relationship("AdminUser", back_populates="audit_log_entries")
