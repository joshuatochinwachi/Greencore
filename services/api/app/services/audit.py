"""
Audit service — single reusable function for writing AuditLogEntry rows.

Section 8.1: "implement this as a single reusable service function,
not repeated per-endpoint, to guarantee nothing is missed."

Section 17.4: before_value / after_value contain ONLY the changed fields,
not the entire entity object.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.admin import AuditLogEntry


def log_audit_entry(
    db: Session,
    *,
    admin_user_id: str | None,
    entity_type: str,
    entity_id: str | uuid.UUID,
    before_value: dict[str, Any] | None = None,
    after_value: dict[str, Any] | None = None,
) -> AuditLogEntry:
    """
    Creates and adds an AuditLogEntry to the session. Does NOT commit —
    the caller's request cycle commits the transaction so the audit entry
    and the triggering change are atomic.

    Args:
        admin_user_id: UUID of the admin who made the change. None if the
                       action was triggered by the system (e.g. auto-close shift).
        entity_type:   String name of the affected table (e.g. "driver", "route").
        entity_id:     UUID of the specific row that changed.
        before_value:  Dict of {field: old_value} for changed fields only.
        after_value:   Dict of {field: new_value} for changed fields only.

    Returns:
        The AuditLogEntry instance (not yet committed).
    """
    entry = AuditLogEntry(
        admin_user_id=uuid.UUID(str(admin_user_id)) if admin_user_id else None,
        entity_type=entity_type,
        entity_id=uuid.UUID(str(entity_id)),
        before_value=before_value,
        after_value=after_value,
    )
    db.add(entry)
    return entry
