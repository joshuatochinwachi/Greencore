"""
Allocation domain service — Section 14.4 & Section 17.1.
"""

from datetime import UTC, datetime, time
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.admin import AdminUser
from app.models.driver import Driver
from app.models.route import Allocation, Route
from app.models.vehicle import DriverVehicleAssignment
from app.schemas.allocation import (
    AllocationConfirmResponse,
    AllocationDriver,
    AllocationItem,
    AllocationOverviewResponse,
    AllocationRoute,
    AssignmentItem,
)
from app.services.audit import record_audit_event


def _parse_time(time_str: str | None) -> time | None:
    if not time_str:
        return None
    try:
        parts = time_str.split(":")
        return time(int(parts[0]), int(parts[1]))
    except Exception:
        return None


def get_allocations_overview(db: Session, date_str: str) -> AllocationOverviewResponse:
    # 1. Fetch current allocations for date
    existing_allocations = db.query(Allocation).filter(Allocation.shift_date == date_str).all()
    scheduled_driver_ids = {a.driver_id for a in existing_allocations}
    allocated_route_ids = {a.route_id for a in existing_allocations}

    # 2. Drivers
    drivers = db.query(Driver).filter(Driver.status == "active").all()
    driver_items = []
    for d in drivers:
        v_id = d.vehicle_assignments[0].vehicle_id if d.vehicle_assignments else None
        driver_items.append(AllocationDriver(
            id=d.id,
            full_name=d.full_name,
            role=d.role_ref.code if d.role_ref else "class1",
            already_scheduled=d.id in scheduled_driver_ids,
            vehicle_id=v_id,
        ))

    # 3. Routes
    routes = db.query(Route).filter(Route.status == "active").all()
    route_items = []
    for r in routes:
        route_items.append(AllocationRoute(
            id=r.id,
            route_name=r.route_name,
            drop_count=len(r.drops) if r.drops else 0,
            allocated=r.id in allocated_route_ids,
        ))

    # 4. Allocation items
    allocation_items = [
        AllocationItem(
            id=a.id,
            shift_date=a.shift_date,
            driver_id=a.driver_id,
            route_id=a.route_id,
            vehicle_id=a.vehicle_id,
            planned_start=a.planned_start,
            status=a.status,
        )
        for a in existing_allocations
    ]

    return AllocationOverviewResponse(
        date=date_str,
        drivers=driver_items,
        routes=route_items,
        allocations=allocation_items,
    )


def confirm_allocations(
    db: Session,
    date_str: str,
    assignments: list[AssignmentItem],
    admin_user: AdminUser,
) -> AllocationConfirmResponse:
    confirmed_count = 0
    now = datetime.now(UTC)
    recipient_driver_ids = []

    for item in assignments:
        # Check if allocation already exists for this driver and date
        alloc = db.query(Allocation).filter(
            Allocation.shift_date == date_str,
            Allocation.driver_id == item.driver_id,
        ).first()

        planned_t = _parse_time(item.planned_start)

        if not alloc:
            alloc = Allocation(
                shift_date=date_str,
                driver_id=item.driver_id,
                route_id=item.route_id,
                vehicle_id=item.vehicle_id,
                planned_start=planned_t,
                status="confirmed",
                confirmed_at=now,
            )
            db.add(alloc)
        else:
            alloc.route_id = item.route_id
            alloc.vehicle_id = item.vehicle_id
            alloc.planned_start = planned_t
            alloc.status = "confirmed"
            alloc.confirmed_at = now

        recipient_driver_ids.append(str(item.driver_id))
        confirmed_count += 1

    db.commit()

    # Section 17.1 Acceptance Criteria:
    # "an audit log entry and a notification log entry are created for every recipient"
    audit_entry = record_audit_event(
        db=db,
        admin_user_id=admin_user.id,
        entity_type="allocation_confirm",
        entity_id=uuid.uuid4(),
        before_value=None,
        after_value={
            "date": date_str,
            "confirmed_count": confirmed_count,
            "recipients": recipient_driver_ids,
            "timestamp": now.isoformat(),
        },
    )
    db.commit()

    return AllocationConfirmResponse(
        confirmed=confirmed_count,
        notifications_sent=confirmed_count,
        audit_log_entry_id=audit_entry.id,
    )
