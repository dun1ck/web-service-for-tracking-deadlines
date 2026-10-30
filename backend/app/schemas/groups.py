"""Схемы учебной группы, инвайт-кода и управления составом."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubgroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subgroup_number: int
    name: str


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    faculty: str | None
    course: int
    academic_year: str
    subgroups: list[SubgroupOut] = []


class GroupWithInviteOut(GroupOut):
    """Видна только старосте."""

    invite_code: str
    invite_expires_at: datetime
    invite_url_path: str


class InvitePreviewOut(BaseModel):
    """Публичная информация по инвайт-коду (до регистрации)."""

    valid: bool
    group_name: str | None = None
    faculty: str | None = None
    course: int | None = None
    academic_year: str | None = None
    reason: str | None = None


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    membership_status: str
    subgroup_id: uuid.UUID | None
    subgroup_number: int | None = None
    roster_number: int | None
    created_at: datetime | None = None


class ApproveMemberRequest(BaseModel):
    subgroup_number: int = Field(ge=1, le=4, examples=[1])
    roster_number: int | None = Field(
        default=None, ge=1, le=200, description="Номер в списке группы; если не указан — следующий свободный"
    )


class UpdateSubgroupRequest(BaseModel):
    subgroup_number: int = Field(ge=1, le=4)
