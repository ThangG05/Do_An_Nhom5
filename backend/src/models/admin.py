import uuid
from typing import Literal
from pydantic import BaseModel, Field
from src.models.post import ProfilePostResponse


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
    rag_input_tokens: int | None = None
    rag_output_tokens: int | None = None
    rag_total_tokens: int | None = None
    rag_usage_calls: int = 0
    rag_usage_missing: int = 0


class AdminUserPage(BaseModel):
    items: list[AdminUserResponse]
    total: int
    limit: int
    offset: int


class AdminProfilePreview(BaseModel):
    id: str
    name: str
    username: str
    avatar: str | None = None
    cover: str | None = None
    bio: str = ""
    student_code: str | None = None
    faculty: str | None = None
    joined_at: str
    status: str


class AdminPublicPostPage(BaseModel):
    items: list[ProfilePostResponse]
    total: int
    limit: int
    offset: int


class AdminPublicPostAction(BaseModel):
    action: Literal["HIDE", "RESTORE"]
    reason: str = Field(min_length=3, max_length=1000)


class GroupAdminInfoResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    student_code: str | None = None
    faculty: str | None = None
    avatar_url: str | None = None
    status: str


class RAGUsageCallResponse(BaseModel):
    id: uuid.UUID
    created_at: str
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    status: str
    usage_source: str


class RAGUsageDayResponse(BaseModel):
    date: str
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    calls: int


class RAGUserUsageResponse(BaseModel):
    user_id: uuid.UUID
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    usage_calls: int
    usage_missing: int
    daily: list[RAGUsageDayResponse]
    calls: list[RAGUsageCallResponse]


class AccountStatusRequest(BaseModel):
    status: Literal["ACTIVE", "LOCKED", "DISABLED"]
    reason: str = Field(min_length=3, max_length=1000)


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
