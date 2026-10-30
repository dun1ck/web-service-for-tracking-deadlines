"""Ступенчатая защита от подбора пароля (п. 4.2.2 ТЗ).

Правила (окно наблюдения BRUTEFORCE_WINDOW_SECONDS = 15 минут):
* 5 неудачных попыток для логина  -> следующая попытка входа требует CAPTCHA;
* 10 неудачных попыток для логина -> вход блокируется на 15 минут;
* 20 неудачных попыток с одного IP (по любым логинам) -> CAPTCHA для этого IP.

Счётчик ведётся по логину, а не по паре «IP + логин», чтобы смена IP-адреса не обнуляла защиту.
Для несуществующих логинов правила те же — так ответ не раскрывает, зарегистрирован ли e-mail.
"""

import secrets
import uuid
from dataclasses import dataclass

from app.core.config import settings
from app.core.kv_store import KVStore
from app.core.security import hash_token


def _login_key(login: str) -> str:
    return f"auth:fail:login:{login.strip().lower()}"


def _ip_key(ip: str) -> str:
    return f"auth:fail:ip:{ip}"


def _lock_key(login: str) -> str:
    return f"auth:lock:{login.strip().lower()}"


def _captcha_key(captcha_id: str) -> str:
    return f"auth:captcha:{captcha_id}"


@dataclass
class LoginGuardState:
    failed_attempts: int
    captcha_required: bool
    locked_seconds_left: int


class LoginGuard:
    def __init__(self, store: KVStore) -> None:
        self.store = store

    def state(self, login: str, ip: str) -> LoginGuardState:
        attempts = int(self.store.get(_login_key(login)) or 0)
        ip_attempts = int(self.store.get(_ip_key(ip)) or 0)
        return LoginGuardState(
            failed_attempts=attempts,
            captcha_required=(
                attempts >= settings.BRUTEFORCE_CAPTCHA_THRESHOLD
                or ip_attempts >= settings.BRUTEFORCE_IP_THRESHOLD
            ),
            locked_seconds_left=self.store.ttl(_lock_key(login)),
        )

    def register_failure(self, login: str, ip: str) -> LoginGuardState:
        window = settings.BRUTEFORCE_WINDOW_SECONDS
        attempts = self.store.incr(_login_key(login), window)
        self.store.incr(_ip_key(ip), window)
        if attempts >= settings.BRUTEFORCE_LOCKOUT_THRESHOLD:
            self.store.set(_lock_key(login), "1", settings.BRUTEFORCE_LOCKOUT_DURATION_SECONDS)
            # После блокировки счётчик начинается заново, но CAPTCHA остаётся обязательной
            self.store.set(
                _login_key(login), str(settings.BRUTEFORCE_CAPTCHA_THRESHOLD), window
            )
        return self.state(login, ip)

    def register_success(self, login: str) -> None:
        self.store.delete(_login_key(login), _lock_key(login))

    # ---------------- CAPTCHA ----------------

    def issue_captcha(self) -> tuple[str, str]:
        """Простая арифметическая CAPTCHA без внешних сервисов. Ответ хранится в виде хэша."""
        a, b = secrets.randbelow(9) + 1, secrets.randbelow(9) + 1
        captcha_id = uuid.uuid4().hex
        self.store.set(_captcha_key(captcha_id), hash_token(str(a + b)), settings.CAPTCHA_TTL_SECONDS)
        return captcha_id, f"Сколько будет {a} + {b}?"

    def check_captcha(self, captcha_id: str | None, answer: str | None) -> bool:
        """Одноразовая проверка: после любой попытки CAPTCHA удаляется."""
        if not captcha_id or answer is None:
            return False
        key = _captcha_key(captcha_id)
        expected = self.store.get(key)
        self.store.delete(key)
        return expected is not None and secrets.compare_digest(expected, hash_token(answer.strip()))
