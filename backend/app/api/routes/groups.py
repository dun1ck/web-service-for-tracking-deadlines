"""Учебная группа: инвайт-коды и управление составом (доступно старосте)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.deps import ROLE_STAROSTA, ROLE_STUDENT, client_ip, get_active_member, require_starosta
from app.core.database import get_db
from app.core.timeutils import utcnow
from app.models import AuthSession, Group, Subgroup, User
from app.schemas.groups import (
    ApproveMemberRequest,
    GroupOut,
    GroupWithInviteOut,
    InvitePreviewOut,
    MemberOut,
    UpdateSubgroupRequest,
)
from app.services.audit import write_audit
from app.services.groups import (
    find_group_by_invite,
    get_subgroup_by_number,
    group_out,
    invite_expiry,
    new_unique_invite_code,
    next_roster_number,
)

router = APIRouter(prefix="/groups", tags=["Авторизация и Группы (RBAC)"])

MEMBER_STATUSES = {"PENDING", "ACTIVE", "ARCHIVED"}


def _error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _member_out(user: User, subgroups: dict[uuid.UUID, int]) -> MemberOut:
    out = MemberOut.model_validate(user)
    out.subgroup_number = subgroups.get(user.subgroup_id) if user.subgroup_id else None
    return out


def _subgroup_numbers(db: Session, group_id: uuid.UUID) -> dict[uuid.UUID, int]:
    rows = db.execute(select(Subgroup.id, Subgroup.subgroup_number).where(Subgroup.group_id == group_id))
    return {row.id: row.subgroup_number for row in rows}


def _get_student_in_group(db: Session, starosta: User, member_id: uuid.UUID) -> User:
    member = db.get(User, member_id)
    if member is None or member.group_id != starosta.group_id:
        raise _error(status.HTTP_404_NOT_FOUND, "MEMBER_NOT_FOUND", "Участник не найден в вашей группе")
    if member.role != ROLE_STUDENT:
        raise _error(status.HTTP_400_BAD_REQUEST, "NOT_A_STUDENT", "Действие применимо только к студентам")
    return member


def _resolve_subgroup(db: Session, group_id: uuid.UUID, number: int) -> Subgroup:
    subgroup = get_subgroup_by_number(db, group_id, number)
    if subgroup is None:
        raise _error(status.HTTP_400_BAD_REQUEST, "SUBGROUP_NOT_FOUND", f"Подгруппа {number} не существует")
    return subgroup


@router.get(
    "/invite/{invite_code}",
    response_model=InvitePreviewOut,
    summary="Проверить инвайт-код (публично, до регистрации)",
)
def preview_invite(invite_code: str, db: Session = Depends(get_db)) -> InvitePreviewOut:
    group, reason = find_group_by_invite(db, invite_code)
    if group is None:
        return InvitePreviewOut(valid=False, reason=reason)
    return InvitePreviewOut(
        valid=True,
        group_name=group.name,
        faculty=group.faculty,
        course=group.course,
        academic_year=group.academic_year,
    )


@router.get(
    "/me",
    response_model=GroupWithInviteOut | GroupOut,
    summary="Моя группа (инвайт-код виден только старосте)",
)
def my_group(user: User = Depends(get_active_member), db: Session = Depends(get_db)):
    group = db.get(Group, user.group_id)
    return group_out(db, group, with_invite=user.role == ROLE_STAROSTA)


@router.post(
    "/me/invite/regenerate",
    response_model=GroupWithInviteOut,
    summary="Перевыпустить инвайт-код (старый перестаёт действовать)",
)
def regenerate_invite(
    request: Request, starosta: User = Depends(require_starosta), db: Session = Depends(get_db)
) -> GroupWithInviteOut:
    group = db.get(Group, starosta.group_id)
    old_code = group.invite_code
    group.invite_code = new_unique_invite_code(db)
    group.invite_expires_at = invite_expiry()
    write_audit(db, action="INVITE_REGENERATED", entity_type="group", entity_id=group.id,
                actor_id=starosta.id, group_id=group.id, ip_address=client_ip(request),
                old_values={"invite_code": old_code[:4] + "…"})
    db.commit()
    db.refresh(group)
    return group_out(db, group, with_invite=True)


@router.get("/me/members", response_model=list[MemberOut], summary="Состав группы и заявки на вступление")
def list_members(
    status_filter: str | None = Query(default=None, alias="status", description="PENDING / ACTIVE / ARCHIVED"),
    starosta: User = Depends(require_starosta),
    db: Session = Depends(get_db),
) -> list[MemberOut]:
    query = select(User).where(User.group_id == starosta.group_id)
    if status_filter:
        value = status_filter.upper()
        if value not in MEMBER_STATUSES:
            raise _error(status.HTTP_400_BAD_REQUEST, "BAD_STATUS", "Допустимо: PENDING, ACTIVE, ARCHIVED")
        query = query.where(User.membership_status == value)
    users = db.scalars(query.order_by(User.membership_status, User.roster_number, User.full_name)).all()
    subgroups = _subgroup_numbers(db, starosta.group_id)
    return [_member_out(u, subgroups) for u in users]


@router.post(
    "/me/members/{member_id}/approve",
    response_model=MemberOut,
    summary="Подтвердить заявку студента и распределить в подгруппу",
)
def approve_member(
    member_id: uuid.UUID,
    payload: ApproveMemberRequest,
    request: Request,
    starosta: User = Depends(require_starosta),
    db: Session = Depends(get_db),
) -> MemberOut:
    member = _get_student_in_group(db, starosta, member_id)
    if member.membership_status != "PENDING":
        raise _error(status.HTTP_409_CONFLICT, "NOT_PENDING", "Заявка уже обработана")
    subgroup = _resolve_subgroup(db, starosta.group_id, payload.subgroup_number)

    roster = payload.roster_number or next_roster_number(db, starosta.group_id)
    taken = db.scalar(
        select(User.id).where(
            User.group_id == starosta.group_id,
            User.membership_status != "PENDING",
            User.roster_number == roster,
        )
    )
    if taken is not None:
        raise _error(status.HTTP_409_CONFLICT, "ROSTER_TAKEN", f"Номер {roster} в списке группы уже занят")

    member.membership_status = "ACTIVE"
    member.subgroup_id = subgroup.id
    member.roster_number = roster
    write_audit(db, action="MEMBER_APPROVED", entity_type="user", entity_id=member.id,
                actor_id=starosta.id, group_id=starosta.group_id, ip_address=client_ip(request),
                new_values={"subgroup": subgroup.subgroup_number, "roster_number": roster})
    db.commit()
    db.refresh(member)
    return _member_out(member, _subgroup_numbers(db, starosta.group_id))


@router.post(
    "/me/members/{member_id}/reject",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Отклонить заявку (учётная запись удаляется, e-mail освобождается)",
)
def reject_member(
    member_id: uuid.UUID,
    request: Request,
    starosta: User = Depends(require_starosta),
    db: Session = Depends(get_db),
) -> None:
    member = _get_student_in_group(db, starosta, member_id)
    if member.membership_status != "PENDING":
        raise _error(status.HTTP_409_CONFLICT, "NOT_PENDING", "Отклонить можно только необработанную заявку")
    write_audit(db, action="MEMBER_REJECTED", entity_type="user", entity_id=member.id,
                actor_id=starosta.id, group_id=starosta.group_id, ip_address=client_ip(request),
                old_values={"email": member.email, "full_name": member.full_name})
    db.delete(member)
    db.commit()


@router.patch(
    "/me/members/{member_id}/subgroup",
    response_model=MemberOut,
    summary="Перевести студента в другую подгруппу",
)
def change_subgroup(
    member_id: uuid.UUID,
    payload: UpdateSubgroupRequest,
    request: Request,
    starosta: User = Depends(require_starosta),
    db: Session = Depends(get_db),
) -> MemberOut:
    member = _get_student_in_group(db, starosta, member_id)
    if member.membership_status != "ACTIVE":
        raise _error(status.HTTP_409_CONFLICT, "NOT_ACTIVE", "Студент не является активным участником группы")
    subgroup = _resolve_subgroup(db, starosta.group_id, payload.subgroup_number)
    numbers = _subgroup_numbers(db, starosta.group_id)
    old = numbers.get(member.subgroup_id) if member.subgroup_id else None
    member.subgroup_id = subgroup.id
    write_audit(db, action="MEMBER_SUBGROUP_CHANGED", entity_type="user", entity_id=member.id,
                actor_id=starosta.id, group_id=starosta.group_id, ip_address=client_ip(request),
                old_values={"subgroup": old}, new_values={"subgroup": subgroup.subgroup_number})
    db.commit()
    db.refresh(member)
    return _member_out(member, numbers)


@router.post(
    "/me/members/{member_id}/archive",
    response_model=MemberOut,
    summary="Исключить студента из группы (запись сохраняется в архиве, сессии закрываются)",
)
def archive_member(
    member_id: uuid.UUID,
    request: Request,
    starosta: User = Depends(require_starosta),
    db: Session = Depends(get_db),
) -> MemberOut:
    member = _get_student_in_group(db, starosta, member_id)
    if member.membership_status != "ACTIVE":
        raise _error(status.HTTP_409_CONFLICT, "NOT_ACTIVE", "Студент не является активным участником группы")
    member.membership_status = "ARCHIVED"
    # Номер в списке и варианты не освобождаются — у остальных студентов ничего не «съезжает»
    db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == member.id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )
    write_audit(db, action="MEMBER_ARCHIVED", entity_type="user", entity_id=member.id,
                actor_id=starosta.id, group_id=starosta.group_id, ip_address=client_ip(request))
    db.commit()
    db.refresh(member)
    return _member_out(member, _subgroup_numbers(db, starosta.group_id))
