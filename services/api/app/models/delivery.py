"""
Delivery model — Section 8.

client_uuid is the on-device UUID generated at completion time (even offline)
used for deduplication on sync (Section 3.3, Section 14.6, Section 17.2).
"""

import uuid

from geoalchemy2 import Geography
from sqlalchemy import Column, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import TIMESTAMP

from app.database import Base


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drop_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shift_id = Column(
        UUID(as_uuid=True),
        ForeignKey("shifts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    driver_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(
        Enum(
            "not_started", "en_route", "arrived", "delivered",
            "partial", "failed", "closed", "no_access", "other",
            name="delivery_status_enum",
        ),
        nullable=False,
    )
    completed_at = Column(TIMESTAMP(timezone=True), nullable=False)
    completed_location = Column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )
    proof_photo_url = Column(Text, nullable=True)
    signature_url = Column(Text, nullable=True)
    failure_reason = Column(
        Enum(
            "shop_closed", "no_access", "loading_bay_unavailable",
            "road_closed", "customer_refused", "wrong_address",
            "vehicle_issue", "product_unavailable", "other",
            name="failure_reason_enum",
        ),
        nullable=True,
    )
    notes = Column(Text, nullable=True)
    # Client-generated UUID for offline deduplication (Section 3.3)
    client_uuid = Column(UUID(as_uuid=True), unique=True, nullable=True, index=True)

    drop = relationship("Drop", back_populates="deliveries")
    shift = relationship("Shift", back_populates="deliveries")
    driver = relationship("Driver", back_populates="deliveries")
