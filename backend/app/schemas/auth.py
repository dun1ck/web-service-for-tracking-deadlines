"""Схемы авторизации, регистрации и профиля пользователя."""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import BCRYPT_MAX_PASSWORD_BYTES


def _validate_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Пароль должен содержать не менее 8 символов")
    if len(value.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError("Пароль слишком длинный (не более 72 байт)")
    if not re.search(r"[A-Za-zА-Яа-яЁё]", value) or not re.search(r"\d", value):
        raise ValueError("Пароль должен содержать хотя бы одну букву и одну цифру")
    return value


def _validate_full_name(value: str) -> str:
    value = " ".join(value.split())
    if len(value) < 3:
        raise ValueError("Укажите ФИО полностью")
    return value


class StudentRegisterRequest(BaseModel):
    """Регистрация студента по инвайт-коду группы (п. 4.2.1.1 ТЗ)."""

    invite_code: str = Field(min_length=4, max_length=64, examples=["GRP-7KQ2-M9XA"])
    email: EmailStr = Field(examples=["ivanov@student.bsu.by"])
    full_name: str = Field(max_length=150, examples=["Иванов Иван Иванович"])
    password: str = Field(examples=["Passw0rd!"])
    pdn_consent: bool = Field(description="Согласие на обработку ПДн (Закон РБ № 99-З)")

    check_password = field_validator("password")(_validate_password)
    check_full_name = field_validator("full_name")(_validate_full_name)

    @field_validator("invite_code")
    @classmethod
    def normalize_invite_code(cls, value: str) -> str:
        return value.strip().upper()


class StarostaRegisterRequest(BaseModel):
    """Регистрация старосты одновременно с созданием учебной группы."""

    email: EmailStr = Field(examples=["starosta@student.bsu.by"])
    full_name: str = Field(max_length=150, examples=["Петров Пётр Петрович"])
    password: str = Field(examples=["Passw0rd!"])
    pdn_consent: bool
    group_name: str = Field(min_length=2, max_length=50, examples=["ПО-21"])
    faculty: str | None = Field(default=None, max_length=150, examples=["ФКП"])
    course: int = Field(default=1, ge=1, le=6)
    academic_year: str = Field(min_length=4, max_length=20, examples=["2026/2027"])
    subgroups_count: int = Field(default=2, ge=1, le=4)

    check_password = field_validator("password")(_validate_password)
    check_full_name = field_validator("full_name")(_validate_full_name)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)
    captcha_id: str | None = Field(default=None, description="Обязателен после 5 неудачных попыток")
    captcha_answer: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Срок жизни access-токена, секунды")


class CaptchaResponse(BaseModel):
    captcha_id: str
    question: str
    expires_in: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    membership_status: str
    group_id: uuid.UUID | None
    subgroup_id: uuid.UUID | None
    roster_number: int | None
    pdn_consent_given: bool
    created_at: datetime | None = None


class RegisterResponse(BaseModel):
    user: UserOut
    message: str
