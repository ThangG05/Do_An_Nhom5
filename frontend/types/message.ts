export type MessageStatus = 'sent' | 'delivered' | 'seen';

export type MessageType = 'text' | 'image' | 'file';

export interface MessageAttachment {
  id: string;
  type: 'image' | 'file';
  url: string;
  name: string;
  size?: string;
}

export interface Message {
  id: string;
  conversationId: string;
  senderId: string;
  senderName: string;
  senderAvatar: string;
  content: string;
  timestamp: string;
  status: MessageStatus;
  type: MessageType;
  attachments?: MessageAttachment[];
}

export interface SharedMedia {
  id: string;
  url: string;
  type: 'image' | 'video';
  name: string;
}

export interface SharedFile {
  id: string;
  name: string;
  size: string;
  type: string;
  url: string;
}

export interface Conversation {
  id: string;
  participantId: string;
  participantName: string;
  participantAvatar: string;
  isOnline: boolean;
  lastActive?: string;
  lastMessageSnippet: string;
  lastMessageTime: string;
  unreadCount: number;
  bio?: string;
  role?: string;
  sharedMedia: SharedMedia[];
  sharedFiles: SharedFile[];
}
