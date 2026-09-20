import uuid
from typing import Literal
from pydantic import BaseModel, Field


class AdminDashboardResponse(BaseModel):
    total_users: int
    active_users: int
    locked_users: int
    disabled_users: int
    pending_posts: int
    approved_posts: int
    rejected_posts: int
    total_likes: int
    total_comments: int
    total_messages: int
    groups: list[dict]
    activity: list[dict]


class AdminUserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    student_code: str | None = None
    faculty: str | None = None
    status: str
    system_role: str
    admin_groups: list[dict] = Field(default_factory=list)
    created_at: str
    last_login_at: str | None = None
    suspended_until: str | None = None
    warning_count: int = 0


class AdminUserPage(BaseModel):
    items: list[AdminUserResponse]
    total: int
    limit: int
    offset: int


class AccountStatusRequest(BaseModel):
    status: Literal["ACTIVE", "LOCKED", "DISABLED"]
    reason: str = Field(min_length=3, max_length=1000)


class GroupRoleRequest(BaseModel):
    group_id: uuid.UUID
    grant: bool

class DisciplineRequest(BaseModel):
    action: Literal["WARN", "SUSPEND", "BAN", "UNLOCK"]
    reason: str = Field(min_length=3, max_length=1000)
    duration_days: int | None = Field(default=None, ge=1, le=365)

class AuditLogResponse(BaseModel):
    id: str
    actor_name: str
    action: str
    target_type: str
    target_id: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: str
