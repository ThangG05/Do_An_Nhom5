import enum


class StrEnum(str, enum.Enum):
    pass


class AccountStatus(StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    DISABLED = "DISABLED"


class GroupRole(StrEnum):
    MEMBER = "MEMBER"
    ADMIN = "ADMIN"


class GroupStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class PostStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    HIDDEN = "HIDDEN"


class FriendRequestStatus(StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class ConversationType(StrEnum):
    DIRECT = "DIRECT"
    GROUP = "GROUP"


class MessageType(StrEnum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    FILE = "FILE"
    SYSTEM = "SYSTEM"


class NotificationType(StrEnum):
    POST_REVIEW = "POST_REVIEW"
    POST_LIKE = "POST_LIKE"
    COMMENT = "COMMENT"
    FRIEND_REQUEST = "FRIEND_REQUEST"
    MESSAGE = "MESSAGE"
    SYSTEM = "SYSTEM"


class ReportStatus(StrEnum):
    PENDING = "PENDING"
    REVIEWING = "REVIEWING"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"


class ReportTargetType(StrEnum):
    USER = "USER"
    POST = "POST"
    COMMENT = "COMMENT"


class AIDocumentType(StrEnum):
    REGULATION = "REGULATION"
    ANNOUNCEMENT = "ANNOUNCEMENT"
    FAQ = "FAQ"
    GUIDE = "GUIDE"
    DECISION = "DECISION"
    OTHER = "OTHER"


class AIDocumentStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class AIVisibility(StrEnum):
    PUBLIC = "PUBLIC"
    AUTHENTICATED = "AUTHENTICATED"
    GROUP = "GROUP"
    PRIVATE = "PRIVATE"


class AIMessageRole(StrEnum):
    SYSTEM = "SYSTEM"
    USER = "USER"
    ASSISTANT = "ASSISTANT"
