from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from src.api.dependencies import CurrentUser
from src.db.session import get_db
from src.models.auth import (
    AuthUserResponse,
    CompleteRegistrationRequest,
    EmailRegistrationRequest,
    GoogleAuthRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegistrationVerifiedResponse,
    TokenResponse,
    VerifyEmailCodeRequest,
    PasswordResetRequest, PasswordResetConfirmRequest, PasswordChangeRequest,
)
from src.services import auth_service, email_service

router = APIRouter(prefix="/auth", tags=["Auth"])
DbSession = Annotated[Session, Depends(get_db)]

def _session_cookies(response:Response,tokens:TokenResponse)->TokenResponse:
    import secrets
    from src.config import settings
    csrf=secrets.token_urlsafe(24);domain=settings.AUTH_COOKIE_DOMAIN or None
    response.set_cookie("hvnh_refresh",tokens.refresh_token,max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS*86400,httponly=True,secure=settings.AUTH_COOKIE_SECURE,samesite="lax",path="/api/v1/auth",domain=domain)
    response.set_cookie("hvnh_csrf",csrf,max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS*86400,httponly=False,secure=settings.AUTH_COOKIE_SECURE,samesite="lax",path="/",domain=domain)
    tokens.refresh_token=""
    return tokens

def _cookie_token(request:Request,payload_token:str|None)->str:
    token=request.cookies.get("hvnh_refresh") or payload_token
    if not token: raise HTTPException(401,"Không có phiên đăng nhập.")
    if request.cookies.get("hvnh_refresh"):
        csrf=request.cookies.get("hvnh_csrf");header=request.headers.get("x-csrf-token")
        if not csrf or not header or not __import__('hmac').compare_digest(csrf,header): raise HTTPException(403,"CSRF token không hợp lệ.")
    return token


def _manual_auth_error(exc: Exception) -> HTTPException:
    if isinstance(exc, auth_service.VerificationCodeCooldownError):
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
            headers={"Retry-After": str(exc.retry_after)},
        )
    if isinstance(exc, auth_service.AccountAlreadyRegisteredError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, email_service.EmailDeliveryError):
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/register/request-code",
    response_model=MessageResponse,
    summary="Gửi OTP đăng ký tới email HVNH",
)
def request_registration_code(
    request: EmailRegistrationRequest,
    db: DbSession,
) -> MessageResponse:
    try:
        retry_after = auth_service.request_registration_code(request.email, db)
        return MessageResponse(
            message="Mã xác thực đã được gửi tới email của bạn.",
            retry_after=retry_after,
        )
    except (
        auth_service.ManualAuthenticationError,
        email_service.EmailDeliveryError,
    ) as exc:
        raise _manual_auth_error(exc) from exc


@router.post(
    "/register/verify-code",
    response_model=RegistrationVerifiedResponse,
    summary="Xác minh OTP đăng ký",
)
def verify_registration_code(
    request: VerifyEmailCodeRequest,
    db: DbSession,
) -> RegistrationVerifiedResponse:
    try:
        return auth_service.verify_registration_code(request.email, request.code, db)
    except auth_service.ManualAuthenticationError as exc:
        raise _manual_auth_error(exc) from exc


@router.post(
    "/register/complete",
    response_model=TokenResponse,
    summary="Đặt mật khẩu và hoàn tất đăng ký",
)
def complete_registration(
    request: CompleteRegistrationRequest,
    db: DbSession,
    response: Response,
) -> TokenResponse:
    try:
        return _session_cookies(response,auth_service.complete_registration(
            request.registration_token,
            request.password,
            db,
        ))
    except auth_service.ManualAuthenticationError as exc:
        raise _manual_auth_error(exc) from exc


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Đăng nhập bằng email và mật khẩu",
)
def login(request: LoginRequest, db: DbSession,response:Response) -> TokenResponse:
    try:
        return _session_cookies(response,auth_service.authenticate_with_password(request.email, request.password, db))
    except auth_service.ManualAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@router.post("/refresh", response_model=TokenResponse, summary="Làm mới phiên đăng nhập")
def refresh(payload: RefreshTokenRequest, request:Request,response:Response,db: DbSession) -> TokenResponse:
    try:
        return _session_cookies(response,auth_service.refresh_session(_cookie_token(request,payload.refresh_token), db))
    except auth_service.ManualAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@router.post("/logout", response_model=MessageResponse, summary="Đăng xuất")
def logout(payload: LogoutRequest, request:Request,response:Response,db: DbSession) -> MessageResponse:
    auth_service.logout(_cookie_token(request,payload.refresh_token), db)
    response.delete_cookie("hvnh_refresh",path="/api/v1/auth");response.delete_cookie("hvnh_csrf",path="/")
    return MessageResponse(message="Đã đăng xuất.")


@router.get("/me", response_model=AuthUserResponse, summary="Lấy người dùng hiện tại")
def me(current_user: CurrentUser, db: DbSession) -> AuthUserResponse:
    response = auth_service.serialize_auth_user(current_user)
    if current_user.profile and current_user.profile.avatar_media_id:
        from src.db.models.media import MediaFile, MediaStatus
        from src.services.storage_service import create_download_url
        media = db.get(MediaFile, current_user.profile.avatar_media_id)
        if media and media.status == MediaStatus.READY:
            response.avatar_url = create_download_url(media)
    return response


@router.post(
    "/google",
    response_model=TokenResponse,
    summary="Đăng ký hoặc đăng nhập bằng Google Workspace HVNH",
)
def google_auth(request: GoogleAuthRequest, db: DbSession,response:Response) -> TokenResponse:
    try:
        return _session_cookies(response,auth_service.authenticate_with_google(request.credential, db))
    except auth_service.GoogleAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@router.get("/health")
async def health() -> dict[str, str]:
    return {"module": "auth"}

@router.post("/password/forgot",response_model=MessageResponse)
def forgot_password(payload:PasswordResetRequest,db:DbSession):
    try: auth_service.request_password_reset(payload.email,db)
    except (auth_service.ManualAuthenticationError,auth_service.VerificationCodeCooldownError,email_service.EmailDeliveryError) as exc: raise _manual_auth_error(exc) from exc
    return MessageResponse(message="Nếu tài khoản hợp lệ, mã khôi phục đã được gửi.")

@router.post("/password/reset",response_model=MessageResponse)
def reset_password(payload:PasswordResetConfirmRequest,db:DbSession):
    try: auth_service.confirm_password_reset(payload.email,payload.code,payload.new_password,db)
    except auth_service.ManualAuthenticationError as exc: raise _manual_auth_error(exc) from exc
    return MessageResponse(message="Đã đặt lại mật khẩu. Hãy đăng nhập lại.")

@router.post("/password/change",response_model=MessageResponse)
def update_password(payload:PasswordChangeRequest,current_user:CurrentUser,db:DbSession):
    try: auth_service.change_password(current_user,payload.current_password,payload.new_password,db)
    except auth_service.ManualAuthenticationError as exc: raise _manual_auth_error(exc) from exc
    return MessageResponse(message="Đã đổi mật khẩu. Hãy đăng nhập lại.")
