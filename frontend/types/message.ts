export type MessageStatus = 'sent' | 'delivered' | 'seen';

export type MessageType = 'text' | 'image' | 'video' | 'audio' | 'file';

export interface MessageAttachment {
  id: string;
  type: 'image' | 'video' | 'audio' | 'file';
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
  theme: 'blue' | 'indigo' | 'emerald' | 'rose' | 'violet' | 'amber';
  nickname?: string | null;
  isMuted: boolean;
  sharedMedia: SharedMedia[];
  sharedFiles: SharedFile[];
}

export interface RealtimeCallEvent {
  event: 'call.offer' | 'call.answer' | 'call.ice' | 'call.end';
  conversation_id: string;
  from_user_id: string;
  video?: boolean;
  sdp?: RTCSessionDescriptionInit;
  candidate?: RTCIceCandidateInit;
  reason?: string;
  sequence: number;
}
