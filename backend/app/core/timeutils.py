"""Работа со временем в UTC."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Текущее время в UTC с указанием часового пояса."""
    return datetime.now(timezone.utc)


def as_aware(value: datetime | None) -> datetime | None:
    """Приводит дату к UTC-aware виду (некоторые драйверы БД возвращают naive-даты)."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
