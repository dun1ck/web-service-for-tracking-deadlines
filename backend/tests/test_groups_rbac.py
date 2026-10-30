"""TC-RBAC-* — роли, инвайты, модерация состава группы (блок 2 ТЗ)."""

from __future__ import annotations

from sqlalchemy import select

from app.models import AuthSession, User
from tests.conftest import (
    API,
    auth_header,
    detail_code,
    login,
    register_starosta,
    register_student,
)


def _tokens(client, email: str) -> dict:
    return login(client, email)["response"].json()


class TestGroupsRbac:
    def test_tc_rbac_01_pending_cannot_access_group(self, client, unique_email):
        """TC-RBAC-01: PENDING → GET /groups/me → MEMBERSHIP_PENDING."""
        starosta = register_starosta(client, unique_email)
        student_email = unique_email.replace("@", "+pending@")
        reg = register_student(client, student_email, starosta["invite_code"])
        assert reg["response"].status_code == 201
        tokens = _tokens(client, student_email)
        response = client.get(f"{API}/groups/me", headers=auth_header(tokens["access_token"]))
        assert response.status_code == 403
        assert detail_code(response) == "MEMBERSHIP_PENDING"

    def test_tc_rbac_02_starosta_approves_student(self, client, unique_email):
        """TC-RBAC-02: approve → ACTIVE, подгруппа и roster."""
        starosta = register_starosta(client, unique_email)
        student_email = unique_email.replace("@", "+approve@")
        student = register_student(client, student_email, starosta["invite_code"])["response"].json()
        starosta_tokens = _tokens(client, unique_email)
        member_id = student["user"]["id"]
        approved = client.post(
            f"{API}/groups/me/members/{member_id}/approve",
            json={"subgroup_number": 1, "roster_number": 1},
            headers=auth_header(starosta_tokens["access_token"]),
        )
        assert approved.status_code == 200
        body = approved.json()
        assert body["membership_status"] == "ACTIVE"
        assert body["subgroup_number"] == 1
        assert body["roster_number"] == 1
        group_me = client.get(
            f"{API}/groups/me", headers=auth_header(_tokens(client, student_email)["access_token"])
        )
        assert group_me.status_code == 200

    def test_tc_rbac_03_student_forbidden_starosta_endpoints(self, client, unique_email):
        """TC-RBAC-03: студент не может regenerate / members."""
        starosta = register_starosta(client, unique_email)
        student_email = unique_email.replace("@", "+student@")
        student = register_student(client, student_email, starosta["invite_code"])["response"].json()
        starosta_tokens = _tokens(client, unique_email)
        client.post(
            f"{API}/groups/me/members/{student['user']['id']}/approve",
            json={"subgroup_number": 1, "roster_number": 2},
            headers=auth_header(starosta_tokens["access_token"]),
        )
        student_tokens = _tokens(client, student_email)
        headers = auth_header(student_tokens["access_token"])
        regen = client.post(f"{API}/groups/me/invite/regenerate", headers=headers)
        assert regen.status_code == 403
        assert detail_code(regen) == "FORBIDDEN_ROLE"
        members = client.get(f"{API}/groups/me/members", headers=headers)
        assert members.status_code == 403
        assert detail_code(members) == "FORBIDDEN_ROLE"

    def test_tc_rbac_04_regenerate_invite_invalidates_old(self, client, unique_email):
        """TC-RBAC-04: старый код invalid, новый valid."""
        starosta = register_starosta(client, unique_email)
        old_code = starosta["invite_code"]
        tokens = _tokens(client, unique_email)
        regen = client.post(
            f"{API}/groups/me/invite/regenerate",
            headers=auth_header(tokens["access_token"]),
        )
        assert regen.status_code == 200
        new_code = regen.json()["invite_code"]
        assert new_code != old_code
        old_preview = client.get(f"{API}/groups/invite/{old_code}")
        assert old_preview.json()["valid"] is False
        new_preview = client.get(f"{API}/groups/invite/{new_code}")
        assert new_preview.json()["valid"] is True

    def test_tc_rbac_05_archive_revokes_sessions_keeps_roster(
        self, client, db_session, unique_email
    ):
        """TC-RBAC-05: ARCHIVED, сессии отозваны, roster_number сохранён."""
        starosta = register_starosta(client, unique_email)
        student_email = unique_email.replace("@", "+archive@")
        student = register_student(client, student_email, starosta["invite_code"])["response"].json()
        starosta_tokens = _tokens(client, unique_email)
        member_id = student["user"]["id"]
        client.post(
            f"{API}/groups/me/members/{member_id}/approve",
            json={"subgroup_number": 1, "roster_number": 5},
            headers=auth_header(starosta_tokens["access_token"]),
        )
        assert _tokens(client, student_email)["access_token"]
        archived = client.post(
            f"{API}/groups/me/members/{member_id}/archive",
            headers=auth_header(starosta_tokens["access_token"]),
        )
        assert archived.status_code == 200
        assert archived.json()["membership_status"] == "ARCHIVED"
        assert archived.json()["roster_number"] == 5
        db_session.expire_all()
        sessions = db_session.scalars(
            select(AuthSession).where(
                AuthSession.user_id == member_id, AuthSession.revoked_at.is_(None)
            )
        ).all()
        assert len(sessions) == 0
        user = db_session.get(User, member_id)
        assert user.roster_number == 5
