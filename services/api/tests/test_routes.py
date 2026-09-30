"""
Integration tests for Route and Drop endpoints — Section 14.3.
"""

import io
import uuid
import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import AdminUser
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


def test_create_and_manage_route_with_drops(client, super_admin_token):
    random_code = uuid.uuid4().hex[:6]
    route_name = f"TEST ROUTE {random_code}"

    # 1. Create Route
    create_res = client.post(
        "/routes",
        json={"route_name": route_name, "max_drops": 2},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert create_res.status_code == 201
    route_data = create_res.json()
    route_id = route_data["id"]
    assert route_data["route_name"] == route_name

    # 2. Add Drop #1
    drop1_res = client.post(
        f"/routes/{route_id}/drops",
        json={
            "customer_name": "Store Alpha",
            "account_number": "ACC101",
            "postcode": "NW1 1AA",
            "delivery_instructions": "Rear bay",
        },
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert drop1_res.status_code == 201
    drop1 = drop1_res.json()
    assert drop1["sequence"] == 1
    assert drop1["customer_name"] == "Store Alpha"

    # 3. Add Drop #2
    drop2_res = client.post(
        f"/routes/{route_id}/drops",
        json={
            "customer_name": "Store Beta",
            "account_number": "ACC102",
            "postcode": "NW1 2BB",
        },
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert drop2_res.status_code == 201
    drop2 = drop2_res.json()
    assert drop2["sequence"] == 2

    # 4. Fetch Route detail
    get_res = client.get(
        f"/routes/{route_id}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert get_res.status_code == 200
    route_detail = get_res.json()
    assert len(route_detail["drops"]) == 2


def test_drop_move_with_conflict_warning(client, super_admin_token):
    # Route A (has 1 drop)
    r_a = client.post(
        "/routes",
        json={"route_name": f"ROUTE A {uuid.uuid4().hex[:4]}", "max_drops": 10},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    ).json()

    # Route B (has max_drops = 1)
    r_b = client.post(
        "/routes",
        json={"route_name": f"ROUTE B {uuid.uuid4().hex[:4]}", "max_drops": 1},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    ).json()

    # Add drop to Route B so Route B is at capacity
    client.post(
        f"/routes/{r_b['id']}/drops",
        json={"customer_name": "Existing Drop B", "account_number": "EX01"},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )

    # Add drop to Route A
    drop_a = client.post(
        f"/routes/{r_a['id']}/drops",
        json={"customer_name": "Moving Drop", "account_number": "MOVE01"},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    ).json()

    # Move drop_a to Route B without force -> should yield route_capacity_exceeded warning and moved=False
    move_res = client.post(
        f"/routes/{r_a['id']}/drops/{drop_a['id']}/move",
        json={"target_route_id": r_b["id"], "sequence": 1, "force": False},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert move_res.status_code == 200
    move_data = move_res.json()
    assert move_data["moved"] is False
    assert "route_capacity_exceeded" in move_data["warnings"]

    # Now move with force=True -> succeeds
    force_res = client.post(
        f"/routes/{r_a['id']}/drops/{drop_a['id']}/move",
        json={"target_route_id": r_b["id"], "sequence": 1, "force": True},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert force_res.status_code == 200
    force_data = force_res.json()
    assert force_data["moved"] is True


def test_csv_import_flow(client, super_admin_token):
    # CSV content with 3 rows: 2 valid, 1 missing customer name (Section 14.3 / 17.6)
    csv_data = (
        "Account No,Customer,Postcode,Notes,Route\n"
        "123456,ABC Shop,AB1 2CD,Front door,IMPORT ROUTE 1\n"
        "654321,,EF3 4GH,No name shop,IMPORT ROUTE 1\n"
        "789012,XYZ Mart,SW1 1AA,Rear bay,IMPORT ROUTE 1\n"
    )

    file_obj = io.BytesIO(csv_data.encode("utf-8"))
    upload_res = client.post(
        "/routes/import",
        files={"file": ("test_route.csv", file_obj, "text/csv")},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert upload_res.status_code == 200
    preview = upload_res.json()
    import_id = preview["import_id"]
    assert preview["row_count"] == 3
    assert "Account No" in preview["detected_columns"]

    # Commit import with column mapping
    commit_payload = {
        "import_id": import_id,
        "column_mapping": {
            "Account No": "account_number",
            "Customer": "customer_name",
            "Postcode": "postcode",
            "Notes": "delivery_instructions",
            "Route": "route_name",
        },
    }
    commit_res = client.post(
        "/routes/import/map",
        json=commit_payload,
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert commit_res.status_code == 200
    commit_data = commit_res.json()
    assert commit_data["imported"] == 2
    assert commit_data["failed"] == 1
    assert commit_data["errors"][0]["reason"] == "missing_customer_name"
