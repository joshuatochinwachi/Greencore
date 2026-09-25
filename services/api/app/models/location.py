"""
LocationPing model — Section 8.

LOCATION_PING rows are only ever inserted while a SHIFT has no end_time.
This constraint is enforced at the application layer in the location WebSocket
handler, not by a DB constraint (which would require a trigger). Section 8.1
is explicit: "enforce this at the application layer."

Retention: rows older than settings.location_data_retention_days are purged by
a scheduled background job (Phase 1 background task). The retention period is
a [CONFIRM] value per Section 12 Q3.
"""

import uuid

from geoalchemy2 import Geography
from sqlalchemy import Column, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import TIMESTAMP

from app.database import Base


class LocationPing(Base):
    __tablename__ = "location_pings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shift_id = Column(
        UUID(as_uuid=True),
        ForeignKey("shifts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    location = Column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )
    recorded_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,  # index for retention-period sweep query
    )

    shift = relationship("Shift", back_populates="location_pings")
