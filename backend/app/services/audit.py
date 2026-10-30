"""Запись событий в журнал аудита (п. 4.1.6 ТЗ)."""

import json
import uuid

from sqlalchemy.orm import Session

from app.models import AuditLog


def write_audit(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    actor_id: uuid.UUID | None = None,
    group_id: uuid.UUID | None = None,
    old_values: dict | None = None,
    new_values: dict | None = None,
    ip_address: str | None = None,
) -> None:
    """Добавляет запись в audit_log. Коммит выполняет вызывающий код вместе с основным изменением."""
    db.add(
        AuditLog(
            actor_id=actor_id,
            group_id=group_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_values=json.dumps(old_values, ensure_ascii=False, default=str) if old_values else None,
            new_values=json.dumps(new_values, ensure_ascii=False, default=str) if new_values else None,
            ip_address=ip_address if _is_ip(ip_address) else None,
        )
    )


def _is_ip(value: str | None) -> bool:
    import ipaddress

    if not value:
        return False
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True
