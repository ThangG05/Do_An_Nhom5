import uuid
from pydantic import BaseModel,Field,model_validator

class DirectConversationRequest(BaseModel): target_user_id: uuid.UUID
class ConversationSettingsRequest(BaseModel):
    theme:str|None=Field(default=None,pattern="^(blue|indigo|emerald|rose|violet|amber)$")
    nickname:str|None=Field(default=None,max_length=100)
    is_muted:bool|None=None
class SendMessageRequest(BaseModel):
    content: str=""; media_ids:list[uuid.UUID]=Field(default_factory=list,max_length=5); reply_to_id:uuid.UUID|None=None
    @model_validator(mode="after")
    def valid(self):
        if not self.content.strip() and not self.media_ids: raise ValueError("Tin nhắn phải có nội dung hoặc media.")
        return self
class AttachmentResponse(BaseModel): id:str; type:str; url:str; name:str; size:str|None=None
class SharedAttachmentsResponse(BaseModel): media:list[AttachmentResponse]=Field(default_factory=list); files:list[AttachmentResponse]=Field(default_factory=list)
class MessageResponse(BaseModel): id:str; conversationId:str; senderId:str; senderName:str; senderAvatar:str; content:str; timestamp:str; status:str; type:str; attachments:list[AttachmentResponse]=Field(default_factory=list)
class ConversationResponse(BaseModel): id:str; participantId:str; participantName:str; participantAvatar:str; isOnline:bool=False; lastActive:str="Ngoại tuyến"; lastMessageSnippet:str=""; lastMessageTime:str=""; unreadCount:int=0; bio:str=""; role:str="Sinh viên"; theme:str="blue"; nickname:str|None=None; isMuted:bool=False; sharedMedia:list[AttachmentResponse]=Field(default_factory=list); sharedFiles:list[AttachmentResponse]=Field(default_factory=list)
class UnreadMessagesResponse(BaseModel): unread_count:int
