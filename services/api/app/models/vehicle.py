"""
Vehicle and DriverVehicleAssignment models — Section 8.
"""

import uuid

from sqlalchemy import Column, Date, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    registration = Column(String(20), unique=True, nullable=False)
    vehicle_type = Column(
        Enum("van", "7_5t", "class1_hgv", "class2_hgv", name="vehicle_type_enum"),
        nullable=False,
    )
    weight_class = Column(String(50), nullable=True)
    mot_due = Column(Date, nullable=True)
    insurance_due = Column(Date, nullable=True)
    service_due = Column(Date, nullable=True)
    status = Column(
        Enum("active", "in_repair", "retired", name="vehicle_status_enum"),
        nullable=False,
        default="active",
    )

    assignments = relationship("DriverVehicleAssignment", back_populates="vehicle")
    allocations = relationship("Allocation", back_populates="vehicle")
    defect_reports = relationship("DefectReport", back_populates="vehicle")

    def __repr__(self) -> str:
        return f"<Vehicle {self.registration}>"


class DriverVehicleAssignment(Base):
    """Junction table — which driver is assigned to which vehicle."""

    __tablename__ = "driver_vehicle_assignments"

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

    driver = relationship("Driver", back_populates="vehicle_assignments")
    vehicle = relationship("Vehicle", back_populates="assignments")
