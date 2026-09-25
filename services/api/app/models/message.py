"""
ChatMessage and Announcement models — Section 8.

Chat scope visibility (route / depot / global) is resolved server-side at
send time from current shift/allocation data per Section 15.11 — it is NOT
a stored group membership. The scope field on each message records what scope
was applied, but the server re-derives membership on every message to prevent
stale group data from leaking drop-level detail (Section 9.4).
"""

import uuid

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import TIMESTAMP

from app.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_driver_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content = Column(Text, nullable=False)
    photo_url = Column(Text, nullable=True)
    scope = Column(
        Enum("route", "depot", "global", name="chat_scope_enum"),
        nullable=False,
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    reported = Column(Boolean, nullable=False, default=False)

    sender_driver = relationship("Driver", back_populates="chat_messages")


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sent_by = Column(
        UUID(as_uuid=True),
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    content = Column(Text, nullable=False)
    target_type = Column(
        Enum(
            "all", "driver", "route", "depot", "vehicle_category",
            name="announcement_target_enum",
        ),
        nullable=False,
    )
    # target_ids: list of UUIDs (driver ids, route ids, etc.) or empty for "all"
    target_ids = Column(JSONB, nullable=True, default=list)
    sent_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    sender = relationship("AdminUser", back_populates="announcements")
