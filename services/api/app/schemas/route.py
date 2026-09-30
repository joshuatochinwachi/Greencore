"""
Pydantic schemas for Routes, Drops, and Import endpoints — Section 14.3.
"""

from typing import Any, Literal
import uuid

from pydantic import BaseModel, ConfigDict, Field


class PointSchema(BaseModel):
    lat: float
    lng: float


class DropBase(BaseModel):
    sequence: int = Field(..., ge=1)
    account_number: str | None = None
    customer_name: str = Field(..., max_length=255)
    address: str | None = None
    postcode: str | None = Field(None, max_length=10)
    location: PointSchema | None = None
    delivery_instructions: str | None = None
    access_instructions: str | None = None
    tray_instructions: str | None = None
    opening_hours: dict[str, Any] | None = None
    contact_phone: str | None = Field(None, max_length=50)
    fixed_position: bool = False
    must_precede_drop_id: uuid.UUID | None = None
    required_vehicle_class: Literal["van", "7_5t", "class1_hgv", "class2_hgv"] | None = None
    status: Literal[
        "not_started", "en_route", "arrived", "delivered",
        "partial", "failed", "closed", "no_access", "other"
    ] = "not_started"


class DropCreate(BaseModel):
    account_number: str | None = None
    customer_name: str = Field(..., max_length=255)
    address: str | None = None
    postcode: str | None = Field(None, max_length=10)
    location: PointSchema | None = None
    delivery_instructions: str | None = None
    access_instructions: str | None = None
    tray_instructions: str | None = None
    opening_hours: dict[str, Any] | None = None
    contact_phone: str | None = Field(None, max_length=50)
    sequence: int | None = None
    fixed_position: bool = False
    must_precede_drop_id: uuid.UUID | None = None
    required_vehicle_class: Literal["van", "7_5t", "class1_hgv", "class2_hgv"] | None = None


class DropUpdate(BaseModel):
    sequence: int | None = Field(None, ge=1)
    account_number: str | None = None
    customer_name: str | None = Field(None, max_length=255)
    address: str | None = None
    postcode: str | None = Field(None, max_length=10)
    location: PointSchema | None = None
    delivery_instructions: str | None = None
    access_instructions: str | None = None
    tray_instructions: str | None = None
    opening_hours: dict[str, Any] | None = None
    contact_phone: str | None = Field(None, max_length=50)
    fixed_position: bool | None = None
    must_precede_drop_id: uuid.UUID | None = None
    required_vehicle_class: Literal["van", "7_5t", "class1_hgv", "class2_hgv"] | None = None
    status: Literal[
        "not_started", "en_route", "arrived", "delivered",
        "partial", "failed", "closed", "no_access", "other"
    ] | None = None


class DropResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sequence: int
    account_number: str | None = None
    customer_name: str
    address: str | None = None
    postcode: str | None = None
    location: PointSchema | None = None
    delivery_instructions: str | None = None
    access_instructions: str | None = None
    tray_instructions: str | None = None
    opening_hours: dict[str, Any] | None = None
    contact_phone: str | None = None
    fixed_position: bool
    must_precede_drop_id: uuid.UUID | None = None
    required_vehicle_class: str | None = None
    status: str


class RouteCreate(BaseModel):
    route_name: str = Field(..., max_length=255)
    depot_id: uuid.UUID | None = None
    start_point: PointSchema | None = None
    end_point: PointSchema | None = None
    status: Literal["active", "inactive"] = "active"
    max_drops: int | None = Field(None, ge=1)


class RouteUpdate(BaseModel):
    route_name: str | None = Field(None, max_length=255)
    depot_id: uuid.UUID | None = None
    start_point: PointSchema | None = None
    end_point: PointSchema | None = None
    status: Literal["active", "inactive"] | None = None
    max_drops: int | None = Field(None, ge=1)


class RouteSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    route_name: str
    depot_id: uuid.UUID | None = None
    status: str
    max_drops: int | None = None
    drop_count: int = 0


class RouteDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    route_name: str
    depot_id: uuid.UUID | None = None
    start_point: PointSchema | None = None
    end_point: PointSchema | None = None
    status: str
    max_drops: int | None = None
    drops: list[DropResponse] = []


class DropMoveRequest(BaseModel):
    target_route_id: uuid.UUID
    sequence: int = Field(..., ge=1)
    force: bool = False


class DropMoveResponse(BaseModel):
    moved: bool
    warnings: list[str] = []


class RouteImportPreviewResponse(BaseModel):
    import_id: str
    detected_columns: list[str]
    row_count: int
    sample_rows: list[dict[str, Any]]


class RouteImportCommitRequest(BaseModel):
    import_id: str
    column_mapping: dict[str, str]
    default_route_name: str = "Imported Route"
    depot_id: uuid.UUID | None = None


class RouteImportCommitResponse(BaseModel):
    imported: int
    failed: int
    errors: list[dict[str, Any]]
