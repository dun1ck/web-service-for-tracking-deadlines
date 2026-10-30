"""Зависимости FastAPI: текущий пользователь и разграничение прав (RBAC: Студент / Староста)."""

import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import TokenError, decode_access_token
from app.models import User

ROLE_STUDENT = "STUDENT"
ROLE_STAROSTA = "STAROSTA"

bearer_scheme = HTTPBearer(auto_error=False, description="JWT access-токен из /api/v1/auth/login")


def client_ip(request: Request) -> str:
    """IP клиента. За nginx берётся X-Real-IP (nginx перезаписывает его значением $remote_addr)."""
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "NOT_AUTHENTICATED", "message": message},
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Проверяет JWT и возвращает пользователя. Роль всегда берётся из БД, а не из токена."""
    if credentials is None:
        raise _unauthorized("Требуется авторизация")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(payload["sub"])
    except (TokenError, ValueError) as exc:
        raise _unauthorized("Токен недействителен или истёк") from exc

    user = db.get(User, user_id)
    if user is None or user.membership_status == "ARCHIVED":
        raise _unauthorized("Учётная запись недоступна")
    return user


def get_active_member(user: User = Depends(get_current_user)) -> User:
    """Доступ к данным группы есть только у подтверждённых участников."""
    if user.group_id is None or user.membership_status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "MEMBERSHIP_PENDING",
                "message": "Заявка на вступление в группу ещё не подтверждена старостой",
            },
        )
    return user


def require_roles(*roles: str) -> Callable[..., User]:
    """Фабрика зависимостей: пропускает только указанные роли."""

    def checker(user: User = Depends(get_active_member)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN_ROLE", "message": "Недостаточно прав для этого действия"},
            )
        return user

    return checker


require_starosta = require_roles(ROLE_STAROSTA)
