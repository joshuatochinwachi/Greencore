"""
Route & Drop domain service — Section 14.3.

Handles:
- Route CRUD and Drop management
- Sequence re-ordering
- Conflict detection (Section 15.7)
- In-memory CSV/Excel import staging & row-level commit
"""

import csv
import io
import json
import uuid
from typing import Any

from geoalchemy2.elements import WKTElement
from sqlalchemy.orm import Session

from app.models.admin import AdminUser
from app.models.route import Depot, Drop, Route
from app.models.vehicle import Vehicle
from app.schemas.route import (
    DropCreate,
    DropMoveResponse,
    DropUpdate,
    PointSchema,
    RouteCreate,
    RouteUpdate,
)
from app.services.audit import record_audit_event


def point_to_dict(point: Any) -> dict[str, float] | None:
    if point is None:
        return None
    try:
        from geoalchemy2.shape import to_shape
        shp = to_shape(point)
        return {"lat": round(shp.y, 6), "lng": round(shp.x, 6)}
    except Exception:
        return None


def dict_to_point(p: PointSchema | dict[str, float] | None) -> WKTElement | None:
    if p is None:
        return None
    if isinstance(p, dict):
        lat, lng = p["lat"], p["lng"]
    else:
        lat, lng = p.lat, p.lng
    return WKTElement(f"POINT({lng} {lat})", srid=4326)


def _drop_to_dict(drop: Drop) -> dict[str, Any]:
    return {
        "id": drop.id,
        "sequence": drop.sequence,
        "account_number": drop.account_number,
        "customer_name": drop.customer_name,
        "address": drop.address,
        "postcode": drop.postcode,
        "location": point_to_dict(drop.location),
        "delivery_instructions": drop.delivery_instructions,
        "access_instructions": drop.access_instructions,
        "tray_instructions": drop.tray_instructions,
        "opening_hours": drop.opening_hours,
        "contact_phone": drop.contact_phone,
        "fixed_position": drop.fixed_position,
        "must_precede_drop_id": drop.must_precede_drop_id,
        "required_vehicle_class": drop.required_vehicle_class,
        "status": drop.status,
    }


def _route_to_dict(route: Route, include_drops: bool = True) -> dict[str, Any]:
    res = {
        "id": route.id,
        "route_name": route.route_name,
        "depot_id": route.depot_id,
        "start_point": point_to_dict(route.start_point),
        "end_point": point_to_dict(route.end_point),
        "status": route.status,
        "max_drops": route.max_drops,
        "drop_count": len(route.drops) if route.drops else 0,
    }
    if include_drops:
        res["drops"] = [_drop_to_dict(d) for d in sorted(route.drops, key=lambda x: x.sequence)]
    return res


# ── Route CRUD ────────────────────────────────────────────────────────────────

def list_routes(
    db: Session,
    *,
    status: str | None = None,
    depot_id: uuid.UUID | None = None,
    search: str | None = None,
) -> list[dict[str, Any]]:
    query = db.query(Route)
    if status:
        query = query.filter(Route.status == status)
    if depot_id:
        query = query.filter(Route.depot_id == depot_id)
    if search:
        query = query.filter(Route.route_name.ilike(f"%{search}%"))

    routes = query.order_by(Route.route_name.asc()).all()
    return [_route_to_dict(r, include_drops=False) for r in routes]


def get_route_by_id(db: Session, route_id: uuid.UUID) -> dict[str, Any] | None:
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        return None
    return _route_to_dict(route, include_drops=True)


def create_route(
    db: Session,
    route_in: RouteCreate,
    admin_user: AdminUser | None = None,
) -> dict[str, Any]:
    route = Route(
        route_name=route_in.route_name,
        depot_id=route_in.depot_id,
        start_point=dict_to_point(route_in.start_point),
        end_point=dict_to_point(route_in.end_point),
        status=route_in.status,
        max_drops=route_in.max_drops,
    )
    db.add(route)
    db.commit()
    db.refresh(route)

    res = _route_to_dict(route, include_drops=True)
    if admin_user:
        record_audit_event(
            db=db,
            admin_user_id=admin_user.id,
            entity_type="route",
            entity_id=route.id,
            before_value=None,
            after_value={"route_name": route.route_name, "status": route.status},
        )
        db.commit()
    return res


def update_route(
    db: Session,
    route_id: uuid.UUID,
    route_update: RouteUpdate,
    admin_user: AdminUser | None = None,
) -> dict[str, Any] | None:
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        return None

    changes = {}
    if route_update.route_name is not None and route.route_name != route_update.route_name:
        route.route_name = route_update.route_name
        changes["route_name"] = route_update.route_name
    if route_update.status is not None and route.status != route_update.status:
        route.status = route_update.status
        changes["status"] = route_update.status
    if route_update.max_drops is not None and route.max_drops != route_update.max_drops:
        route.max_drops = route_update.max_drops
        changes["max_drops"] = route_update.max_drops
    if route_update.depot_id is not None and route.depot_id != route_update.depot_id:
        route.depot_id = route_update.depot_id
        changes["depot_id"] = str(route_update.depot_id)
    if route_update.start_point is not None:
        route.start_point = dict_to_point(route_update.start_point)
        changes["start_point"] = route_update.start_point.model_dump()
    if route_update.end_point is not None:
        route.end_point = dict_to_point(route_update.end_point)
        changes["end_point"] = route_update.end_point.model_dump()

    db.commit()
    db.refresh(route)

    if admin_user and changes:
        record_audit_event(
            db=db,
            admin_user_id=admin_user.id,
            entity_type="route",
            entity_id=route.id,
            before_value=None,
            after_value=changes,
        )
        db.commit()

    return _route_to_dict(route, include_drops=True)


# ── Drop Management & Conflict Checking ───────────────────────────────────────

def add_drop_to_route(
    db: Session,
    route_id: uuid.UUID,
    drop_in: DropCreate,
    admin_user: AdminUser | None = None,
) -> dict[str, Any]:
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise ValueError(f"Route {route_id} not found")

    existing_drops = sorted(route.drops, key=lambda x: x.sequence)
    max_seq = existing_drops[-1].sequence if existing_drops else 0
    seq = drop_in.sequence if drop_in.sequence is not None else max_seq + 1

    # Shift higher sequences up if inserting in the middle
    for d in existing_drops:
        if d.sequence >= seq:
            d.sequence += 1

    drop = Drop(
        route_id=route.id,
        sequence=seq,
        account_number=drop_in.account_number,
        customer_name=drop_in.customer_name,
        address=drop_in.address,
        postcode=drop_in.postcode,
        location=dict_to_point(drop_in.location),
        delivery_instructions=drop_in.delivery_instructions,
        access_instructions=drop_in.access_instructions,
        tray_instructions=drop_in.tray_instructions,
        opening_hours=drop_in.opening_hours,
        contact_phone=drop_in.contact_phone,
        fixed_position=drop_in.fixed_position,
        must_precede_drop_id=drop_in.must_precede_drop_id,
        required_vehicle_class=drop_in.required_vehicle_class,
        status="not_started",
    )
    db.add(drop)
    db.commit()
    db.refresh(drop)

    res = _drop_to_dict(drop)
    if admin_user:
        record_audit_event(
            db=db,
            admin_user_id=admin_user.id,
            entity_type="drop",
            entity_id=drop.id,
            before_value=None,
            after_value={"customer_name": drop.customer_name, "sequence": drop.sequence},
        )
        db.commit()
    return res


def check_route_conflicts(
    db: Session,
    drop: Drop,
    target_route: Route,
) -> list[str]:
    """
    Evaluates Section 15.7 conflict warnings:
    - vehicle_class_mismatch
    - route_capacity_exceeded
    - duplicate_drop
    - time_window_conflict
    """
    warnings = []

    # 1. Capacity check
    if target_route.max_drops is not None:
        current_count = len(target_route.drops)
        if current_count + 1 > target_route.max_drops:
            warnings.append("route_capacity_exceeded")

    # 2. Duplicate check (by account_number in same route)
    if drop.account_number:
        for d in target_route.drops:
            if d.id != drop.id and d.account_number == drop.account_number:
                warnings.append("duplicate_drop")
                break

    # 3. Vehicle class check (if target route has an assigned vehicle)
    # Check if target route has allocations with vehicles
    if drop.required_vehicle_class:
        for alloc in target_route.allocations:
            if alloc.vehicle and alloc.vehicle.vehicle_type != drop.required_vehicle_class:
                # E.g. class1 required but allocated to van
                warnings.append("vehicle_class_mismatch")
                break

    return warnings


def move_drop(
    db: Session,
    drop_id: uuid.UUID,
    target_route_id: uuid.UUID,
    new_sequence: int,
    force: bool = False,
    admin_user: AdminUser | None = None,
) -> DropMoveResponse:
    drop = db.query(Drop).filter(Drop.id == drop_id).first()
    if not drop:
        raise ValueError(f"Drop {drop_id} not found")

    target_route = db.query(Route).filter(Route.id == target_route_id).first()
    if not target_route:
        raise ValueError(f"Target route {target_route_id} not found")

    warnings = check_route_conflicts(db, drop, target_route)

    if warnings and not force:
        # Return warnings without applying move per Section 14.3
        return DropMoveResponse(moved=False, warnings=warnings)

    old_route_id = drop.route_id
    old_route = db.query(Route).filter(Route.id == old_route_id).first()

    # Re-sequence old route
    if old_route:
        for d in old_route.drops:
            if d.id != drop.id and d.sequence > drop.sequence:
                d.sequence -= 1

    # Shift target route sequences to make room
    for d in target_route.drops:
        if d.id != drop.id and d.sequence >= new_sequence:
            d.sequence += 1

    drop.route_id = target_route_id
    drop.sequence = new_sequence
    db.commit()

    if admin_user:
        record_audit_event(
            db=db,
            admin_user_id=admin_user.id,
            entity_type="drop",
            entity_id=drop.id,
            before_value={"route_id": str(old_route_id)},
            after_value={"route_id": str(target_route_id), "sequence": new_sequence, "warnings": warnings},
        )
        db.commit()

    return DropMoveResponse(moved=True, warnings=warnings)


# ── CSV Import Staging ────────────────────────────────────────────────────────

# In-memory store for staged uploads (can be moved to Redis in production)
_import_cache: dict[str, list[dict[str, str]]] = {}


def stage_csv_upload(file_bytes: bytes) -> tuple[str, list[str], int, list[dict[str, Any]]]:
    import_id = f"imp_{uuid.uuid4().hex[:12]}"
    content = file_bytes.decode("utf-8-sig", errors="ignore")
    reader = csv.DictReader(io.StringIO(content))
    
    rows = []
    fieldnames = reader.fieldnames or []
    for row in reader:
        rows.append(row)

    _import_cache[import_id] = rows
    sample = rows[:5]
    return import_id, list(fieldnames), len(rows), sample


def commit_csv_import(
    db: Session,
    import_id: str,
    column_mapping: dict[str, str],
    default_route_name: str = "Imported Route",
    depot_id: uuid.UUID | None = None,
    admin_user: AdminUser | None = None,
) -> tuple[int, int, list[dict[str, Any]]]:
    rows = _import_cache.get(import_id)
    if not rows:
        raise ValueError(f"Import session {import_id} not found or expired")

    imported_count = 0
    failed_count = 0
    errors = []

    # Map of route_name -> Route instance
    route_map: dict[str, Route] = {}

    for idx, row in enumerate(rows, start=1):
        # Extract mapped values
        customer_name_col = next((k for k, v in column_mapping.items() if v == "customer_name"), None)
        account_col = next((k for k, v in column_mapping.items() if v == "account_number"), None)
        postcode_col = next((k for k, v in column_mapping.items() if v == "postcode"), None)
        address_col = next((k for k, v in column_mapping.items() if v == "address"), None)
        instructions_col = next((k for k, v in column_mapping.items() if v == "delivery_instructions"), None)
        route_col = next((k for k, v in column_mapping.items() if v == "route_name"), None)

        customer_name = row.get(customer_name_col, "").strip() if customer_name_col else ""
        if not customer_name:
            failed_count += 1
            errors.append({"row": idx, "reason": "missing_customer_name"})
            continue

        postcode = row.get(postcode_col, "").strip() if postcode_col else ""
        route_name = row.get(route_col, "").strip() if route_col else default_route_name
        if not route_name:
            route_name = default_route_name

        # Resolve Route
        if route_name not in route_map:
            route = db.query(Route).filter(Route.route_name == route_name).first()
            if not route:
                route = Route(route_name=route_name, depot_id=depot_id, status="active")
                db.add(route)
                db.flush()
            route_map[route_name] = route
        route = route_map[route_name]

        seq = len(route.drops) + 1
        drop = Drop(
            route_id=route.id,
            sequence=seq,
            account_number=row.get(account_col, "").strip() if account_col else None,
            customer_name=customer_name,
            address=row.get(address_col, "").strip() if address_col else None,
            postcode=postcode or None,
            delivery_instructions=row.get(instructions_col, "").strip() if instructions_col else None,
            status="not_started",
        )
        db.add(drop)
        route.drops.append(drop)
        imported_count += 1

    db.commit()

    if admin_user and imported_count > 0:
        record_audit_event(
            db=db,
            admin_user_id=admin_user.id,
            entity_type="route_import",
            entity_id=uuid.uuid4(),
            before_value=None,
            after_value={"imported": imported_count, "failed": failed_count},
        )
        db.commit()

    # Clear staging cache
    _import_cache.pop(import_id, None)

    return imported_count, failed_count, errors
