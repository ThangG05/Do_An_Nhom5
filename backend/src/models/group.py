import uuid
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class GroupResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str = ""
    member_count: int = 0
    membership: Literal["NONE", "PENDING", "MEMBER", "ADMIN"] = "NONE"


class GroupPostCreateRequest(BaseModel):
    content: str = Field(default="", max_length=10000)
    media_ids: list[uuid.UUID] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def validate_content(self):
        if not self.content.strip() and not self.media_ids:
            raise ValueError("Bài viết phải có nội dung hoặc media.")
        return self


class ModerationRequest(BaseModel):
    decision: Literal["APPROVE", "REJECT"]
    reason: str | None = Field(default=None, max_length=2000)


class JoinRequestDecision(BaseModel):
    decision: Literal["APPROVE", "REJECT"]


class PinRequest(BaseModel):
    is_pinned: bool

class RemovePostRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)


class GroupMemberResponse(BaseModel):
    id: str
    name: str
    username: str
    role: str
    student_code: str | None = None


class JoinRequestResponse(BaseModel):
    id: str
    user_id: str
    name: str
    username: str
    created_at: str
