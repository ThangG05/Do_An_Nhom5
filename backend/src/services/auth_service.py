import re
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy import func, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, object_session

from src.config import settings
from src.core.security import (
    create_access_token,
    create_refresh_token,
    create_registration_token,
    decode_registration_token,
    hash_password,
    hash_refresh_token,
    hash_verification_code,
    verification_code_matches,
    verify_password,
)
from src.db.models.user import (
    AccountStatus,
    EmailVerificationCode,
    Profile,
    PasswordResetCode,
    RefreshToken,
    SystemRole,
    User,
)
from src.models.auth import AuthUserResponse, RegistrationVerifiedResponse, TokenResponse
from src.services import email_service


class GoogleAuthenticationError(Exception):
    """Lỗi xác thực Google có thể hiển thị an toàn cho người dùng."""


class ManualAuthenticationError(Exception):
    """Dữ liệu đăng ký hoặc đăng nhập thủ công không hợp lệ."""


class AccountAlreadyRegisteredError(ManualAuthenticationError):
    """Email đã có mật khẩu và không thể đăng ký lại."""


class VerificationCodeCooldownError(ManualAuthenticationError):
    def __init__(self, retry_after: int):
        super().__init__(f"Vui lòng chờ {retry_after} giây trước khi gửi lại mã.")
        self.retry_after = retry_after


def _normalize_email(value: object) -> str:
    return str(value or "").strip().lower()


def _validate_hvnh_email(value: object) -> str:
    email = _normalize_email(value)
    suffix = f"@{settings.ALLOWED_EMAIL_DOMAIN.strip().lower()}"
    if not email or not email.endswith(suffix) or email.count("@") != 1:
        raise ManualAuthenticationError(f"Chỉ chấp nhận email {suffix}.")
    return email


def _validate_google_identity(claims: dict[str, object]) -> tuple[str, str, str | None]:
    email = _normalize_email(claims.get("email"))
    allowed_domain = settings.ALLOWED_EMAIL_DOMAIN.strip().lower()
    expected_suffix = f"@{allowed_domain}"

    if claims.get("email_verified") is not True:
        raise GoogleAuthenticationError("Tài khoản Google chưa xác minh email.")
    if not email or not email.endswith(expected_suffix):
        raise GoogleAuthenticationError(f"Chỉ chấp nhận email {expected_suffix}.")
    if str(claims.get("hd") or "").lower() != allowed_domain:
        raise GoogleAuthenticationError(
            "Tài khoản này không thuộc Google Workspace của Học viện Ngân hàng."
        )

    full_name = str(claims.get("name") or email.split("@", 1)[0]).strip()
    picture = str(claims.get("picture") or "").strip() or None
    return email, full_name[:150], picture


def _verify_google_token(credential: str) -> dict[str, object]:
    if not settings.GOOGLE_CLIENT_ID:
        raise GoogleAuthenticationError("Đăng nhập Google chưa được cấu hình.")
    try:
        claims = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except (ValueError, GoogleAuthError) as exc:
        raise GoogleAuthenticationError("Thông tin đăng nhập Google không hợp lệ.") from exc
    return claims


def _make_username(email: str) -> str:
    local_part = email.split("@", 1)[0]
    return re.sub(r"[^a-z0-9_.-]", "", local_part.lower())[:100] or "student"


def _repair_legacy_google_username(user: User, db: Session) -> None:
    """Bỏ hậu tố ngẫu nhiên do phiên bản Google Auth cũ từng tạo."""
    expected_username = _make_username(user.email)
    legacy_pattern = rf"{re.escape(expected_username)}_[0-9a-f]{{8}}"
    if not re.fullmatch(legacy_pattern, user.username):
        return

    username_owner = db.scalar(select(User).where(User.username == expected_username))
    if username_owner is None or username_owner.id == user.id:
        user.username = expected_username


def _issue_tokens(user: User, db: Session, *, is_new_user: bool) -> TokenResponse:
    access_token, expires_in = create_access_token(str(user.id))
    refresh_token, refresh_hash, refresh_expires_at = create_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=refresh_expires_at,
        )
    )
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        user=serialize_auth_user(user, is_new_user=is_new_user),
    )


def serialize_auth_user(user: User, *, is_new_user: bool = False) -> AuthUserResponse:
    session = object_session(user)
    admin_group_slugs = []
    if session is not None:
        admin_group_slugs = list(
            session.scalars(
                text(
                    "SELECT groups.slug FROM group_members "
                    "JOIN groups ON groups.id = group_members.group_id "
                    "WHERE group_members.user_id = :user_id AND group_members.role = 'ADMIN' "
                    "ORDER BY groups.slug"
                ),
                {"user_id": user.id},
            )
        )
    return AuthUserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        full_name=user.profile.full_name if user.profile else user.username,
        avatar_url=None,
        is_new_user=is_new_user,
        system_role=(
            user.system_role.value
            if isinstance(user.system_role, SystemRole)
            else str(user.system_role)
        ),
        admin_group_slugs=admin_group_slugs,
    )


def refresh_session(refresh_token_value: str, db: Session) -> TokenResponse:
    now = datetime.now(UTC)
    stored_token = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(refresh_token_value),
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
    )
    if stored_token is None:
        raise ManualAuthenticationError("Refresh token không hợp lệ hoặc đã hết hạn.")

    user = db.get(User, stored_token.user_id)
    if user is None or user.deleted_at is not None or user.status != AccountStatus.ACTIVE:
        raise ManualAuthenticationError("Tài khoản không còn hoạt động.")

    access_token, expires_in = create_access_token(str(user.id))
    new_refresh_token, new_hash, new_expires_at = create_refresh_token()
    replacement = RefreshToken(
        user_id=user.id,
        token_hash=new_hash,
        expires_at=new_expires_at,
    )
    db.add(replacement)
    db.flush()
    stored_token.revoked_at = now
    stored_token.replaced_by_id = replacement.id
    db.commit()
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=expires_in,
        user=serialize_auth_user(user),
    )


def logout(refresh_token_value: str, db: Session) -> None:
    stored_token = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(refresh_token_value),
            RefreshToken.revoked_at.is_(None),
        )
    )
    if stored_token is not None:
        stored_token.revoked_at = datetime.now(UTC)
        db.commit()


def request_registration_code(email_value: str, db: Session) -> int:
    email = _validate_hvnh_email(email_value)
    user = db.scalar(select(User).where(func.lower(User.email) == email))

    if user is not None:
        if user.deleted_at is not None or user.status == AccountStatus.DISABLED:
            raise ManualAuthenticationError("Tài khoản đã bị vô hiệu hóa.")
        if user.status == AccountStatus.LOCKED:
            raise ManualAuthenticationError("Tài khoản đã bị khóa.")
        if user.status == AccountStatus.ACTIVE and not user.password_hash.startswith("!google:"):
            raise AccountAlreadyRegisteredError("Email này đã được đăng ký. Hãy đăng nhập.")
    else:
        user = User(
            email=email,
            username=_make_username(email),
            password_hash=f"!pending:{secrets.token_urlsafe(32)}",
            status=AccountStatus.PENDING,
        )
        user.profile = Profile(full_name=_make_username(email))
        db.add(user)
        try:
            db.flush()
        except IntegrityError as exc:
            db.rollback()
            raise AccountAlreadyRegisteredError("Email này đã được đăng ký.") from exc

    now = datetime.now(UTC)
    latest_code = db.scalar(
        select(EmailVerificationCode)
        .where(
            EmailVerificationCode.user_id == user.id,
            EmailVerificationCode.consumed_at.is_(None),
        )
        .order_by(EmailVerificationCode.created_at.desc())
        .limit(1)
    )
    if latest_code is not None and latest_code.created_at is not None:
        elapsed = (now - latest_code.created_at).total_seconds()
        if elapsed < settings.OTP_RESEND_COOLDOWN_SECONDS:
            retry_after = max(1, int(settings.OTP_RESEND_COOLDOWN_SECONDS - elapsed))
            raise VerificationCodeCooldownError(retry_after)

    db.execute(
        update(EmailVerificationCode)
        .where(
            EmailVerificationCode.user_id == user.id,
            EmailVerificationCode.consumed_at.is_(None),
        )
        .values(consumed_at=now)
    )
    code = f"{secrets.randbelow(10_000):04d}"
    db.add(
        EmailVerificationCode(
            user_id=user.id,
            code_hash=hash_verification_code(str(user.id), code),
            expires_at=now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
        )
    )

    try:
        email_service.send_verification_code(email, code)
        db.commit()
    except email_service.EmailDeliveryError:
        db.rollback()
        raise
    return settings.OTP_RESEND_COOLDOWN_SECONDS


def verify_registration_code(
    email_value: str,
    code: str,
    db: Session,
) -> RegistrationVerifiedResponse:
    email = _validate_hvnh_email(email_value)
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    if user is None:
        raise ManualAuthenticationError("Mã xác thực không hợp lệ hoặc đã hết hạn.")

    now = datetime.now(UTC)
    verification = db.scalar(
        select(EmailVerificationCode)
        .where(
            EmailVerificationCode.user_id == user.id,
            EmailVerificationCode.consumed_at.is_(None),
            EmailVerificationCode.expires_at > now,
        )
        .order_by(EmailVerificationCode.created_at.desc())
        .limit(1)
    )
    if verification is None or not verification_code_matches(
        str(user.id), code, verification.code_hash
    ):
        raise ManualAuthenticationError("Mã xác thực không hợp lệ hoặc đã hết hạn.")

    verification.consumed_at = now
    user.email_verified_at = user.email_verified_at or now
    db.commit()
    registration_token, expires_in = create_registration_token(str(user.id))
    return RegistrationVerifiedResponse(
        registration_token=registration_token,
        expires_in=expires_in,
    )


def complete_registration(
    registration_token: str,
    password: str,
    db: Session,
) -> TokenResponse:
    try:
        user_id = uuid.UUID(decode_registration_token(registration_token))
    except (ValueError, TypeError) as exc:
        raise ManualAuthenticationError(str(exc)) from exc

    user = db.get(User, user_id)
    if user is None or user.email_verified_at is None:
        raise ManualAuthenticationError("Tài khoản chưa được xác thực email.")
    if user.deleted_at is not None or user.status == AccountStatus.DISABLED:
        raise ManualAuthenticationError("Tài khoản đã bị vô hiệu hóa.")
    if user.status == AccountStatus.LOCKED:
        raise ManualAuthenticationError("Tài khoản đã bị khóa.")
    if user.status == AccountStatus.ACTIVE and not user.password_hash.startswith(("!google:", "!pending:")):
        raise AccountAlreadyRegisteredError("Tài khoản đã có mật khẩu.")

    is_new_user = user.status == AccountStatus.PENDING
    user.password_hash = hash_password(password)
    user.status = AccountStatus.ACTIVE
    user.last_login_at = datetime.now(UTC)
    return _issue_tokens(user, db, is_new_user=is_new_user)


def authenticate_with_password(email_value: str, password: str, db: Session) -> TokenResponse:
    email = _validate_hvnh_email(email_value)
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    now = datetime.now(UTC)
    if user is not None and user.login_locked_until and user.login_locked_until > now:
        raise ManualAuthenticationError("Tài khoản tạm khóa do đăng nhập sai nhiều lần. Vui lòng thử lại sau.")
    if user is None or not verify_password(password, user.password_hash):
        if user is not None:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.LOGIN_MAX_FAILED_ATTEMPTS:
                user.failed_login_attempts = 0
                user.login_locked_until = now + timedelta(minutes=settings.LOGIN_LOCK_MINUTES)
            db.commit()
        raise ManualAuthenticationError("Email hoặc mật khẩu không đúng.")
    if user.deleted_at is not None or user.status == AccountStatus.DISABLED:
        raise ManualAuthenticationError("Tài khoản đã bị vô hiệu hóa.")
    if user.status == AccountStatus.LOCKED:
        raise ManualAuthenticationError("Tài khoản đã bị khóa.")
    if user.status != AccountStatus.ACTIVE:
        raise ManualAuthenticationError("Tài khoản chưa được xác thực email.")

    user.failed_login_attempts = 0
    user.login_locked_until = None
    user.last_login_at = now
    return _issue_tokens(user, db, is_new_user=False)


def authenticate_with_google(
    credential: str,
    db: Session,
) -> TokenResponse:
    claims = _verify_google_token(credential)
    email, full_name, picture = _validate_google_identity(claims)

    user = db.scalar(select(User).where(func.lower(User.email) == email))
    is_new_user = user is None

    if user is None:
        now = datetime.now(UTC)
        user = User(
            email=email,
            username=_make_username(email),
            # Giá trị không thể đăng nhập bằng mật khẩu; schema hiện yêu cầu NOT NULL.
            password_hash=f"!google:{secrets.token_urlsafe(32)}",
            status=AccountStatus.ACTIVE,
            email_verified_at=now,
            last_login_at=now,
        )
        user.profile = Profile(full_name=full_name)
        db.add(user)
        try:
            db.flush()
        except IntegrityError as exc:
            db.rollback()
            # Một request đồng thời có thể vừa tạo cùng email. Tái sử dụng user đó.
            user = db.scalar(select(User).where(func.lower(User.email) == email))
            if user is None:
                raise GoogleAuthenticationError("Không thể tạo tài khoản Google.") from exc
            is_new_user = False

    if user.deleted_at is not None or user.status == AccountStatus.DISABLED:
        raise GoogleAuthenticationError("Tài khoản đã bị vô hiệu hóa.")
    if user.status == AccountStatus.LOCKED:
        raise GoogleAuthenticationError("Tài khoản đã bị khóa.")

    _repair_legacy_google_username(user, db)

    now = datetime.now(UTC)
    # Google đã xác minh đúng Workspace, nên có thể hoàn tất tài khoản PENDING cũ.
    if user.status == AccountStatus.PENDING:
        user.status = AccountStatus.ACTIVE
        user.email_verified_at = user.email_verified_at or now
    user.last_login_at = now

    response = _issue_tokens(user, db, is_new_user=is_new_user)
    response.user.avatar_url = picture
    response.user.full_name = user.profile.full_name if user.profile else full_name
    return response


def request_password_reset(email_value: str, db: Session) -> None:
    email = _validate_hvnh_email(email_value)
    user = db.scalar(select(User).where(func.lower(User.email) == email, User.deleted_at.is_(None)))
    if user is None or user.status != AccountStatus.ACTIVE:
        return
    now = datetime.now(UTC)
    latest = db.scalar(select(PasswordResetCode).where(PasswordResetCode.user_id == user.id, PasswordResetCode.consumed_at.is_(None)).order_by(PasswordResetCode.created_at.desc()).limit(1))
    if latest and (now - latest.created_at).total_seconds() < settings.OTP_RESEND_COOLDOWN_SECONDS:
        raise VerificationCodeCooldownError(max(1, int(settings.OTP_RESEND_COOLDOWN_SECONDS - (now-latest.created_at).total_seconds())))
    db.execute(update(PasswordResetCode).where(PasswordResetCode.user_id==user.id,PasswordResetCode.consumed_at.is_(None)).values(consumed_at=now))
    code=f"{secrets.randbelow(10000):04d}"
    db.add(PasswordResetCode(user_id=user.id,code_hash=hash_verification_code(str(user.id),code),expires_at=now+timedelta(minutes=settings.OTP_EXPIRE_MINUTES)))
    email_service.send_password_reset_code(email,code)
    db.commit()


def confirm_password_reset(email_value:str,code:str,new_password:str,db:Session)->None:
    email=_validate_hvnh_email(email_value);user=db.scalar(select(User).where(func.lower(User.email)==email,User.deleted_at.is_(None)))
    if not user: raise ManualAuthenticationError("Mã khôi phục không hợp lệ hoặc đã hết hạn.")
    now=datetime.now(UTC);item=db.scalar(select(PasswordResetCode).where(PasswordResetCode.user_id==user.id,PasswordResetCode.consumed_at.is_(None),PasswordResetCode.expires_at>now).order_by(PasswordResetCode.created_at.desc()).limit(1).with_for_update())
    if not item or item.attempts>=5: raise ManualAuthenticationError("Mã khôi phục không hợp lệ hoặc đã hết hạn.")
    if not verification_code_matches(str(user.id),code,item.code_hash):
        item.attempts+=1;db.commit();raise ManualAuthenticationError("Mã khôi phục không chính xác.")
    if not any(c.isalpha() for c in new_password) or not any(c.isdigit() for c in new_password): raise ManualAuthenticationError("Mật khẩu phải có chữ cái và chữ số.")
    user.password_hash=hash_password(new_password);item.consumed_at=now
    db.execute(update(RefreshToken).where(RefreshToken.user_id==user.id,RefreshToken.revoked_at.is_(None)).values(revoked_at=now));db.commit()


def change_password(user:User,current_password:str,new_password:str,db:Session)->None:
    if not verify_password(current_password,user.password_hash): raise ManualAuthenticationError("Mật khẩu hiện tại không chính xác.")
    if verify_password(new_password,user.password_hash): raise ManualAuthenticationError("Mật khẩu mới phải khác mật khẩu hiện tại.")
    if not any(c.isalpha() for c in new_password) or not any(c.isdigit() for c in new_password): raise ManualAuthenticationError("Mật khẩu phải có chữ cái và chữ số.")
    user.password_hash=hash_password(new_password);now=datetime.now(UTC)
    db.execute(update(RefreshToken).where(RefreshToken.user_id==user.id,RefreshToken.revoked_at.is_(None)).values(revoked_at=now));db.commit()
