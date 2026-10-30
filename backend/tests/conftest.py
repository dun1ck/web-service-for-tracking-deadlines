"""Фикстуры pytest: изолированная БД (savepoint), in-memory KV и HTTP-клиент FastAPI."""

from __future__ import annotations

import os
import re
import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

# До импорта приложения — тестовый KV без Redis
os.environ.setdefault("KV_BACKEND", "memory")

from app.core.database import get_db  # noqa: E402
from app.core.kv_store import MemoryKVStore, get_kv_store  # noqa: E402
from app.main import app  # noqa: E402

API = "/api/v1"
DEFAULT_PASSWORD = "Passw0rd1"


def detail_code(response) -> str:
    body = response.json()
    d = body.get("detail")
    if isinstance(d, dict):
        return d.get("code", "")
    return ""


def detail_body(response) -> dict:
    d = response.json().get("detail")
    return d if isinstance(d, dict) else {}


@pytest.fixture(scope="session")
def engine():
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://deadline_user:deadline_secret_password@localhost:5432/deadline_tracker_db",
    )
    eng = create_engine(url, pool_pre_ping=True)
    return eng


@pytest.fixture()
def db_session(engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)
    connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess: Session, trans) -> None:
        if trans.nested and trans._parent and not trans._parent.nested:
            connection.begin_nested()

    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def kv_store() -> MemoryKVStore:
    return MemoryKVStore()


@pytest.fixture()
def client(db_session: Session, kv_store: MemoryKVStore) -> Generator[TestClient, None, None]:
    def override_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_kv_store] = lambda: kv_store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:12]}@test.bsu.by"


def register_starosta(client: TestClient, email: str, *, group_name: str | None = None) -> dict:
    payload = {
        "email": email,
        "full_name": "Петров Пётр Петрович",
        "password": DEFAULT_PASSWORD,
        "pdn_consent": True,
        "group_name": group_name or f"ГР-{uuid.uuid4().hex[:6].upper()}",
        "faculty": "ФКП",
        "course": 2,
        "academic_year": "2026/2027",
        "subgroups_count": 2,
    }
    response = client.post(f"{API}/auth/register/starosta", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    return {
        "email": email,
        "password": DEFAULT_PASSWORD,
        "user": data["user"],
        "group": data["group"],
        "invite_code": data["group"]["invite_code"],
    }


def register_student(
    client: TestClient,
    email: str,
    invite_code: str,
    *,
    pdn_consent: bool = True,
) -> dict:
    payload = {
        "invite_code": invite_code,
        "email": email,
        "full_name": "Иванов Иван Иванович",
        "password": DEFAULT_PASSWORD,
        "pdn_consent": pdn_consent,
    }
    response = client.post(f"{API}/auth/register", json=payload)
    return {"response": response, "payload": payload}


def login(client: TestClient, email: str, password: str = DEFAULT_PASSWORD, **extra) -> dict:
    body = {"email": email, "password": password, **extra}
    response = client.post(f"{API}/auth/login", json=body)
    return {"response": response, "body": body}


def auth_header(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def solve_captcha(client: TestClient) -> tuple[str, str]:
    captcha = client.get(f"{API}/auth/captcha").json()
    match = re.search(r"(\d+)\s*\+\s*(\d+)", captcha["question"])
    assert match, captcha["question"]
    answer = str(int(match.group(1)) + int(match.group(2)))
    return captcha["captcha_id"], answer
