"""TC-REG-* и TC-AUTH-* — регистрация, JWT, refresh (блок 2 ТЗ)."""

from __future__ import annotations

import re

from sqlalchemy import select

from app.core.config import settings
from app.core.timeutils import utcnow
from app.models import AuthSession, Group, User
from tests.conftest import (
    API,
    DEFAULT_PASSWORD,
    auth_header,
    detail_body,
    detail_code,
    login,
    register_starosta,
    register_student,
    solve_captcha,
)


class TestRegistration:
    def test_tc_reg_01_starosta_creates_group_and_invite(self, client, unique_email):
        """TC-REG-01: староста ACTIVE, группа и инвайт GRP-XXXX-XXXX."""
        data = register_starosta(client, unique_email)
        assert data["user"]["membership_status"] == "ACTIVE"
        assert data["user"]["role"] == "STAROSTA"
        code = data["invite_code"]
        assert re.fullmatch(r"GRP-[A-Z2-9]{4}-[A-Z2-9]{4}", code)

    def test_tc_reg_02_student_by_valid_invite_pending(self, client, unique_email):
        """TC-REG-02: студент по инвайту → PENDING."""
        starosta = register_starosta(client, unique_email)
        student_email = unique_email.replace("@", "+student@")
        result = register_student(client, student_email, starosta["invite_code"])
        assert result["response"].status_code == 201
        assert result["response"].json()["user"]["membership_status"] == "PENDING"

    def test_tc_reg_03_pdn_consent_required(self, client, unique_email):
        """TC-REG-03: без согласия на ПДн → 400 PDN_CONSENT_REQUIRED."""
        starosta = register_starosta(client, unique_email)
        student_email = unique_email.replace("@", "+pdn@")
        result = register_student(
            client, student_email, starosta["invite_code"], pdn_consent=False
        )
        assert result["response"].status_code == 400
        assert detail_code(result["response"]) == "PDN_CONSENT_REQUIRED"

    def test_tc_reg_04_invalid_invite(self, client, unique_email):
        """TC-REG-04: неверный инвайт → INVITE_INVALID."""
        result = register_student(client, unique_email, "GRP-XXXX-YYYY")
        assert result["response"].status_code == 400
        assert detail_code(result["response"]) == "INVITE_INVALID"

    def test_tc_reg_04_expired_invite(self, client, db_session, unique_email):
        """TC-REG-04: просроченный инвайт → INVITE_INVALID."""
        starosta = register_starosta(client, unique_email)
        group = db_session.get(Group, starosta["group"]["id"])
        group.invite_expires_at = utcnow()
        db_session.flush()
        result = register_student(client, unique_email.replace("@", "+exp@"), starosta["invite_code"])
        assert result["response"].status_code == 400
        assert detail_code(result["response"]) == "INVITE_INVALID"

    def test_tc_reg_05_email_taken(self, client, unique_email):
        """TC-REG-05: повтор e-mail → 409 EMAIL_TAKEN."""
        register_starosta(client, unique_email)
        other = register_starosta(client, unique_email.replace("@", "+other@"))
        result = register_student(client, unique_email, other["invite_code"])
        assert result["response"].status_code == 409
        assert detail_code(result["response"]) == "EMAIL_TAKEN"


class TestAuthentication:
    def test_tc_auth_01_login_success(self, client, unique_email):
        """TC-AUTH-01: 200, access + refresh, срок access 30 мин."""
        register_starosta(client, unique_email)
        result = login(client, unique_email)
        assert result["response"].status_code == 200
        tokens = result["response"].json()
        assert "access_token" in tokens and "refresh_token" in tokens
        assert tokens["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    def test_tc_auth_02_me_with_bearer(self, client, unique_email):
        """TC-AUTH-02: GET /auth/me с access-токеном."""
        register_starosta(client, unique_email)
        tokens = login(client, unique_email)["response"].json()
        me = client.get(f"{API}/auth/me", headers=auth_header(tokens["access_token"]))
        assert me.status_code == 200
        assert me.json()["email"] == unique_email.lower()

    def test_tc_auth_03_refresh_rotates_tokens(self, client, unique_email):
        """TC-AUTH-03: refresh выдаёт новую пару, старый refresh отзывается."""
        register_starosta(client, unique_email)
        first = login(client, unique_email)["response"].json()
        old_refresh = first["refresh_token"]
        refreshed = client.post(f"{API}/auth/refresh", json={"refresh_token": old_refresh})
        assert refreshed.status_code == 200
        new_pair = refreshed.json()
        assert new_pair["refresh_token"] != old_refresh
        again = client.post(f"{API}/auth/refresh", json={"refresh_token": old_refresh})
        assert again.status_code == 401
        assert detail_code(again) == "REFRESH_INVALID"

    def test_tc_auth_04_refresh_reuse_revokes_all_sessions(self, client, db_session, unique_email):
        """TC-AUTH-04: повтор отозванного refresh закрывает все сессии пользователя."""
        register_starosta(client, unique_email)
        tokens = login(client, unique_email)["response"].json()
        client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        user_id = db_session.scalar(select(User.id).where(User.email == unique_email.lower()))
        active_before = db_session.scalars(
            select(AuthSession).where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
        ).all()
        assert len(active_before) >= 1
        reuse = client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert reuse.status_code == 401
        assert detail_code(reuse) == "REFRESH_INVALID"
        db_session.expire_all()
        active_after = db_session.scalars(
            select(AuthSession).where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
        ).all()
        assert len(active_after) == 0


class TestBruteforce:
    def test_tc_brute_01_first_four_failures_no_captcha(self, client, unique_email):
        """TC-BRUTE-01: 1–4 ошибки — INVALID_CREDENTIALS, captcha_required=false."""
        register_starosta(client, unique_email)
        for _ in range(4):
            result = login(client, unique_email, password="WrongPass1")
            assert result["response"].status_code == 401
            assert detail_code(result["response"]) == "INVALID_CREDENTIALS"
            assert detail_body(result["response"]).get("captcha_required") is False

    def test_tc_brute_02_fifth_failure_requires_captcha(self, client, unique_email):
        """TC-BRUTE-02: на 5-й ошибке captcha_required=true."""
        register_starosta(client, unique_email)
        for _ in range(4):
            login(client, unique_email, password="WrongPass1")
        fifth = login(client, unique_email, password="WrongPass1")
        assert fifth["response"].status_code == 401
        assert detail_body(fifth["response"]).get("captcha_required") is True

    def test_tc_brute_03_sixth_without_captcha_blocked(self, client, unique_email):
        """TC-BRUTE-03: 6-я попытка без captcha → CAPTCHA_REQUIRED."""
        register_starosta(client, unique_email)
        for _ in range(5):
            login(client, unique_email, password="WrongPass1")
        sixth = login(client, unique_email, password="WrongPass1")
        assert sixth["response"].status_code == 401
        assert detail_code(sixth["response"]) == "CAPTCHA_REQUIRED"

    def test_tc_brute_04_captcha_then_valid_password(self, client, unique_email):
        """TC-BRUTE-04: CAPTCHA + верный пароль → успешный вход."""
        register_starosta(client, unique_email)
        for _ in range(5):
            login(client, unique_email, password="WrongPass1")
        captcha_id, answer = solve_captcha(client)
        ok = login(
            client,
            unique_email,
            password=DEFAULT_PASSWORD,
            captcha_id=captcha_id,
            captcha_answer=answer,
        )
        assert ok["response"].status_code == 200

    def test_tc_brute_05_tenth_failure_locks_account(self, client, unique_email):
        """TC-BRUTE-05: 10 ошибок → 423 ACCOUNT_LOCKED, retry_after_seconds=900."""
        register_starosta(client, unique_email)
        last = None
        for _ in range(10):
            last = login(client, unique_email, password="WrongPass1")
        assert last is not None
        assert last["response"].status_code == 423
        body = detail_body(last["response"])
        assert body.get("code") == "ACCOUNT_LOCKED"
        assert body.get("retry_after_seconds") == settings.BRUTEFORCE_LOCKOUT_DURATION_SECONDS
