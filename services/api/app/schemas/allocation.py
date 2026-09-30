"""
Pydantic schemas for Allocation endpoints — Section 14.4.
"""

from datetime import time
from typing import Literal
import uuid

from pydantic import BaseModel, ConfigDict, Field


class AllocationDriver(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    role: str
    already_scheduled: bool = False
    vehicle_id: uuid.UUID | None = None


class AllocationRoute(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    route_name: str
    drop_count: int = 0
    allocated: bool = False


class AllocationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    shift_date: str
    driver_id: uuid.UUID
    route_id: uuid.UUID
    vehicle_id: uuid.UUID | None = None
    planned_start: time | None = None
    status: Literal["draft", "confirmed", "notified"]


class AllocationOverviewResponse(BaseModel):
    date: str
    drivers: list[AllocationDriver]
    routes: list[AllocationRoute]
    allocations: list[AllocationItem] = []


class AssignmentItem(BaseModel):
    driver_id: uuid.UUID
    route_id: uuid.UUID
    vehicle_id: uuid.UUID | None = None
    planned_start: str | None = Field(None, description="Planned start time, e.g. '06:00'")


class AllocationConfirmRequest(BaseModel):
    date: str = Field(..., description="Target date in YYYY-MM-DD format")
    assignments: list[AssignmentItem]


class AllocationConfirmResponse(BaseModel):
    confirmed: int
    notifications_sent: int
    audit_log_entry_id: uuid.UUID
