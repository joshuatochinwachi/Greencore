"""
Database seed script — Section 19.

Populates initial seed fixtures into the database for local dev and CI testing.
Idempotent: skips records that already exist by primary key or unique fields.

Usage:
    python scripts/seed.py
    # or from project root:
    # python -m scripts.seed (with PYTHONPATH set to services/api)
"""

import json
import os
import sys
import uuid
from pathlib import Path

# Ensure 'app' package is importable when running directly from scripts/ or services/api
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.database import SessionLocal
from app.models.admin import AdminUser
from app.models.driver import Driver, DriverRole
from app.models.route import Depot, Drop, Route
from app.models.vehicle import DriverVehicleAssignment, Vehicle
from app.services.auth import hash_password


def run_seed():
    fixtures_path = BASE_DIR / "fixtures" / "seed.json"
    if not fixtures_path.exists():
        print(f"Error: Fixture file not found at {fixtures_path}")
        sys.exit(1)

    with open(fixtures_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    db = SessionLocal()
    try:
        print("🌱 Seeding database...")

        # 1. Depots
        for d in data.get("depots", []):
            depot_id = uuid.UUID(d["id"])
            existing = db.query(Depot).filter(Depot.id == depot_id).first()
            if not existing:
                depot = Depot(id=depot_id, name=d["name"])
                db.add(depot)
                print(f"  + Added depot: {d['name']}")
        db.commit()

        # 2. Admin Users
        for a in data.get("admin_users", []):
            admin_id = uuid.UUID(a["id"])
            existing = db.query(AdminUser).filter(AdminUser.email == a["email"]).first()
            if not existing:
                admin = AdminUser(
                    id=admin_id,
                    full_name=a["full_name"],
                    email=a["email"],
                    password_hash=hash_password(a.get("password", "Password123!")),
                    permission_role=a["permission_role"],
                )
                db.add(admin)
                print(f"  + Added admin user: {a['email']} ({a['permission_role']})")
        db.commit()

        # 3. Vehicles
        for v in data.get("vehicles", []):
            veh_id = uuid.UUID(v["id"])
            existing = db.query(Vehicle).filter(Vehicle.registration == v["registration"]).first()
            if not existing:
                vehicle = Vehicle(
                    id=veh_id,
                    registration=v["registration"],
                    vehicle_type=v["vehicle_type"],
                    status=v.get("status", "active"),
                )
                db.add(vehicle)
                print(f"  + Added vehicle: {v['registration']} ({v['vehicle_type']})")
        db.commit()

        # 4. Driver Roles (ensure exist, usually seeded by migration)
        default_roles = [
            ("van", "Van"),
            ("7_5t", "7.5 Tonne"),
            ("class1", "Class 1 HGV"),
            ("class2", "Class 2 HGV"),
        ]
        role_map = {}
        for code, label in default_roles:
            role = db.query(DriverRole).filter(DriverRole.code == code).first()
            if not role:
                role = DriverRole(code=code, label=label)
                db.add(role)
                db.flush()
                print(f"  + Added driver role: {code}")
            role_map[code] = role.id
        db.commit()

        # 5. Drivers
        for dr in data.get("drivers", []):
            driver_id = uuid.UUID(dr["id"])
            existing = db.query(Driver).filter(Driver.email == dr["email"]).first()
            if not existing:
                role_code = dr.get("role", "class1")
                role_id = role_map.get(role_code)
                if not role_id:
                    role_obj = db.query(DriverRole).filter(DriverRole.code == role_code).first()
                    role_id = role_obj.id if role_obj else None

                driver = Driver(
                    id=driver_id,
                    full_name=dr["full_name"],
                    email=dr["email"],
                    password_hash=hash_password(dr.get("password", "Password123!")),
                    role_id=role_id,
                    status=dr.get("status", "active"),
                    depot_id=uuid.UUID(dr["depot_id"]) if dr.get("depot_id") else None,
                )
                db.add(driver)
                db.flush()
                print(f"  + Added driver: {dr['email']}")

                # Assign vehicle if present
                if dr.get("vehicle_id"):
                    v_id = uuid.UUID(dr["vehicle_id"])
                    assignment = DriverVehicleAssignment(
                        driver_id=driver.id,
                        vehicle_id=v_id,
                    )
                    db.add(assignment)
                    print(f"    -> Assigned to vehicle {dr['vehicle_id']}")
        db.commit()

        # 6. Routes and Drops
        for r in data.get("routes", []):
            route_id = uuid.UUID(r["id"])
            existing_route = db.query(Route).filter(Route.id == route_id).first()
            if not existing_route:
                route = Route(
                    id=route_id,
                    route_name=r["route_name"],
                    depot_id=uuid.UUID(r["depot_id"]) if r.get("depot_id") else None,
                    status=r.get("status", "active"),
                )
                db.add(route)
                db.flush()
                print(f"  + Added route: {r['route_name']}")

                for drop_data in r.get("drops", []):
                    drop = Drop(
                        id=uuid.UUID(drop_data["id"]),
                        route_id=route.id,
                        sequence=drop_data["sequence"],
                        account_number=drop_data.get("account_number"),
                        customer_name=drop_data["customer_name"],
                        postcode=drop_data.get("postcode"),
                        delivery_instructions=drop_data.get("delivery_instructions"),
                        status=drop_data.get("status", "not_started"),
                    )
                    db.add(drop)
                    print(f"    - Drop #{drop.sequence}: {drop.customer_name}")
        db.commit()

        print("✅ Seeding completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"❌ Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
