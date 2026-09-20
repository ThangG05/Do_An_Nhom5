import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.security import decode_access_token
from src.db.models.user import AccountStatus, SystemRole, User
from src.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bạn chưa đăng nhập.",
        )
    try:
        user_id = uuid.UUID(decode_access_token(credentials.credentials))
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    user = db.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise HTTPException(status_code=401, detail="Tài khoản không tồn tại.")
    if user.status == AccountStatus.LOCKED and user.suspended_until and user.suspended_until <= datetime.now(UTC):
        user.status=AccountStatus.ACTIVE;user.suspended_until=None;db.commit()
    if user.status == AccountStatus.LOCKED:
        raise HTTPException(status_code=403, detail="Tài khoản đã bị khóa.")
    if user.status != AccountStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="Tài khoản chưa hoạt động.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_super_admin(current_user: CurrentUser) -> User:
    if current_user.system_role != SystemRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên tổng được thực hiện thao tác này.")
    return current_user


def require_group_admin(
    group_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if current_user.system_role == SystemRole.SUPER_ADMIN:
        return current_user
    is_admin = db.execute(
        text(
            "SELECT 1 FROM group_members "
            "WHERE group_id = :group_id AND user_id = :user_id AND role = 'ADMIN'"
        ),
        {"group_id": group_id, "user_id": current_user.id},
    ).first()
    if is_admin is None:
        raise HTTPException(status_code=403, detail="Bạn không phải quản trị viên của nhóm này.")
    return current_user


CurrentSuperAdmin = Annotated[User, Depends(require_super_admin)]
CurrentGroupAdmin = Annotated[User, Depends(require_group_admin)]
