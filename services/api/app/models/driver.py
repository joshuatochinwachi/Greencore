"""
Driver model.

Section 8 schema. driver.role is a lookup-table relationship (not a native
PG enum) per Section 15.1: "Recommend a lookup table over a native DB enum
for this specific field, since the original spec explicitly says roles should
be expandable later."
"""

import uuid

from sqlalchemy import (
    Column,
    Enum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import TIMESTAMP

from app.database import Base


class DriverRole(Base):
    """
    Lookup table for driver licence/vehicle roles.
    Seeded with: van, 7_5t, class1, class2.
    New roles added here without any code change (Section 15.1).
    """

    __tablename__ = "driver_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False)   # e.g. "class1"
    label = Column(String(100), nullable=False)              # e.g. "Class 1 HGV"

    drivers = relationship("Driver", back_populates="role_ref")

    def __repr__(self) -> str:
        return f"<DriverRole {self.code}>"


class Driver(Base):
    """
    Core driver entity. Auth credentials live in RefreshToken / InviteToken
    (app/models/auth.py); the password hash is stored directly here alongside
    the profile, keeping the auth query surface minimal.
    """

    __tablename__ = "drivers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(30), nullable=True)
    photo_url = Column(Text, nullable=True)
    password_hash = Column(Text, nullable=False)

    # FK to driver_roles lookup table — not a PG enum (Section 15.1)
    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("driver_roles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    role_ref = relationship("DriverRole", back_populates="drivers")

    licence_number = Column(String(100), nullable=True)
    status = Column(
        Enum("active", "inactive", name="driver_status_enum"),
        nullable=False,
        default="active",
    )

    # depot_id is a FK to the depots table (created in route.py).
    # nullable for now — will be enforced once Q4 (single vs multi-depot) is resolved.
    depot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("depots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    depot = relationship("Depot", back_populates="drivers")
    vehicle_assignments = relationship(
        "DriverVehicleAssignment", back_populates="driver"
    )
    allocations = relationship("Allocation", back_populates="driver")
    shifts = relationship("Shift", back_populates="driver")
    deliveries = relationship("Delivery", back_populates="driver")
    chat_messages = relationship("ChatMessage", back_populates="sender_driver")
    incident_reports = relationship("IncidentReport", back_populates="driver")
    defect_reports = relationship("DefectReport", back_populates="driver")
    refresh_tokens = relationship("RefreshToken", back_populates="driver")

    def __repr__(self) -> str:
        return f"<Driver {self.email}>"
