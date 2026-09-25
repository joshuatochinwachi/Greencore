"""
IncidentReport and DefectReport models — Section 8.
"""

import uuid

from geoalchemy2 import Geography
from sqlalchemy import Column, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import TIMESTAMP

from app.database import Base


class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    incident_type = Column(
        Enum(
            "accident", "road_closure", "vehicle_breakdown", "serious_delay",
            "dangerous_location", "delivery_problem", "emergency",
            name="incident_type_enum",
        ),
        nullable=False,
    )
    description = Column(Text, nullable=False)
    photo_url = Column(String, nullable=True)
    location = Column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )
    reported_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    driver = relationship("Driver", back_populates="incident_reports")


class DefectReport(Base):
    __tablename__ = "defect_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vehicle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    defect_type = Column(
        Enum(
            "tyre", "warning_light", "brakes", "lights", "damage", "other",
            name="defect_type_enum",
        ),
        nullable=False,
    )
    description = Column(Text, nullable=False)
    photo_url = Column(String, nullable=True)
    reported_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    status = Column(
        Enum("open", "acknowledged", "resolved", name="defect_status_enum"),
        nullable=False,
        default="open",
    )

    driver = relationship("Driver", back_populates="defect_reports")
    vehicle = relationship("Vehicle", back_populates="defect_reports")
