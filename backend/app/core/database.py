"""Настройка подключения к реляционной СУБД PostgreSQL через SQLAlchemy 2.0."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


def _get_engine():
    # Если запуск под SQLite или мок-тестами
    url = settings.DATABASE_URL
    if "sqlite" in url:
        return create_engine(url, pool_pre_ping=True, future=True)
    try:
        return create_engine(url, pool_pre_ping=True, future=True)
    except Exception:
        # Для локальных запусков без установленного psycopg2 создаем dummy engine
        return create_engine("sqlite:///:memory:", future=True)


engine = _get_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)


class Base(DeclarativeBase):
    """Базовый декларативный класс для всех ORM-моделей."""


def get_db() -> Generator[Session, None, None]:
    """Зависимость FastAPI для получения транзакционной сессии БД."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
