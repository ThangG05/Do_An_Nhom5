"use client";

import React, { useState } from "react";
import { Conversation } from "@/types/message";
import { safeImageSrc } from "@/lib/media";
import NewConversationModal from "./NewConversationModal";
import RelativeTime from "@/components/ui/RelativeTime";

interface ConversationListProps {
  conversations: Conversation[];
  activeConversationId: string;
  onSelectConversation: (id: string) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onStartConversation: (userId:string) => Promise<unknown>;
}

export default function ConversationList({
  conversations,
  activeConversationId,
  onSelectConversation,
  searchQuery,
  onSearchChange,
  onStartConversation,
}: ConversationListProps) {
  const [showNewChat,setShowNewChat]=useState(false);
  return (
    <aside className="messenger-left-panel" aria-label="Danh sách cuộc trò chuyện">
      {showNewChat&&<NewConversationModal onClose={()=>setShowNewChat(false)} onStart={onStartConversation}/>}
      {/* Panel Header */}
      <div className="left-panel-header">
        <div className="title-row">
          <h2>Tin nhắn</h2>
          <button
            type="button"
            className="new-chat-icon-btn"
            title="Tạo cuộc trò chuyện mới"
            onClick={() => setShowNewChat(true)}
          >
            ✏️
          </button>
        </div>

        {/* Search Bar */}
        <div className="chat-search-box">
          <span className="search-icon">⌕</span>
          <input
            type="text"
            placeholder="Tìm kiếm trên Messenger..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
          />
          {searchQuery && (
            <button
              type="button"
              className="clear-search-btn"
              onClick={() => onSearchChange("")}
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Conversations List */}
      <div className="conversations-scroll-list">
        {conversations.length === 0 ? (
          <div className="no-chats-found">
            <p>Không tìm thấy cuộc trò chuyện</p>
          </div>
        ) : (
          conversations.map((conv) => {
            const isActive = conv.id === activeConversationId;
            const hasUnread = conv.unreadCount > 0;

            return (
              <div
                key={conv.id}
                className={`conversation-item-card ${isActive ? "active" : ""} ${
                  hasUnread ? "unread" : ""
                }`}
                onClick={() => onSelectConversation(conv.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter") onSelectConversation(conv.id);
                }}
              >
                {/* Avatar with Online/Offline Dot */}
                <div className="chat-avatar-wrap">
                  <div className="participant-avatar">{conv.participantAvatar.startsWith('/') || conv.participantAvatar.startsWith('http') ? <img src={safeImageSrc(conv.participantAvatar)} alt={conv.participantName} /> : conv.participantAvatar}</div>
                  <span
                    className={`online-status-dot ${
                      conv.isOnline ? "online" : "offline"
                    }`}
                    title={conv.isOnline ? "Đang hoạt động" : "Ngoại tuyến"}
                  />
                </div>

                {/* Text Meta */}
                <div className="chat-item-meta">
                  <div className="chat-item-top">
                    <strong className="participant-name">{conv.participantName}</strong>
                    <RelativeTime className="chat-time-stamp" value={conv.lastMessageTime}/>
                  </div>

                  <div className="chat-snippet-row">
                    <p className={`snippet-text ${hasUnread ? "bold" : ""}`}>
                      {conv.lastMessageSnippet}
                    </p>
                    {hasUnread && (
                      <span className="unread-counter-badge">
                        {conv.unreadCount}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}
