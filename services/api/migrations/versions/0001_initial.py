"""Initial schema — Phase 0 foundations.

Creates all tables defined in Section 8 of GREENCORE_DOCUMENTATION.md.
PostGIS extension is enabled first so geography columns can be created.

Revision ID: 0001_initial
Revises: (none)
Create Date: 2026-09-25
"""

from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── PostGIS extension ─────────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # ── Enums ─────────────────────────────────────────────────────────────────
    driver_status_enum = postgresql.ENUM(
        "active", "inactive", name="driver_status_enum", create_type=False
    )
    vehicle_type_enum = postgresql.ENUM(
        "van", "7_5t", "class1_hgv", "class2_hgv",
        name="vehicle_type_enum", create_type=False,
    )
    vehicle_status_enum = postgresql.ENUM(
        "active", "in_repair", "retired",
        name="vehicle_status_enum", create_type=False,
    )
    route_status_enum = postgresql.ENUM(
        "active", "inactive", name="route_status_enum", create_type=False
    )
    drop_vehicle_class_enum = postgresql.ENUM(
        "van", "7_5t", "class1_hgv", "class2_hgv",
        name="drop_vehicle_class_enum", create_type=False,
    )
    drop_status_enum = postgresql.ENUM(
        "not_started", "en_route", "arrived", "delivered",
        "partial", "failed", "closed", "no_access", "other",
        name="drop_status_enum", create_type=False,
    )
    allocation_status_enum = postgresql.ENUM(
        "draft", "confirmed", "notified",
        name="allocation_status_enum", create_type=False,
    )
    delivery_status_enum = postgresql.ENUM(
        "not_started", "en_route", "arrived", "delivered",
        "partial", "failed", "closed", "no_access", "other",
        name="delivery_status_enum", create_type=False,
    )
    failure_reason_enum = postgresql.ENUM(
        "shop_closed", "no_access", "loading_bay_unavailable",
        "road_closed", "customer_refused", "wrong_address",
        "vehicle_issue", "product_unavailable", "other",
        name="failure_reason_enum", create_type=False,
    )
    chat_scope_enum = postgresql.ENUM(
        "route", "depot", "global", name="chat_scope_enum", create_type=False
    )
    announcement_target_enum = postgresql.ENUM(
        "all", "driver", "route", "depot", "vehicle_category",
        name="announcement_target_enum", create_type=False,
    )
    admin_role_enum = postgresql.ENUM(
        "super_admin", "ops_manager", "route_manager", "payroll_hr", "read_only",
        name="admin_role_enum", create_type=False,
    )
    incident_type_enum = postgresql.ENUM(
        "accident", "road_closure", "vehicle_breakdown", "serious_delay",
        "dangerous_location", "delivery_problem", "emergency",
        name="incident_type_enum", create_type=False,
    )
    defect_type_enum = postgresql.ENUM(
        "tyre", "warning_light", "brakes", "lights", "damage", "other",
        name="defect_type_enum", create_type=False,
    )
    defect_status_enum = postgresql.ENUM(
        "open", "acknowledged", "resolved",
        name="defect_status_enum", create_type=False,
    )

    # Create enum types in the DB
    for enum in [
        driver_status_enum, vehicle_type_enum, vehicle_status_enum,
        route_status_enum, drop_vehicle_class_enum, drop_status_enum,
        allocation_status_enum, delivery_status_enum, failure_reason_enum,
        chat_scope_enum, announcement_target_enum, admin_role_enum,
        incident_type_enum, defect_type_enum, defect_status_enum,
    ]:
        enum.create(op.get_bind(), checkfirst=True)

    # ── driver_roles (lookup table, Section 15.1) ─────────────────────────────
    op.create_table(
        "driver_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("label", sa.String(100), nullable=False),
    )
    # Seed the four initial roles
    op.execute("""
        INSERT INTO driver_roles (id, code, label) VALUES
        (gen_random_uuid(), 'van',    'Van Driver'),
        (gen_random_uuid(), '7_5t',   '7.5 Tonne'),
        (gen_random_uuid(), 'class1', 'Class 1 HGV'),
        (gen_random_uuid(), 'class2', 'Class 2 HGV');
    """)

    # ── depots ────────────────────────────────────────────────────────────────
    op.create_table(
        "depots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
    )

    # ── admin_users ───────────────────────────────────────────────────────────
    op.create_table(
        "admin_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("permission_role", admin_role_enum, nullable=False, server_default="read_only"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_admin_users_email", "admin_users", ["email"])

    # ── drivers ───────────────────────────────────────────────────────────────
    op.create_table(
        "drivers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("photo_url", sa.Text, nullable=True),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("driver_roles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("licence_number", sa.String(100), nullable=True),
        sa.Column("status", driver_status_enum, nullable=False, server_default="active"),
        sa.Column(
            "depot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("depots.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_drivers_email", "drivers", ["email"])
    op.create_index("ix_drivers_depot_id", "drivers", ["depot_id"])

    # ── vehicles ──────────────────────────────────────────────────────────────
    op.create_table(
        "vehicles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("registration", sa.String(20), nullable=False, unique=True),
        sa.Column("vehicle_type", vehicle_type_enum, nullable=False),
        sa.Column("weight_class", sa.String(50), nullable=True),
        sa.Column("mot_due", sa.Date, nullable=True),
        sa.Column("insurance_due", sa.Date, nullable=True),
        sa.Column("service_due", sa.Date, nullable=True),
        sa.Column("status", vehicle_status_enum, nullable=False, server_default="active"),
    )

    # ── driver_vehicle_assignments ────────────────────────────────────────────
    op.create_table(
        "driver_vehicle_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "driver_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drivers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vehicle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("vehicles.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    op.create_index("ix_dva_driver_id", "driver_vehicle_assignments", ["driver_id"])
    op.create_index("ix_dva_vehicle_id", "driver_vehicle_assignments", ["vehicle_id"])

    # ── routes ────────────────────────────────────────────────────────────────
    op.create_table(
        "routes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("route_name", sa.String(255), nullable=False),
        sa.Column(
            "depot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("depots.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "start_point",
            geoalchemy2.Geography(geometry_type="POINT", srid=4326),
            nullable=True,
        ),
        sa.Column(
            "end_point",
            geoalchemy2.Geography(geometry_type="POINT", srid=4326),
            nullable=True,
        ),
        sa.Column("status", route_status_enum, nullable=False, server_default="active"),
        sa.Column("max_drops", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_routes_depot_id", "routes", ["depot_id"])

    # ── drops ─────────────────────────────────────────────────────────────────
    op.create_table(
        "drops",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "route_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("routes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer, nullable=False),
        sa.Column("account_number", sa.String(100), nullable=True),
        sa.Column("customer_name", sa.String(255), nullable=False),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("postcode", sa.String(10), nullable=True),
        sa.Column(
            "location",
            geoalchemy2.Geography(geometry_type="POINT", srid=4326),
            nullable=True,
        ),
        sa.Column("delivery_instructions", sa.Text, nullable=True),
        sa.Column("access_instructions", sa.Text, nullable=True),
        sa.Column("tray_instructions", sa.Text, nullable=True),
        sa.Column("opening_hours", postgresql.JSONB, nullable=True),
        sa.Column("contact_phone", sa.String(30), nullable=True),
        sa.Column("fixed_position", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "must_precede_drop_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drops.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("required_vehicle_class", drop_vehicle_class_enum, nullable=True),
        sa.Column("status", drop_status_enum, nullable=False, server_default="not_started"),
    )
    op.create_index("ix_drops_route_id", "drops", ["route_id"])

    # ── allocations ───────────────────────────────────────────────────────────
    op.create_table(
        "allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("shift_date", sa.String(10), nullable=False),
        sa.Column(
            "driver_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drivers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "route_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("routes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vehicle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("vehicles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("planned_start", sa.Time, nullable=True),
        sa.Column("status", allocation_status_enum, nullable=False, server_default="draft"),
        sa.Column("confirmed_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index("ix_allocations_shift_date", "allocations", ["shift_date"])
    op.create_index("ix_allocations_driver_id", "allocations", ["driver_id"])
    op.create_index("ix_allocations_route_id", "allocations", ["route_id"])

    # ── shifts ────────────────────────────────────────────────────────────────
    op.create_table(
        "shifts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "driver_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drivers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "allocation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("allocations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("start_time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("end_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("breaks", postgresql.JSONB, nullable=True),
        sa.Column("total_working_time", sa.Interval, nullable=True),
        sa.Column("amended", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("amendment_reason", sa.Text, nullable=True),
        sa.Column(
            "amended_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_shifts_driver_id", "shifts", ["driver_id"])

    # ── deliveries ────────────────────────────────────────────────────────────
    op.create_table(
        "deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "drop_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drops.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "shift_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("shifts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "driver_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drivers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", delivery_status_enum, nullable=False),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "completed_location",
            geoalchemy2.Geography(geometry_type="POINT", srid=4326),
            nullable=True,
        ),
        sa.Column("proof_photo_url", sa.Text, nullable=True),
        sa.Column("signature_url", sa.Text, nullable=True),
        sa.Column("failure_reason", failure_reason_enum, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("client_uuid", postgresql.UUID(as_uuid=True), nullable=True, unique=True),
    )
    op.create_index("ix_deliveries_drop_id", "deliveries", ["drop_id"])
    op.create_index("ix_deliveries_shift_id", "deliveries", ["shift_id"])
    op.create_index("ix_deliveries_driver_id", "deliveries", ["driver_id"])
    op.create_index("ix_deliveries_client_uuid", "deliveries", ["client_uuid"])

    # ── location_pings ────────────────────────────────────────────────────────
    op.create_table(
        "location_pings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "shift_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("shifts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "location",
            geoalchemy2.Geography(geometry_type="POINT", srid=4326),
            nullable=False,
        ),
        sa.Column(
            "recorded_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_location_pings_shift_id", "location_pings", ["shift_id"])
    op.create_index("ix_location_pings_recorded_at", "location_pings", ["recorded_at"])

    # ── chat_messages ─────────────────────────────────────────────────────────
    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "sender_driver_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drivers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("photo_url", sa.Text, nullable=True),
        sa.Column("scope", chat_scope_enum, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("reported", sa.Boolean, nullable=False, server_default="false"),
    )
    op.create_index("ix_chat_messages_sender_driver_id", "chat_messages", ["sender_driver_id"])

    # ── announcements ─────────────────────────────────────────────────────────
    op.create_table(
        "announcements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "sent_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("target_type", announcement_target_enum, nullable=False),
        sa.Column("target_ids", postgresql.JSONB, nullable=True),
        sa.Column(
            "sent_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── incident_reports ──────────────────────────────────────────────────────
    op.create_table(
        "incident_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "driver_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drivers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("incident_type", incident_type_enum, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("photo_url", sa.String, nullable=True),
        sa.Column(
            "location",
            geoalchemy2.Geography(geometry_type="POINT", srid=4326),
            nullable=True,
        ),
        sa.Column(
            "reported_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_incident_reports_driver_id", "incident_reports", ["driver_id"])

    # ── defect_reports ────────────────────────────────────────────────────────
    op.create_table(
        "defect_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "driver_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drivers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vehicle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("vehicles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("defect_type", defect_type_enum, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("photo_url", sa.String, nullable=True),
        sa.Column(
            "reported_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("status", defect_status_enum, nullable=False, server_default="open"),
    )
    op.create_index("ix_defect_reports_driver_id", "defect_reports", ["driver_id"])
    op.create_index("ix_defect_reports_vehicle_id", "defect_reports", ["vehicle_id"])

    # ── audit_log_entries ─────────────────────────────────────────────────────
    op.create_table(
        "audit_log_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "admin_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("before_value", postgresql.JSONB, nullable=True),
        sa.Column("after_value", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_audit_log_admin_user_id", "audit_log_entries", ["admin_user_id"])
    op.create_index("ix_audit_log_entity_id", "audit_log_entries", ["entity_id"])
    op.create_index("ix_audit_log_created_at", "audit_log_entries", ["created_at"])

    # ── auth tokens ───────────────────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column(
            "driver_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drivers.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "admin_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin_users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("is_revoked", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])
    op.create_index("ix_refresh_tokens_driver_id", "refresh_tokens", ["driver_id"])

    op.create_table(
        "invite_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("driver_roles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "depot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("depots.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_used", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index("ix_invite_tokens_token_hash", "invite_tokens", ["token_hash"])
    op.create_index("ix_invite_tokens_email", "invite_tokens", ["email"])


def downgrade() -> None:
    # Drop in reverse FK order
    op.drop_table("invite_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("audit_log_entries")
    op.drop_table("defect_reports")
    op.drop_table("incident_reports")
    op.drop_table("announcements")
    op.drop_table("chat_messages")
    op.drop_table("location_pings")
    op.drop_table("deliveries")
    op.drop_table("shifts")
    op.drop_table("allocations")
    op.drop_table("drops")
    op.drop_table("routes")
    op.drop_table("driver_vehicle_assignments")
    op.drop_table("vehicles")
    op.drop_table("drivers")
    op.drop_table("admin_users")
    op.drop_table("depots")
    op.drop_table("driver_roles")

    # Drop enum types
    for enum_name in [
        "defect_status_enum", "defect_type_enum", "incident_type_enum",
        "admin_role_enum", "announcement_target_enum", "chat_scope_enum",
        "failure_reason_enum", "delivery_status_enum", "allocation_status_enum",
        "drop_status_enum", "drop_vehicle_class_enum", "route_status_enum",
        "vehicle_status_enum", "vehicle_type_enum", "driver_status_enum",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name};")
