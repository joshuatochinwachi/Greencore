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


from datetime import datetime


def _serialize_value(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, (uuid.UUID, datetime)):
        return str(val)
    if isinstance(val, dict):
        return {k: _serialize_value(v) for k, v in val.items()}
    if isinstance(val, (list, tuple, set)):
        return [_serialize_value(v) for v in val]
    return val


def log_audit_entry(
    db: Session,
    *,
    admin_user_id: str | None,
    entity_type: str,
    entity_id: str | uuid.UUID,
    before_value: dict[str, Any] | None = None,
    after_value: dict[str, Any] | None = None,
) -> AuditLogEntry:
    entry = AuditLogEntry(
        admin_user_id=uuid.UUID(str(admin_user_id)) if admin_user_id else None,
        entity_type=entity_type,
        entity_id=uuid.UUID(str(entity_id)),
        before_value=_serialize_value(before_value),
        after_value=_serialize_value(after_value),
    )
    db.add(entry)
    return entry


record_audit_event = log_audit_entry
