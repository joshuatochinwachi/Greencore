"""
Pydantic schemas for Driver endpoints — Section 14.2.
"""

from datetime import datetime
from typing import Literal
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class DriverBase(BaseModel):
    full_name: str = Field(..., max_length=255)
    email: EmailStr
    phone: str | None = Field(None, max_length=30)
    photo_url: str | None = None
    role: str = "class1"
    licence_number: str | None = Field(None, max_length=100)
    status: Literal["active", "inactive"] = "active"
    depot_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None


class DriverCreate(BaseModel):
    full_name: str = Field(..., max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone: str | None = Field(None, max_length=30)
    photo_url: str | None = None
    role: str = "class1"
    licence_number: str | None = Field(None, max_length=100)
    depot_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None


class DriverUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=30)
    photo_url: str | None = None
    role: str | None = None
    licence_number: str | None = Field(None, max_length=100)
    status: Literal["active", "inactive"] | None = None
    depot_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None


class DriverResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: str
    phone: str | None = None
    photo_url: str | None = None
    role: str
    licence_number: str | None = None
    status: str
    depot_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    created_at: datetime


class DriverListResponse(BaseModel):
    data: list[DriverResponse]
    page: int
    page_size: int
    total: int


class DriverDeactivateRequest(BaseModel):
    reason: str | None = None


class DriverDeactivateResponse(BaseModel):
    id: uuid.UUID
    status: str
    deactivated_at: datetime
