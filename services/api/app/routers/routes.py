"""
Routes and Drops API Router — Section 14.3.
"""

from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models.admin import AdminUser
from app.schemas.route import (
    DropCreate,
    DropMoveRequest,
    DropMoveResponse,
    DropResponse,
    RouteCreate,
    RouteDetailResponse,
    RouteImportCommitRequest,
    RouteImportCommitResponse,
    RouteImportPreviewResponse,
    RouteSummaryResponse,
    RouteUpdate,
)
from app.services import route as route_service

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=list[RouteSummaryResponse])
def list_routes(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[AdminUser, Depends(require_roles("super_admin", "ops_manager", "route_manager", "payroll_hr", "read_only"))],
    status: str | None = Query(None),
    depot_id: uuid.UUID | None = Query(None),
    search: str | None = Query(None),
):
    return route_service.list_routes(db, status=status, depot_id=depot_id, search=search)


@router.get("/{route_id}", response_model=RouteDetailResponse)
def get_route(
    route_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[AdminUser, Depends(require_roles("super_admin", "ops_manager", "route_manager", "payroll_hr", "read_only"))],
):
    route = route_service.get_route_by_id(db, route_id)
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route {route_id} not found",
        )
    return route


@router.post("", response_model=RouteDetailResponse, status_code=status.HTTP_201_CREATED)
def create_route(
    route_in: RouteCreate,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[AdminUser, Depends(require_roles("super_admin", "ops_manager", "route_manager"))],
):
    return route_service.create_route(db, route_in, admin_user=admin_user)


@router.patch("/{route_id}", response_model=RouteDetailResponse)
def update_route(
    route_id: uuid.UUID,
    route_update: RouteUpdate,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[AdminUser, Depends(require_roles("super_admin", "ops_manager", "route_manager"))],
):
    updated = route_service.update_route(db, route_id, route_update, admin_user=admin_user)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route {route_id} not found",
        )
    return updated


@router.post("/{route_id}/drops", response_model=DropResponse, status_code=status.HTTP_201_CREATED)
def add_drop_to_route(
    route_id: uuid.UUID,
    drop_in: DropCreate,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[AdminUser, Depends(require_roles("super_admin", "ops_manager", "route_manager"))],
):
    try:
        return route_service.add_drop_to_route(db, route_id, drop_in, admin_user=admin_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{route_id}/drops/{drop_id}/move", response_model=DropMoveResponse)
def move_drop(
    route_id: uuid.UUID,
    drop_id: uuid.UUID,
    payload: DropMoveRequest,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[AdminUser, Depends(require_roles("super_admin", "ops_manager", "route_manager"))],
):
    try:
        return route_service.move_drop(
            db=db,
            drop_id=drop_id,
            target_route_id=payload.target_route_id,
            new_sequence=payload.sequence,
            force=payload.force,
            admin_user=admin_user,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ── Import Endpoints ──────────────────────────────────────────────────────────

@router.post("/import", response_model=RouteImportPreviewResponse)
async def upload_import_file(
    file: UploadFile = File(...),
    _admin: Annotated[AdminUser, Depends(require_roles("super_admin", "ops_manager", "route_manager"))] = None,
):
    if not file.filename.endswith((".csv", ".txt")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currently supporting CSV file uploads (.csv)",
        )
    content = await file.read()
    import_id, cols, row_count, sample = route_service.stage_csv_upload(content)
    return {
        "import_id": import_id,
        "detected_columns": cols,
        "row_count": row_count,
        "sample_rows": sample,
    }


@router.post("/import/map", response_model=RouteImportCommitResponse)
def commit_mapped_import(
    payload: RouteImportCommitRequest,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[AdminUser, Depends(require_roles("super_admin", "ops_manager", "route_manager"))],
):
    try:
        imported, failed, errors = route_service.commit_csv_import(
            db=db,
            import_id=payload.import_id,
            column_mapping=payload.column_mapping,
            default_route_name=payload.default_route_name,
            depot_id=payload.depot_id,
            admin_user=admin_user,
        )
        return {
            "imported": imported,
            "failed": failed,
            "errors": errors,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
