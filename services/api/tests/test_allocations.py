"""
Integration tests for Allocation endpoints — Section 14.4 and Section 17.1.
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import AdminUser
from app.models.driver import Driver, DriverRole
from app.models.route import Route
from app.services.auth import create_access_token, hash_password


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def super_admin_token():
    db = SessionLocal()
    try:
        admin = db.query(AdminUser).filter(AdminUser.email == "test_super_admin@example.com").first()
        if not admin:
            admin = AdminUser(
                full_name="Super Admin Test",
                email="test_super_admin@example.com",
                password_hash=hash_password("Pass1234!"),
                permission_role="super_admin",
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        token, _ = create_access_token(
            subject_id=str(admin.id),
            subject_type="admin",
            role=admin.permission_role,
        )
        return token
    finally:
        db.close()


def test_allocation_overview_and_confirm(client, super_admin_token):
    target_date = "2026-10-01"

    # 1. Fetch overview for target date
    res = client.get(
        f"/allocations?date={target_date}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["date"] == target_date
    assert "drivers" in data
    assert "routes" in data
    assert "allocations" in data

    if not data["drivers"] or not data["routes"]:
        # Ensure at least 1 driver and 1 route exist
        db = SessionLocal()
        role = db.query(DriverRole).first()
        driver = Driver(
            full_name="Alloc Test Driver",
            email=f"alloc_drv_{uuid.uuid4().hex[:4]}@test.com",
            password_hash=hash_password("Pass123!"),
            role_id=role.id,
            status="active",
        )
        route = Route(route_name=f"ALLOC ROUTE {uuid.uuid4().hex[:4]}", status="active")
        db.add(driver)
        db.add(route)
        db.commit()
        db.refresh(driver)
        db.refresh(route)
        d_id = str(driver.id)
        r_id = str(route.id)
        db.close()
    else:
        d_id = str(data["drivers"][0]["id"])
        r_id = str(data["routes"][0]["id"])

    # 2. Confirm allocation
    confirm_payload = {
        "date": target_date,
        "assignments": [
            {
                "driver_id": d_id,
                "route_id": r_id,
                "planned_start": "06:30",
            }
        ],
    }

    confirm_res = client.post(
        "/allocations/confirm",
        json=confirm_payload,
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert confirm_res.status_code == 200
    confirm_data = confirm_res.json()
    assert confirm_data["confirmed"] == 1
    assert confirm_data["notifications_sent"] == 1
    assert "audit_log_entry_id" in confirm_data

    # 3. Re-fetch overview and verify scheduled/allocated flags
    recheck_res = client.get(
        f"/allocations?date={target_date}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    recheck_data = recheck_res.json()
    matched_driver = next(d for d in recheck_data["drivers"] if d["id"] == d_id)
    assert matched_driver["already_scheduled"] is True

    matched_route = next(r for r in recheck_data["routes"] if r["id"] == r_id)
    assert matched_route["allocated"] is True
