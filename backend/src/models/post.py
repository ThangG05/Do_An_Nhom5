import uuid
import re
from datetime import date, time
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class MarketListingData(BaseModel):
    productName: str = Field(default="", max_length=200)
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
    eventName: str = Field(default="", max_length=200)
    eventDate: str = Field(default="", max_length=30)
    eventTime: str = Field(default="", max_length=30)
    location: str = Field(default="", max_length=255)
    organizer: str = Field(default="", max_length=255)
    status: Literal["active", "expired"] = "active"


class StudyListingData(BaseModel):
    subjectName: str = Field(default="", max_length=200)


def validate_group_fields(category: str, content: str, listing: dict | None) -> None:
    """Validate new forms, without making legacy JSONB rows unreadable."""
    data = listing or {}
    required = {
        "market": [("productName", "Tên vật phẩm"), ("location", "Vị trí")],
        "event": [("eventName", "Tên sự kiện"), ("location", "Vị trí")],
        "roommate": [("location", "Vị trí")],
        "study": [("subjectName", "Tên môn học")],
    }
    for key, label in required.get(category, []):
        if not str(data.get(key, "")).strip():
            raise ValueError(f"{label} không được để trống.")
    if category in {"event", "roommate", "study"} and not content.strip():
        raise ValueError("Vui lòng nhập mô tả sự kiện, thông tin phòng hoặc nội dung tài liệu.")
    if category in {"market", "roommate"}:
        price = str(data.get("price" if category == "market" else "rentPerMonth", "")).strip()
        if (category == "market" or price) and not re.fullmatch(r"[0-9]{1,15}", price):
            raise ValueError("Giá phải là số nguyên VNĐ không âm (tối đa 15 chữ số).")
    if category == "event":
        try:
            date.fromisoformat(data.get("eventDate", ""))
            time.fromisoformat(data.get("eventTime", ""))
        except (ValueError, TypeError):
            raise ValueError("Vui lòng chọn ngày và giờ diễn ra hợp lệ.") from None


class PostLocationData(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    address: str | None = Field(default=None, max_length=500)


class CreateProfilePostRequest(BaseModel):
    # Version 1 remains readable/writable for the existing mobile application.
    form_version: Literal[1, 2] = 1
    content: str = Field(default="", max_length=10000)
    privacy: Literal["public", "friends", "private"] = "public"
    media_ids: list[uuid.UUID] = Field(default_factory=list, max_length=10)
    category: Literal["general", "market", "roommate", "event", "study"] = "general"
    marketListing: MarketListingData | None = None
    roomListing: RoomListingData | None = None
    eventListing: EventListingData | None = None
    studyListing: StudyListingData | None = None
    location: PostLocationData | None = None

    @model_validator(mode="after")
    def has_content(self):
        self.content = self.content.strip()
        if self.form_version == 2 and self.category != "general":
            value = {"market": self.marketListing, "roommate": self.roomListing, "event": self.eventListing, "study": self.studyListing}.get(self.category)
            validate_group_fields(self.category, self.content, value.model_dump() if value else None)
        elif not self.content and not self.media_ids:
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
    groupName: str | None = None
    groupSlug: str | None = None
    status: str = "APPROVED"
    rejectionReason: str | None = None
    isPinned: bool = False
    marketListing: MarketListingData | None = None
    roomListing: RoomListingData | None = None
    eventListing: EventListingData | None = None
    studyListing: StudyListingData | None = None
    location: PostLocationData | None = None


class UpdatePostRequest(BaseModel):
    form_version: Literal[1, 2] = 1
    content: str = Field(max_length=10000)
    privacy: Literal["public", "friends", "private"] | None = None
    category: Literal["general", "market", "roommate", "event", "study"] | None = None
    media_ids: list[uuid.UUID] | None = Field(default=None,max_length=10)
    marketListing: MarketListingData | None = None
    roomListing: RoomListingData | None = None
    eventListing: EventListingData | None = None
    studyListing: StudyListingData | None = None
    location: PostLocationData | None = None


class CommentMentionInput(BaseModel):
    user_id: uuid.UUID
    start: int = Field(ge=0)
    end: int = Field(gt=0)


class CommentCreateRequest(BaseModel):
    content: str = Field(default="", max_length=2000)
    parent_id: uuid.UUID | None = None
    media_id: uuid.UUID | None = None
    mentions: list[CommentMentionInput] = Field(default_factory=list, max_length=20)
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


class CommentMentionResponse(BaseModel):
    userId: str
    name: str
    username: str
    start: int
    end: int


class CommentResponse(BaseModel):
    id: str
    author: CommentAuthorResponse
    content: str
    createdAt: str
    parentId: str | None = None
    imageUrl: str | None = None
    mentions: list[CommentMentionResponse] = Field(default_factory=list)


class LikeResponse(BaseModel):
    isLiked: bool
    likesCount: int


class LikeRequest(BaseModel):
    is_liked: bool


ProfilePostResponse.model_rebuild()
