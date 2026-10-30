"""Авторизация: регистрация, вход (JWT + bcrypt), refresh-токены, CAPTCHA и защита от брутфорса."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import ROLE_STAROSTA, ROLE_STUDENT, client_ip, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.kv_store import KVStore, get_kv_store
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.core.timeutils import as_aware, utcnow
from app.models import AuthSession, Group, Subgroup, User
from app.schemas.auth import (
    CaptchaResponse,
    LoginRequest,
    RefreshRequest,
    RegisterResponse,
    StarostaRegisterRequest,
    StudentRegisterRequest,
    TokenPair,
    UserOut,
)
from app.schemas.groups import GroupWithInviteOut
from app.services.audit import write_audit
from app.services.bruteforce import LoginGuard
from app.services.groups import find_group_by_invite, group_out, invite_expiry, new_unique_invite_code

router = APIRouter(prefix="/auth", tags=["Авторизация и Группы (RBAC)"])


class StarostaRegisterResponse(BaseModel):
    user: UserOut
    group: GroupWithInviteOut
    message: str


def _error(status_code: int, code: str, message: str, **extra) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message, **extra})


def _require_consent(consent: bool) -> None:
    if not consent:
        raise _error(
            status.HTTP_400_BAD_REQUEST,
            "PDN_CONSENT_REQUIRED",
            "Необходимо согласие на обработку персональных данных (Закон РБ № 99-З)",
        )


def _ensure_email_free(db: Session, email: str) -> None:
    if db.scalar(select(User.id).where(User.email == email)) is not None:
        raise _error(status.HTTP_409_CONFLICT, "EMAIL_TAKEN", "Пользователь с таким e-mail уже зарегистрирован")


def _issue_tokens(db: Session, user: User, request: Request) -> TokenPair:
    refresh = generate_refresh_token()
    db.add(
        AuthSession(
            user_id=user.id,
            token_hash=hash_token(refresh),
            token_type="REFRESH",
            ip_address=_safe_ip(client_ip(request)),
            user_agent=(request.headers.get("user-agent") or "")[:500] or None,
            expires_at=utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    return TokenPair(
        access_token=create_access_token(user.id, user.role, user.group_id),
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def _safe_ip(value: str) -> str | None:
    import ipaddress

    try:
        ipaddress.ip_address(value)
    except ValueError:
        return None
    return value


# ----------------------------------------------------------------------------- регистрация


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация студента по инвайт-коду группы",
)
def register_student(payload: StudentRegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    """Студент сам регистрируется по коду от старосты. Заявка получает статус PENDING до подтверждения."""
    _require_consent(payload.pdn_consent)
    group, reason = find_group_by_invite(db, payload.invite_code)
    if group is None:
        raise _error(status.HTTP_400_BAD_REQUEST, "INVITE_INVALID", reason)

    email = payload.email.lower()
    _ensure_email_free(db, email)
    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=ROLE_STUDENT,
        group_id=group.id,
        membership_status="PENDING",
        pdn_consent_given=True,
        pdn_consent_at=utcnow(),
    )
    db.add(user)
    try:
        db.flush()
        write_audit(db, action="MEMBER_JOIN_REQUEST", entity_type="user", entity_id=user.id,
                    actor_id=user.id, group_id=group.id, new_values={"email": email})
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _error(status.HTTP_409_CONFLICT, "EMAIL_TAKEN", "Пользователь с таким e-mail уже зарегистрирован") from exc
    db.refresh(user)
    return RegisterResponse(
        user=UserOut.model_validate(user),
        message=f"Заявка в группу «{group.name}» отправлена. Дождитесь подтверждения старосты.",
    )


@router.post(
    "/register/starosta",
    response_model=StarostaRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация старосты и создание учебной группы",
)
def register_starosta(payload: StarostaRegisterRequest, db: Session = Depends(get_db)) -> StarostaRegisterResponse:
    """Создаёт группу с подгруппами, учётную запись старосты (сразу ACTIVE) и выпускает инвайт-код."""
    _require_consent(payload.pdn_consent)
    email = payload.email.lower()
    _ensure_email_free(db, email)

    exists = db.scalar(
        select(Group.id).where(Group.name == payload.group_name, Group.academic_year == payload.academic_year)
    )
    if exists is not None:
        raise _error(status.HTTP_409_CONFLICT, "GROUP_EXISTS", "Группа с таким названием и учебным годом уже существует")

    group = Group(
        name=payload.group_name.strip(),
        faculty=payload.faculty,
        course=payload.course,
        academic_year=payload.academic_year.strip(),
        invite_code=new_unique_invite_code(db),
        invite_expires_at=invite_expiry(),
    )
    db.add(group)
    db.flush()
    for number in range(1, payload.subgroups_count + 1):
        db.add(Subgroup(group_id=group.id, subgroup_number=number, name=f"Подгруппа {number}"))

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=ROLE_STAROSTA,
        group_id=group.id,
        membership_status="ACTIVE",
        roster_number=None,
        pdn_consent_given=True,
        pdn_consent_at=utcnow(),
    )
    db.add(user)
    try:
        db.flush()
        write_audit(db, action="GROUP_CREATED", entity_type="group", entity_id=group.id,
                    actor_id=user.id, group_id=group.id, new_values={"name": group.name})
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _error(status.HTTP_409_CONFLICT, "CONFLICT", "Группа или e-mail уже существуют") from exc
    db.refresh(user)
    return StarostaRegisterResponse(
        user=UserOut.model_validate(user),
        group=group_out(db, group, with_invite=True),
        message="Группа создана. Отправьте студентам инвайт-код или ссылку для регистрации.",
    )


# ----------------------------------------------------------------------------- вход


@router.get("/captcha", response_model=CaptchaResponse, summary="Получить CAPTCHA для входа")
def get_captcha(store: KVStore = Depends(get_kv_store)) -> CaptchaResponse:
    captcha_id, question = LoginGuard(store).issue_captcha()
    return CaptchaResponse(captcha_id=captcha_id, question=question, expires_in=settings.CAPTCHA_TTL_SECONDS)


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Вход по e-mail и паролю (5 ошибок → CAPTCHA, 10 ошибок → блокировка на 15 минут)",
    responses={
        401: {"description": "Неверный логин/пароль, требуется или неверна CAPTCHA"},
        423: {"description": "Учётная запись временно заблокирована"},
    },
)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    store: KVStore = Depends(get_kv_store),
) -> TokenPair:
    email = payload.email.lower()
    ip = client_ip(request)
    guard = LoginGuard(store)
    state = guard.state(email, ip)

    if state.locked_seconds_left > 0:
        raise _error(
            status.HTTP_423_LOCKED,
            "ACCOUNT_LOCKED",
            "Слишком много неудачных попыток. Вход временно заблокирован.",
            retry_after_seconds=state.locked_seconds_left,
        )

    if state.captcha_required and not guard.check_captcha(payload.captcha_id, payload.captcha_answer):
        code = "CAPTCHA_INVALID" if payload.captcha_id else "CAPTCHA_REQUIRED"
        message = "Неверный ответ CAPTCHA" if payload.captcha_id else "Подтвердите, что вы не робот"
        raise _error(status.HTTP_401_UNAUTHORIZED, code, message, captcha_required=True,
                     failed_attempts=state.failed_attempts)

    user = db.scalar(select(User).where(User.email == email))
    if user is None or user.membership_status == "ARCHIVED" or not verify_password(
        payload.password, user.password_hash if user else None
    ):
        state = guard.register_failure(email, ip)
        if user is not None:
            user.failed_login_attempts = min(state.failed_attempts, 32767)
            user.last_failed_login_at = utcnow()
            if state.locked_seconds_left > 0:
                user.locked_until = utcnow() + timedelta(seconds=state.locked_seconds_left)
                write_audit(db, action="ACCOUNT_LOCKED", entity_type="user", entity_id=user.id,
                            group_id=user.group_id, ip_address=ip,
                            new_values={"locked_seconds": state.locked_seconds_left})
            db.commit()
        if state.locked_seconds_left > 0:
            raise _error(
                status.HTTP_423_LOCKED,
                "ACCOUNT_LOCKED",
                "Слишком много неудачных попыток. Вход заблокирован на 15 минут.",
                retry_after_seconds=state.locked_seconds_left,
            )
        raise _error(
            status.HTTP_401_UNAUTHORIZED,
            "INVALID_CREDENTIALS",
            "Неверный e-mail или пароль",
            captcha_required=state.captcha_required,
            failed_attempts=state.failed_attempts,
        )

    guard.register_success(email)
    user.failed_login_attempts = 0
    user.locked_until = None
    tokens = _issue_tokens(db, user, request)
    write_audit(db, action="LOGIN_SUCCESS", entity_type="user", entity_id=user.id,
                actor_id=user.id, group_id=user.group_id, ip_address=ip)
    db.commit()
    return tokens


@router.post("/refresh", response_model=TokenPair, summary="Обновить пару токенов по refresh-токену")
def refresh_tokens(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    """Ротация: старый refresh-токен отзывается. Повторное использование отозванного токена
    считается кражей — все сессии пользователя закрываются."""
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == hash_token(payload.refresh_token)))
    invalid = _error(status.HTTP_401_UNAUTHORIZED, "REFRESH_INVALID", "Сессия истекла, войдите заново")
    if session is None or session.token_type != "REFRESH":
        raise invalid
    if session.revoked_at is not None:
        db.execute(
            update(AuthSession)
            .where(AuthSession.user_id == session.user_id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=utcnow())
        )
        write_audit(db, action="REFRESH_TOKEN_REUSE", entity_type="user", entity_id=session.user_id,
                    ip_address=client_ip(request))
        db.commit()
        raise invalid
    if as_aware(session.expires_at) <= utcnow():
        raise invalid

    user = db.get(User, session.user_id)
    if user is None or user.membership_status == "ARCHIVED":
        raise invalid
    session.revoked_at = utcnow()
    tokens = _issue_tokens(db, user, request)
    db.commit()
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Выход (отзыв refresh-токена)")
def logout(payload: RefreshRequest, db: Session = Depends(get_db)) -> None:
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == hash_token(payload.refresh_token)))
    if session is not None and session.revoked_at is None:
        session.revoked_at = utcnow()
        db.commit()


@router.get("/me", response_model=UserOut, summary="Текущий пользователь")
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)
