"use client";

import React from "react";
import { PostCategory } from "@/types/post";
import { IconMarket, IconHousing, IconEvent } from "@/components/ui/Icons";

interface CreatePostCardProps {
  onOpenModal: (category?: PostCategory) => void;
  userAvatar?: string;
  userName?: string;
}

export default function CreatePostCard({
  onOpenModal,
  userAvatar = "SV",
  userName = "sinh viên HVNH",
}: CreatePostCardProps) {
  return (
    <section className="create-post-card" aria-label="Tạo bài viết mới">
      {/* Upper Row: Avatar + Simulated Input Pill */}
      <div className="card-top-row">
        <div className="card-user-avatar-wrap">
          <img
            src={userAvatar && userAvatar !== "SV" ? userAvatar : "/assets/logo.png"}
            alt={userName}
            className="create-post-user-avatar"
          />
        </div>
        <button
          type="button"
          className="simulated-input-pill"
          onClick={() => onOpenModal("general")}
          aria-label="Mở bảng tạo bài viết"
        >
          <span>{`Bạn đang nghĩ gì thế, ${userName}?`}</span>
        </button>
      </div>

      <div className="card-divider" />

      {/* Action Triggers Row */}
      <div className="card-actions-row">
        <button
          type="button"
          className="quick-action-btn media-action"
          onClick={() => onOpenModal("general")}
        >
          <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="#0F172A" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" className="action-icon-svg">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <polyline points="21 15 16 10 5 21" />
          </svg>
          <span className="action-label">Ảnh / Video</span>
        </button>

        <button
          type="button"
          className="quick-action-btn market-action"
          onClick={() => onOpenModal("market")}
        >
          <IconMarket size={18} color="#0F172A" strokeWidth={1.8} className="action-icon-svg" />
          <span className="action-label">Pass đồ</span>
        </button>

        <button
          type="button"
          className="quick-action-btn room-action"
          onClick={() => onOpenModal("roommate")}
        >
          <IconHousing size={18} color="#0F172A" strokeWidth={1.8} className="action-icon-svg" />
          <span className="action-label">Ghép phòng</span>
        </button>

        <button
          type="button"
          className="quick-action-btn event-action"
          onClick={() => onOpenModal("event")}
        >
          <IconEvent size={18} color="#0F172A" strokeWidth={1.8} className="action-icon-svg" />
          <span className="action-label">Sự kiện</span>
        </button>
      </div>
    </section>
  );
}

