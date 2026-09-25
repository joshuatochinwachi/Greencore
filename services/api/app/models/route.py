"""
Route, Depot, Drop, Allocation, and Shift models — Section 8.

PostGIS geography columns use GeoAlchemy2's Geography type.
Specifying srid=4326, geometry_type='POINT' matches the spec's
geography(Point, 4326) declaration.
"""

import uuid

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
    Interval,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import TIMESTAMP

from app.database import Base


class Depot(Base):
    """
    Depot — required for driver.depot_id FK.
    Not in the Section 8 ER diagram as a named entity but implicitly required
    by multiple FK references (driver.depot_id, route.depot_id).
    Kept minimal for Phase 0; expanded if Q4 (multi-depot) is answered positively.
    """

    __tablename__ = "depots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)

    drivers = relationship("Driver", back_populates="depot")
    routes = relationship("Route", back_populates="depot")


class Route(Base):
    __tablename__ = "routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_name = Column(String(255), nullable=False)  # e.g. "LONDON 01"
    depot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("depots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # PostGIS geography columns — Section 8.1
    start_point = Column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )
    end_point = Column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )
    status = Column(
        Enum("active", "inactive", name="route_status_enum"),
        nullable=False,
        default="active",
    )
    # Nullable capacity limit — powers route_capacity_exceeded conflict check (Section 8.1)
    max_drops = Column(Integer, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    depot = relationship("Depot", back_populates="routes")
    drops = relationship("Drop", back_populates="route", order_by="Drop.sequence")
    allocations = relationship("Allocation", back_populates="route")


class Drop(Base):
    __tablename__ = "drops"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(
        UUID(as_uuid=True),
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence = Column(Integer, nullable=False)
    account_number = Column(String(100), nullable=True)
    customer_name = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    postcode = Column(String(10), nullable=True)
    # PostGIS geography column (Section 8.1)
    location = Column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )
    delivery_instructions = Column(Text, nullable=True)
    access_instructions = Column(Text, nullable=True)
    tray_instructions = Column(Text, nullable=True)
    opening_hours = Column(JSONB, nullable=True)
    contact_phone = Column(String(30), nullable=True)
    # Sequencing constraints (Section 8.1)
    fixed_position = Column(Boolean, nullable=False, default=False)
    must_precede_drop_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drops.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Vehicle class eligibility — powers vehicle_class_mismatch check (Section 8.1)
    required_vehicle_class = Column(
        Enum(
            "van", "7_5t", "class1_hgv", "class2_hgv",
            name="drop_vehicle_class_enum",
        ),
        nullable=True,
    )
    status = Column(
        Enum(
            "not_started", "en_route", "arrived", "delivered",
            "partial", "failed", "closed", "no_access", "other",
            name="drop_status_enum",
        ),
        nullable=False,
        default="not_started",
    )

    route = relationship("Route", back_populates="drops")
    must_precede = relationship("Drop", remote_side="Drop.id", foreign_keys=[must_precede_drop_id])
    deliveries = relationship("Delivery", back_populates="drop")


class Allocation(Base):
    __tablename__ = "allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shift_date = Column(String(10), nullable=False, index=True)   # YYYY-MM-DD
    driver_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    route_id = Column(
        UUID(as_uuid=True),
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vehicle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )
    planned_start = Column(Time, nullable=True)
    status = Column(
        Enum("draft", "confirmed", "notified", name="allocation_status_enum"),
        nullable=False,
        default="draft",
    )
    confirmed_at = Column(TIMESTAMP(timezone=True), nullable=True)

    driver = relationship("Driver", back_populates="allocations")
    route = relationship("Route", back_populates="allocations")
    vehicle = relationship("Vehicle", back_populates="allocations")
    shifts = relationship("Shift", back_populates="allocation")


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    allocation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("allocations.id", ondelete="SET NULL"),
        nullable=True,
    )
    start_time = Column(TIMESTAMP(timezone=True), nullable=False)
    end_time = Column(TIMESTAMP(timezone=True), nullable=True)
    # breaks: array of {start: ISO8601, end: ISO8601} pairs
    breaks = Column(JSONB, nullable=True, default=list)
    total_working_time = Column(Interval, nullable=True)
    amended = Column(Boolean, nullable=False, default=False)
    amendment_reason = Column(Text, nullable=True)
    amended_by = Column(
        UUID(as_uuid=True),
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    driver = relationship("Driver", back_populates="shifts")
    allocation = relationship("Allocation", back_populates="shifts")
    location_pings = relationship("LocationPing", back_populates="shift")
    deliveries = relationship("Delivery", back_populates="shift")
    amender = relationship("AdminUser", foreign_keys=[amended_by])
