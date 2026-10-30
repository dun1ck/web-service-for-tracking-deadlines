"""Вспомогательная логика учебных групп и инвайт-кодов."""

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import generate_invite_code
from app.core.timeutils import as_aware, utcnow
from app.models import Group, Subgroup, User
from app.schemas.groups import GroupOut, GroupWithInviteOut, SubgroupOut


def new_unique_invite_code(db: Session) -> str:
    """Генерирует инвайт-код, которого ещё нет в БД."""
    while True:
        code = generate_invite_code()
        if db.scalar(select(Group.id).where(Group.invite_code == code)) is None:
            return code


def invite_expiry():
    return utcnow() + timedelta(days=settings.INVITE_CODE_TTL_DAYS)


def find_group_by_invite(db: Session, code: str) -> tuple[Group | None, str | None]:
    """Возвращает (группа, причина_отказа)."""
    group = db.scalar(select(Group).where(Group.invite_code == code.strip().upper()))
    if group is None:
        return None, "Инвайт-код не найден"
    if as_aware(group.invite_expires_at) <= utcnow():
        return None, "Срок действия инвайт-кода истёк — попросите старосту выпустить новый"
    return group, None


def list_subgroups(db: Session, group_id) -> list[Subgroup]:
    return list(
        db.scalars(select(Subgroup).where(Subgroup.group_id == group_id).order_by(Subgroup.subgroup_number))
    )


def get_subgroup_by_number(db: Session, group_id, number: int) -> Subgroup | None:
    return db.scalar(
        select(Subgroup).where(Subgroup.group_id == group_id, Subgroup.subgroup_number == number)
    )


def next_roster_number(db: Session, group_id) -> int:
    """Следующий номер в списке. Номера исключённых студентов не переиспользуются."""
    current = db.scalar(select(func.max(User.roster_number)).where(User.group_id == group_id))
    return (current or 0) + 1


def group_out(db: Session, group: Group, *, with_invite: bool = False) -> GroupOut:
    subgroups = [SubgroupOut.model_validate(s) for s in list_subgroups(db, group.id)]
    base = {
        "id": group.id,
        "name": group.name,
        "faculty": group.faculty,
        "course": group.course,
        "academic_year": group.academic_year,
        "subgroups": subgroups,
    }
    if with_invite:
        return GroupWithInviteOut(
            **base,
            invite_code=group.invite_code,
            invite_expires_at=as_aware(group.invite_expires_at),
            invite_url_path=f"/register/{group.invite_code}",
        )
    return GroupOut(**base)
