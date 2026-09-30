"""
Drivers API Router — Section 14.2.
"""

from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin, get_current_driver, require_roles
from app.models.admin import AdminUser
from app.schemas.driver import (
    DriverCreate,
    DriverDeactivateRequest,
    DriverDeactivateResponse,
    DriverListResponse,
    DriverResponse,
    DriverUpdate,
)
from app.services import driver as driver_service

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("", response_model=DriverListResponse)
def list_drivers(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[AdminUser, Depends(require_roles("super_admin", "ops_manager", "route_manager", "payroll_hr", "read_only"))],
    status: str | None = Query(None, description="Filter by driver status (active/inactive)"),
    role: str | None = Query(None, description="Filter by licence role (van, 7_5t, class1, class2)"),
    depot_id: uuid.UUID | None = Query(None, description="Filter by depot ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    drivers, total = driver_service.list_drivers(
        db,
        status=status,
        role=role,
        depot_id=depot_id,
        page=page,
        page_size=page_size,
    )
    return {
        "data": drivers,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver(
    driver_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[AdminUser, Depends(require_roles("super_admin", "ops_manager", "route_manager", "payroll_hr", "read_only"))],
):
    driver = driver_service.get_driver_by_id(db, driver_id)
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver {driver_id} not found",
        )
    return driver


@router.post("", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
def create_driver(
    driver_in: DriverCreate,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[AdminUser, Depends(require_roles("super_admin", "ops_manager"))],
):
    try:
        return driver_service.create_driver(db, driver_in, admin_user=admin_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch("/{driver_id}", response_model=DriverResponse)
def update_driver(
    driver_id: uuid.UUID,
    driver_update: DriverUpdate,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[AdminUser, Depends(require_roles("super_admin", "ops_manager"))],
):
    updated = driver_service.update_driver(db, driver_id, driver_update, admin_user=admin_user)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver {driver_id} not found",
        )
    return updated


@router.post("/{driver_id}/deactivate", response_model=DriverDeactivateResponse)
def deactivate_driver(
    driver_id: uuid.UUID,
    payload: DriverDeactivateRequest,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[AdminUser, Depends(require_roles("super_admin", "ops_manager"))],
):
    res = driver_service.deactivate_driver(
        db,
        driver_id,
        admin_user=admin_user,
        reason=payload.reason,
    )
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver {driver_id} not found",
        )
    return res
