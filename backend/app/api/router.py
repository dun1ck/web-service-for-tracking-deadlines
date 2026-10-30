"""Маршруты REST API (v1)."""

from fastapi import APIRouter

from app.api.routes import auth, groups
from app.core.config import settings
from app.models import Base

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(groups.router)


@api_router.get("/health", tags=["Система и Мониторинг"], summary="Проверка состояния сервиса (Healthcheck)")
def healthcheck() -> dict:
    """Возвращает статус работоспособности REST API и количество зарегистрированных таблиц ORM."""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "environment": settings.APP_ENV,
        "orm_tables_registered": len(Base.metadata.tables),
        "tables": sorted(Base.metadata.tables.keys()),
    }
