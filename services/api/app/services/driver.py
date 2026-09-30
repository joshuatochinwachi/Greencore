"""
Driver domain service — Section 14.2.
"""

from datetime import UTC, datetime
import math
import uuid
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.admin import AdminUser
from app.models.driver import Driver, DriverRole
from app.models.vehicle import DriverVehicleAssignment
from app.schemas.driver import DriverCreate, DriverResponse, DriverUpdate
from app.services.audit import record_audit_event
from app.services.auth import hash_password, revoke_all_driver_tokens


def _driver_to_response_dict(driver: Driver) -> dict[str, Any]:
    # Determine vehicle_id from active assignment if any
    vehicle_id = None
    if driver.vehicle_assignments:
        vehicle_id = driver.vehicle_assignments[0].vehicle_id

    role_code = driver.role_ref.code if driver.role_ref else "class1"

    return {
        "id": driver.id,
        "full_name": driver.full_name,
        "email": driver.email,
        "phone": driver.phone,
        "photo_url": driver.photo_url,
        "role": role_code,
        "licence_number": driver.licence_number,
        "status": driver.status,
        "depot_id": driver.depot_id,
        "vehicle_id": vehicle_id,
        "created_at": driver.created_at,
    }


def list_drivers(
    db: Session,
    *,
    status: str | None = None,
    role: str | None = None,
    depot_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    query = db.query(Driver)

    if status:
        query = query.filter(Driver.status == status)
    if depot_id:
        query = query.filter(Driver.depot_id == depot_id)
    if role:
        query = query.join(DriverRole).filter(DriverRole.code == role)

    total = query.count()
    offset = (page - 1) * page_size
    drivers = query.order_by(Driver.created_at.desc()).offset(offset).limit(page_size).all()

    return [_driver_to_response_dict(d) for d in drivers], total


def get_driver_by_id(db: Session, driver_id: uuid.UUID) -> dict[str, Any] | None:
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        return None
    return _driver_to_response_dict(driver)


def create_driver(
    db: Session,
    driver_in: DriverCreate,
    admin_user: AdminUser | None = None,
) -> dict[str, Any]:
    # Resolve role lookup
    role = db.query(DriverRole).filter(DriverRole.code == driver_in.role).first()
    if not role:
        # Default or fallback
        role = db.query(DriverRole).filter(DriverRole.code == "class1").first()

    driver = Driver(
        full_name=driver_in.full_name,
        email=driver_in.email,
        phone=driver_in.phone,
        photo_url=driver_in.photo_url,
        password_hash=hash_password(driver_in.password),
        role_id=role.id if role else uuid.uuid4(),
        licence_number=driver_in.licence_number,
        status="active",
        depot_id=driver_in.depot_id,
    )
    db.add(driver)
    db.flush()

    if driver_in.vehicle_id:
        assignment = DriverVehicleAssignment(
            driver_id=driver.id,
            vehicle_id=driver_in.vehicle_id,
        )
        db.add(assignment)

    db.commit()
    db.refresh(driver)

    result = _driver_to_response_dict(driver)

    if admin_user:
        record_audit_event(
            db=db,
            admin_user_id=admin_user.id,
            entity_type="driver",
            entity_id=driver.id,
            before_value=None,
            after_value=result,
        )
        db.commit()

    return result


def update_driver(
    db: Session,
    driver_id: uuid.UUID,
    driver_update: DriverUpdate,
    admin_user: AdminUser | None = None,
) -> dict[str, Any] | None:
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        return None

    before_value = _driver_to_response_dict(driver)
    changes: dict[str, Any] = {}

    if driver_update.full_name is not None and driver.full_name != driver_update.full_name:
        driver.full_name = driver_update.full_name
        changes["full_name"] = driver_update.full_name

    if driver_update.email is not None and driver.email != driver_update.email:
        driver.email = driver_update.email
        changes["email"] = driver_update.email

    if driver_update.phone is not None and driver.phone != driver_update.phone:
        driver.phone = driver_update.phone
        changes["phone"] = driver_update.phone

    if driver_update.photo_url is not None and driver.photo_url != driver_update.photo_url:
        driver.photo_url = driver_update.photo_url
        changes["photo_url"] = driver_update.photo_url

    if driver_update.licence_number is not None and driver.licence_number != driver_update.licence_number:
        driver.licence_number = driver_update.licence_number
        changes["licence_number"] = driver_update.licence_number

    if driver_update.status is not None and driver.status != driver_update.status:
        driver.status = driver_update.status
        changes["status"] = driver_update.status

    if driver_update.depot_id is not None and driver.depot_id != driver_update.depot_id:
        driver.depot_id = driver_update.depot_id
        changes["depot_id"] = str(driver_update.depot_id)

    if driver_update.role is not None:
        role = db.query(DriverRole).filter(DriverRole.code == driver_update.role).first()
        if role and driver.role_id != role.id:
            driver.role_id = role.id
            changes["role"] = driver_update.role

    if driver_update.vehicle_id is not None:
        # Update assignment
        current_assignment = db.query(DriverVehicleAssignment).filter(
            DriverVehicleAssignment.driver_id == driver.id
        ).first()
        if current_assignment:
            if current_assignment.vehicle_id != driver_update.vehicle_id:
                current_assignment.vehicle_id = driver_update.vehicle_id
                changes["vehicle_id"] = str(driver_update.vehicle_id)
        else:
            db.add(DriverVehicleAssignment(
                driver_id=driver.id,
                vehicle_id=driver_update.vehicle_id,
            ))
            changes["vehicle_id"] = str(driver_update.vehicle_id)

    db.commit()
    db.refresh(driver)
    after_value = _driver_to_response_dict(driver)

    if admin_user and changes:
        # Section 17.4: Only record changed fields
        diff_before = {k: before_value.get(k) for k in changes}
        record_audit_event(
            db=db,
            admin_user_id=admin_user.id,
            entity_type="driver",
            entity_id=driver.id,
            before_value=diff_before,
            after_value=changes,
        )
        db.commit()

    return after_value


def deactivate_driver(
    db: Session,
    driver_id: uuid.UUID,
    admin_user: AdminUser | None = None,
    reason: str | None = None,
) -> dict[str, Any] | None:
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        return None

    driver.status = "inactive"
    deactivated_at = datetime.now(UTC)

    # Revoke all active refresh tokens for this driver immediately (Section 14.2)
    revoke_all_driver_tokens(db, str(driver_id))

    db.commit()

    if admin_user:
        record_audit_event(
            db=db,
            admin_user_id=admin_user.id,
            entity_type="driver",
            entity_id=driver.id,
            before_value={"status": "active"},
            after_value={"status": "inactive", "reason": reason, "deactivated_at": deactivated_at.isoformat()},
        )
        db.commit()

    return {
        "id": driver.id,
        "status": "inactive",
        "deactivated_at": deactivated_at,
    }
