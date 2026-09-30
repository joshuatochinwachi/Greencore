"""
Allocation API Router — Section 14.4.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models.admin import AdminUser
from app.schemas.allocation import (
    AllocationConfirmRequest,
    AllocationConfirmResponse,
    AllocationOverviewResponse,
)
from app.services import allocation as allocation_service

router = APIRouter(prefix="/allocations", tags=["allocations"])


@router.get("", response_model=AllocationOverviewResponse)
def get_allocations(
    date: str = Query(..., description="Target date in YYYY-MM-DD format", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_roles("super_admin", "ops_manager", "route_manager", "payroll_hr", "read_only")),
):
    return allocation_service.get_allocations_overview(db, date)


@router.post("/confirm", response_model=AllocationConfirmResponse)
def confirm_allocations(
    payload: AllocationConfirmRequest,
    db: Session = Depends(get_db),
    admin_user: AdminUser = Depends(require_roles("super_admin", "ops_manager", "route_manager")),
):
    return allocation_service.confirm_allocations(
        db=db,
        date_str=payload.date,
        assignments=payload.assignments,
        admin_user=admin_user,
    )
