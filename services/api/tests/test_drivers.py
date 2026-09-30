"""
Integration tests for Driver endpoints — Section 14.2.
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal, get_db
from app.main import app
from app.models.admin import AdminUser
from app.models.driver import DriverRole
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


def test_list_drivers(client, super_admin_token):
    response = client.get(
        "/drivers",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert "page" in data
    assert isinstance(data["data"], list)


def test_create_and_update_driver(client, super_admin_token):
    random_suffix = uuid.uuid4().hex[:6]
    test_email = f"driver_{random_suffix}@test.com"

    # Create driver
    create_payload = {
        "full_name": f"Test Driver {random_suffix}",
        "email": test_email,
        "password": "SecurePassword123!",
        "role": "class1",
        "phone": "+447700900111",
        "licence_number": "LIC123456",
    }
    create_res = client.post(
        "/drivers",
        json=create_payload,
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert create_res.status_code == 201
    driver_data = create_res.json()
    driver_id = driver_data["id"]
    assert driver_data["email"] == test_email
    assert driver_data["role"] == "class1"
    assert driver_data["status"] == "active"

    # Patch driver (partial update)
    patch_res = client.patch(
        f"/drivers/{driver_id}",
        json={"role": "class2", "phone": "+447700900222"},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["role"] == "class2"
    assert updated_data["phone"] == "+447700900222"

    # Deactivate driver
    deact_res = client.post(
        f"/drivers/{driver_id}/deactivate",
        json={"reason": "Test deactivation"},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert deact_res.status_code == 200
    deact_data = deact_res.json()
    assert deact_data["status"] == "inactive"
    assert "deactivated_at" in deact_data
