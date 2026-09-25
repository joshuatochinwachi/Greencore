"""
ORM models package.

Import order matters for Alembic autogenerate — import all model modules here
so that Base.metadata is fully populated before alembic inspects it.
"""

from app.models.admin import AdminUser, AuditLogEntry  # noqa: F401
from app.models.announcement import Announcement  # noqa: F401
from app.models.auth import RefreshToken, InviteToken  # noqa: F401
from app.models.delivery import Delivery  # noqa: F401
from app.models.driver import Driver, DriverRole  # noqa: F401
from app.models.incident import DefectReport, IncidentReport  # noqa: F401
from app.models.location import LocationPing  # noqa: F401
from app.models.message import ChatMessage  # noqa: F401
from app.models.route import Allocation, Drop, Route, Shift  # noqa: F401
from app.models.vehicle import DriverVehicleAssignment, Vehicle  # noqa: F401
