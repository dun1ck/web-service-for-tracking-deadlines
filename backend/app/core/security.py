"""Хэширование паролей (bcrypt), выпуск JWT access-токенов и refresh-токенов (п. 4.2.1 ТЗ)."""

import hashlib
import secrets
import uuid
from datetime import timedelta

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings
from app.core.timeutils import utcnow

# bcrypt обрабатывает не более 72 байт пароля
BCRYPT_MAX_PASSWORD_BYTES = 72

# Заранее посчитанный хэш для выравнивания времени ответа, когда пользователь не найден
_DUMMY_HASH = bcrypt.hashpw(b"timing-equalizer", bcrypt.gensalt(rounds=4))


class TokenError(Exception):
    """Невалидный или просроченный токен."""


def hash_password(password: str) -> str:
    """Хэширует пароль через bcrypt (cost = BCRYPT_ROUNDS, не менее 10)."""
    rounds = max(settings.BCRYPT_ROUNDS, 10)
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=rounds)).decode("ascii")


def verify_password(password: str, password_hash: str | None) -> bool:
    """Проверяет пароль. При отсутствии хэша всё равно выполняет bcrypt, чтобы не выдавать существование логина."""
    raw = password.encode("utf-8")[:BCRYPT_MAX_PASSWORD_BYTES]
    if not password_hash:
        bcrypt.checkpw(raw, _DUMMY_HASH)
        return False
    try:
        return bcrypt.checkpw(raw, password_hash.encode("ascii"))
    except ValueError:
        return False


def create_access_token(user_id: uuid.UUID, role: str, group_id: uuid.UUID | None) -> str:
    """Выпускает короткоживущий JWT access-токен."""
    now = utcnow()
    payload = {
        "sub": str(user_id),
        "role": role,
        "group_id": str(group_id) if group_id else None,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Проверяет подпись и срок действия access-токена."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise TokenError("Невалидный или просроченный токен") from exc
    if payload.get("type") != "access" or not payload.get("sub"):
        raise TokenError("Неверный тип токена")
    return payload


def generate_refresh_token() -> str:
    """Случайный непрозрачный refresh-токен (в БД хранится только его SHA-256)."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """SHA-256 от токена для хранения в таблице auth_sessions."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_invite_code() -> str:
    """Инвайт-код группы вида GRP-XXXX-XXXX (без похожих символов 0/O, 1/I)."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    part = lambda: "".join(secrets.choice(alphabet) for _ in range(4))  # noqa: E731
    return f"GRP-{part()}-{part()}"
