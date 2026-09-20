import uuid
from typing import Literal
from pydantic import BaseModel, Field

class UserResponse(BaseModel):
    id: str
    email: str


class ProfileUpdateRequest(BaseModel):
    bio: str | None = Field(default=None, max_length=5000)
    faculty: str | None = Field(default=None, max_length=150)
    courseYear: str | None = Field(default=None, max_length=50)
    pronouns: str | None = Field(default=None, max_length=50)
    workplace: str | None = Field(default=None, max_length=150)
    education: str | None = Field(default=None, max_length=150)
    currentCity: str | None = Field(default=None, max_length=150)
    hometown: str | None = Field(default=None, max_length=150)
    socialLinks: dict[str, str] | None = None


class ProfileResponse(BaseModel):
    id: str
    name: str
    username: str
    avatar: str
    coverBanner: str
    bio: str
    pronouns: str = ""
    role: str = "Sinh viên"
    studentCode: str | None = None
    faculty: str | None = None
    courseYear: str | None = None
    workplace: str = ""
    education: str = "Học viện Ngân hàng (BAV)"
    currentCity: str = ""
    hometown: str = ""
    joinedDate: str
    email: str
    isVerified: bool
    isOnline: bool = False
    friendsCount: int
    followersCount: int = 0
    mutualFriendsCount: int = 0
    mutualFriendsAvatars: list[str] = Field(default_factory=list)
    friendshipStatus: str
    socialLinks: dict[str, str] = Field(default_factory=dict)
    joinedGroups: list["JoinedGroupResponse"] = Field(default_factory=list)


class JoinedGroupResponse(BaseModel):
    id: str
    name: str
    slug: str
    role: str


class UpdateAvatarRequest(BaseModel):
    media_id: uuid.UUID
    caption: str = Field(default="", max_length=5000)
    visibility: Literal["PUBLIC", "FRIENDS", "PRIVATE"] = "PUBLIC"
    create_post: bool = True


class UpdateAvatarResponse(BaseModel):
    media_id: uuid.UUID
    avatar_url: str
    post_id: uuid.UUID | None = None


class UpdateCoverRequest(BaseModel):
    media_id: uuid.UUID


class UpdateCoverResponse(BaseModel):
    media_id: uuid.UUID
    cover_url: str


class FriendshipActionRequest(BaseModel):
    action: Literal["add", "accept", "reject", "unfriend", "cancel"]


class FriendshipActionResponse(BaseModel):
    status: Literal["self", "none", "friends", "pending_sent", "pending_received"]


class FriendResponse(BaseModel):
    id: str
    name: str
    username: str
    avatar: str
    mutualCount: int
    isOnline: bool = False
    role: str = "Sinh viên"
    faculty: str | None = None
    friendshipStatus: str = "friends"


class UserSearchResponse(FriendResponse):
    studentCode: str | None = None

class BlockResponse(BaseModel):
    blocked: bool


class UserPhotoResponse(BaseModel):
    id: str
    url: str
    caption: str = ""
    createdAt: str
    likesCount: int = 0
    albumName: str = "Ảnh tải lên"


class UserListingResponse(BaseModel):
    id: str
    title: str
    category: Literal["market", "roommate", "event"]
    price: str = ""
    location: str = ""
    status: Literal["active", "sold", "rented", "expired"] = "active"
    imageUrl: str = ""
    createdAt: str
    description: str = ""


ProfileResponse.model_rebuild()
