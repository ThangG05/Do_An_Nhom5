"use client";

import React, { useState, useRef, useEffect } from "react";
import { Conversation, Message } from "@/types/message";

interface ChatWorkspaceProps {
  activeConversation: Conversation;
  messages: Message[];
  currentUserId: string;
  onSendMessage: (text: string, mediaUrl?: string) => void;
  onToggleDetailsPanel: () => void;
  showDetailsPanel: boolean;
  onBackMobile: () => void;
}

export default function ChatWorkspace({
  activeConversation,
  messages,
  currentUserId,
  onSendMessage,
  onToggleDetailsPanel,
  showDetailsPanel,
  onBackMobile,
}: ChatWorkspaceProps) {
  const [inputText, setInputText] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (!inputText.trim()) return;
    onSendMessage(inputText);
    setInputText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const url = URL.createObjectURL(file);
      onSendMessage(`[Đã gửi ảnh: ${file.name}]`, url);
    }
  };

  return (
    <main className="messenger-center-panel" aria-label="Khung trò chuyện">
      {/* Header Bar */}
      <div className="chat-workspace-header">
        <div className="header-left-info">
          {/* Mobile Back Button */}
          <button
            type="button"
            className="mobile-back-btn"
            onClick={onBackMobile}
            aria-label="Quay lại danh sách tin nhắn"
          >
            ←
          </button>

          <div className="header-avatar-wrap">
            <div className="participant-avatar">
              {activeConversation.participantAvatar}
            </div>
            <span
              className={`online-status-dot ${
                activeConversation.isOnline ? "online" : "offline"
              }`}
            />
          </div>

          <div className="header-text-meta">
            <strong className="recipient-name">
              {activeConversation.participantName}
            </strong>
            <span className="recipient-status">
              {activeConversation.isOnline
                ? "🟢 Đang hoạt động"
                : activeConversation.lastActive || "Ngoại tuyến"}
            </span>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="header-actions">
          <button
            type="button"
            className="chat-action-btn"
            title="Bắt đầu cuộc gọi thoại"
            onClick={() => alert(`Cuộc gọi thoại tới ${activeConversation.participantName}`)}
          >
            📞
          </button>
          <button
            type="button"
            className="chat-action-btn"
            title="Bắt đầu cuộc gọi video"
            onClick={() => alert(`Cuộc gọi video tới ${activeConversation.participantName}`)}
          >
            📹
          </button>
          <button
            type="button"
            className={`chat-action-btn ${showDetailsPanel ? "active" : ""}`}
            title="Thông tin cuộc trò chuyện"
            onClick={onToggleDetailsPanel}
          >
            ℹ️
          </button>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="messages-scroll-area">
        <div className="time-divider">
          <span>HÔM NAY · HVNH HUB MESSENGER</span>
        </div>

        {messages.map((msg) => {
          const isMe = msg.senderId === currentUserId;

          return (
            <div
              key={msg.id}
              className={`message-bubble-row ${isMe ? "outgoing" : "incoming"}`}
            >
              {!isMe && (
                <div className="message-sender-avatar">{msg.senderAvatar}</div>
              )}

              <div className="bubble-content-wrap">
                <div className={`chat-bubble ${isMe ? "me" : "them"}`}>
                  <p>{msg.content}</p>
                  {msg.attachments && msg.attachments.length > 0 && (
                    <div className="attachment-preview">
                      <img src={msg.attachments[0].url} alt="Tệp đính kèm" />
                    </div>
                  )}
                </div>

                <div className="message-meta-sub">
                  <span className="msg-time">{msg.timestamp}</span>
                  {isMe && (
                    <span className="msg-status-text">
                      {msg.status === "seen"
                        ? "✓✓ Đã xem"
                        : msg.status === "delivered"
                        ? "✓✓ Đã nhận"
                        : "✓ Đã gửi"}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Toolbar */}
      <div className="chat-input-toolbar">
        <div className="toolbar-left-tools">
          <button
            type="button"
            className="tool-btn"
            title="Đính kèm ảnh"
            onClick={() => fileInputRef.current?.click()}
          >
            🖼️
          </button>
          <button
            type="button"
            className="tool-btn"
            title="Đính kèm tệp"
            onClick={() => fileInputRef.current?.click()}
          >
            📎
          </button>
          <button
            type="button"
            className="tool-btn"
            title="Biểu tượng cảm xúc"
            onClick={() => setInputText((prev) => prev + " 😊")}
          >
            😊
          </button>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,.pdf,.doc,.docx"
          style={{ display: "none" }}
          onChange={handleFileSelect}
        />

        <div className="input-field-wrap">
          <input
            type="text"
            className="chat-text-input"
            placeholder="Nhập tin nhắn..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </div>

        <button
          type="button"
          className="send-message-btn"
          disabled={!inputText.trim()}
          onClick={handleSend}
          title="Gửi tin nhắn"
        >
          ➤
        </button>
      </div>
    </main>
  );
}
