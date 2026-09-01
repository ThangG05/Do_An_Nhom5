"use client";

import React, { useState } from "react";
import { Conversation } from "@/types/message";

interface ChatDetailsPanelProps {
  conversation: Conversation;
  onClose: () => void;
}

export default function ChatDetailsPanel({
  conversation,
  onClose,
}: ChatDetailsPanelProps) {
  const [openCustomization, setOpenCustomization] = useState(true);
  const [openMedia, setOpenMedia] = useState(true);
  const [openPrivacy, setOpenPrivacy] = useState(false);
  const [isMuted, setIsMuted] = useState(false);

  return (
    <aside className="messenger-right-panel" aria-label="Chi tiết cuộc trò chuyện">
      {/* Panel Top Close */}
      <div className="panel-header-top">
        <h3>Thông tin hội thoại</h3>
        <button
          type="button"
          className="close-panel-btn"
          onClick={onClose}
          aria-label="Đóng bảng thông tin"
        >
          ✕
        </button>
      </div>

      <div className="details-scroll-content">
        {/* Profile Card Summary */}
        <div className="profile-summary-card">
          <div className="large-avatar-shell">
            <div className="avatar-core">{conversation.participantAvatar}</div>
            <span
              className={`status-dot ${
                conversation.isOnline ? "online" : "offline"
              }`}
            />
          </div>

          <h3 className="profile-display-name">{conversation.participantName}</h3>
          {conversation.role && (
            <span className="profile-role-chip">{conversation.role}</span>
          )}
          {conversation.bio && (
            <p className="profile-bio-text">{conversation.bio}</p>
          )}

          {/* Quick Action Circle Buttons */}
          <div className="profile-quick-actions">
            <button
              type="button"
              className="action-circle-btn"
              onClick={() => alert(`Xem hồ sơ của ${conversation.participantName}`)}
            >
              👤 <span>Hồ sơ</span>
            </button>
            <button
              type="button"
              className={`action-circle-btn ${isMuted ? "muted" : ""}`}
              onClick={() => setIsMuted((prev) => !prev)}
            >
              {isMuted ? "🔕" : "🔔"} <span>{isMuted ? "Đã tắt" : "Tắt thông báo"}</span>
            </button>
            <button
              type="button"
              className="action-circle-btn"
              onClick={() => alert("Tìm kiếm trong cuộc trò chuyện")}
            >
              ⌕ <span>Tìm kiếm</span>
            </button>
          </div>
        </div>

        {/* Accordion 1: Chat Customization */}
        <div className="accordion-section">
          <button
            type="button"
            className="accordion-header"
            onClick={() => setOpenCustomization((prev) => !prev)}
          >
            <span>🎨 Tùy chỉnh cuộc trò chuyện</span>
            <span className="chevron">{openCustomization ? "▲" : "▼"}</span>
          </button>

          {openCustomization && (
            <div className="accordion-body">
              <button
                type="button"
                className="customization-row-btn"
                onClick={() => alert("Đổi chủ đề màu sắc cuộc trò chuyện")}
              >
                🔴 <span>Đổi chủ đề</span>
              </button>
              <button
                type="button"
                className="customization-row-btn"
                onClick={() => alert("Chỉnh sửa biệt danh")}
              >
                ✏️ <span>Chỉnh sửa biệt danh</span>
              </button>
            </div>
          )}
        </div>

        {/* Accordion 2: Shared Media & Files */}
        <div className="accordion-section">
          <button
            type="button"
            className="accordion-header"
            onClick={() => setOpenMedia((prev) => !prev)}
          >
            <span>🖼️ File & Phương tiện đã chia sẻ</span>
            <span className="chevron">{openMedia ? "▲" : "▼"}</span>
          </button>

          {openMedia && (
            <div className="accordion-body">
              {/* Media Grid */}
              <div className="shared-media-subhead">Ảnh & Video</div>
              {conversation.sharedMedia.length === 0 ? (
                <p className="empty-subtext">Chưa có ảnh/video được chia sẻ</p>
              ) : (
                <div className="shared-media-grid">
                  {conversation.sharedMedia.map((m) => (
                    <div key={m.id} className="shared-media-thumb">
                      <img src={m.url} alt={m.name} />
                    </div>
                  ))}
                </div>
              )}

              {/* Files List */}
              <div className="shared-media-subhead" style={{ marginTop: "14px" }}>
                Tệp đính kèm ({conversation.sharedFiles.length})
              </div>
              {conversation.sharedFiles.length === 0 ? (
                <p className="empty-subtext">Chưa có tài liệu được chia sẻ</p>
              ) : (
                <div className="shared-files-list">
                  {conversation.sharedFiles.map((f) => (
                    <div key={f.id} className="shared-file-item">
                      <span className="file-icon">📄</span>
                      <div className="file-info">
                        <strong>{f.name}</strong>
                        <small>{f.size} · {f.type}</small>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Accordion 3: Privacy & Support */}
        <div className="accordion-section">
          <button
            type="button"
            className="accordion-header"
            onClick={() => setOpenPrivacy((prev) => !prev)}
          >
            <span>🔒 Quyền riêng tư & Hỗ trợ</span>
            <span className="chevron">{openPrivacy ? "▲" : "▼"}</span>
          </button>

          {openPrivacy && (
            <div className="accordion-body">
              <button
                type="button"
                className="customization-row-btn danger"
                onClick={() => alert(`Đã chặn người dùng ${conversation.participantName}`)}
              >
                🚫 <span>Chặn người dùng</span>
              </button>
              <button
                type="button"
                className="customization-row-btn danger"
                onClick={() => alert("Đã gửi báo cáo vi phạm")}
              >
                ⚠️ <span>Báo cáo cuộc trò chuyện</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
