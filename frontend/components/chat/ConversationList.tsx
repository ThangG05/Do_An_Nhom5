"use client";

import React from "react";
import { Conversation } from "@/types/message";

interface ConversationListProps {
  conversations: Conversation[];
  activeConversationId: string;
  onSelectConversation: (id: string) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
}

export default function ConversationList({
  conversations,
  activeConversationId,
  onSelectConversation,
  searchQuery,
  onSearchChange,
}: ConversationListProps) {
  return (
    <aside className="messenger-left-panel" aria-label="Danh sách cuộc trò chuyện">
      {/* Panel Header */}
      <div className="left-panel-header">
        <div className="title-row">
          <h2>Tin nhắn</h2>
          <button
            type="button"
            className="new-chat-icon-btn"
            title="Tạo cuộc trò chuyện mới"
            onClick={() => alert("Chức năng tạo tin nhắn mới với sinh viên HVNH")}
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
                  <div className="participant-avatar">{conv.participantAvatar}</div>
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
                    <span className="chat-time-stamp">{conv.lastMessageTime}</span>
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
