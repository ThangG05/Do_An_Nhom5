import uuid
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class MarketListingData(BaseModel):
    price: str = Field(default="", max_length=100)
    condition: str = Field(default="", max_length=100)
    location: str = Field(default="", max_length=255)
    status: Literal["active", "sold"] = "active"


class RoomListingData(BaseModel):
    rentPerMonth: str = Field(default="", max_length=100)
    area: str = Field(default="", max_length=100)
    amenities: list[str] = Field(default_factory=list, max_length=30)
    location: str = Field(default="", max_length=255)
    status: Literal["active", "rented"] = "active"


class EventListingData(BaseModel):
    eventDate: str = Field(default="", max_length=30)
    eventTime: str = Field(default="", max_length=30)
    location: str = Field(default="", max_length=255)
    organizer: str = Field(default="", max_length=255)
    status: Literal["active", "expired"] = "active"


class CreateProfilePostRequest(BaseModel):
    content: str = Field(default="", max_length=10000)
    privacy: Literal["public", "friends", "private"] = "public"
    media_ids: list[uuid.UUID] = Field(default_factory=list, max_length=10)
    category: Literal["general", "market", "roommate", "event", "study"] = "general"
    marketListing: MarketListingData | None = None
    roomListing: RoomListingData | None = None
    eventListing: EventListingData | None = None

    @model_validator(mode="after")
    def has_content(self):
        if not self.content.strip() and not self.media_ids:
            raise ValueError("Bài viết phải có nội dung hoặc media.")
        return self


class PostMediaResponse(BaseModel):
    id: str
    url: str
    type: Literal["image", "video", "audio", "file"]
    name: str | None = None
    size: int | None = None


class PostAuthorResponse(BaseModel):
    id: str
    name: str
    avatar: str
    role: str = "Sinh viên"
    isVerified: bool = True


class ProfilePostResponse(BaseModel):
    id: str
    author: PostAuthorResponse
    createdAt: str
    content: str
    category: str = "general"
    privacy: str
    media: list[PostMediaResponse] = Field(default_factory=list)
    likesCount: int = 0
    commentsCount: int = 0
    isLiked: bool = False
    comments: list["CommentResponse"] = Field(default_factory=list)
    groupId: str | None = None
    status: str = "APPROVED"
    rejectionReason: str | None = None
    isPinned: bool = False
    marketListing: MarketListingData | None = None
    roomListing: RoomListingData | None = None
    eventListing: EventListingData | None = None


class UpdatePostRequest(BaseModel):
    content: str = Field(min_length=1, max_length=10000)
    privacy: Literal["public", "friends", "private"] | None = None
    category: Literal["general", "market", "roommate", "event", "study"] | None = None
    media_ids: list[uuid.UUID] | None = Field(default=None,max_length=10)
    marketListing: MarketListingData | None = None
    roomListing: RoomListingData | None = None
    eventListing: EventListingData | None = None


class CommentCreateRequest(BaseModel):
    content: str = Field(default="", max_length=2000)
    parent_id: uuid.UUID | None = None
    media_id: uuid.UUID | None = None
    @model_validator(mode="after")
    def has_content_or_media(self):
        if not self.content.strip() and not self.media_id: raise ValueError("Bình luận phải có nội dung hoặc ảnh.")
        return self

class CommentUpdateRequest(BaseModel):
    content: str = Field(min_length=1,max_length=2000)


class CommentAuthorResponse(BaseModel):
    id: str
    name: str
    avatar: str


class CommentResponse(BaseModel):
    id: str
    author: CommentAuthorResponse
    content: str
    createdAt: str
    parentId: str | None = None
    imageUrl: str | None = None


class LikeResponse(BaseModel):
    isLiked: bool
    likesCount: int


class LikeRequest(BaseModel):
    is_liked: bool


ProfilePostResponse.model_rebuild()
