"use client";

import React from "react";
import { GroupTab, GroupHeaderData } from "@/types/group";
import { IconMarket, IconHousing, IconEvent } from "@/components/ui/Icons";

interface GroupHeaderProps {
  data: GroupHeaderData;
  activeTab: GroupTab;
  onTabChange: (tab: GroupTab) => void;
  onToggleJoin: () => void;
  onOpenCreateModal: () => void;
}

export default function GroupHeader({
  data,
  activeTab,
  onTabChange,
  onToggleJoin,
  onOpenCreateModal,
}: GroupHeaderProps) {
  return (
    <header className="group-header-card">
      {/* Group Info Section */}
      <div className="group-info-row">
        {/* Doppelrand Avatar Container */}
        <div className="group-avatar-shell">
          <div className="group-avatar-core">
            <span>{data.avatarImage}</span>
          </div>
        </div>

        {/* Text Meta */}
        <div className="group-title-block">
          <div className="title-with-badge">
            <h1>{data.title}</h1>
            <span className="official-group-badge">✓ Nhóm Chính Thức</span>
          </div>
          <p className="group-meta-stats">
            🌐 Nhóm Công Khai · <strong>{data.memberCount.toLocaleString()} thành viên</strong> · {data.postCount.toLocaleString()} bài viết
          </p>
          <p className="group-description">{data.description}</p>
        </div>

        {/* Action Buttons */}
        <div className="group-header-actions">
          <button
            type="button"
            className={`join-group-btn ${data.isJoined ? "joined" : ""}`}
            onClick={onToggleJoin}
          >
            {data.isJoined ? "✓ Đã tham gia" : "+ Tham gia nhóm"}
          </button>

          <button
            type="button"
            className="create-listing-btn"
            onClick={onOpenCreateModal}
          >
            + Tạo tin đăng
          </button>
        </div>
      </div>

      {/* Navigation Tabs Bar */}
      <nav className="group-nav-tabs" aria-label="Danh mục hội nhóm">
        <button
          type="button"
          className={`group-tab-item ${activeTab === "market" ? "active" : ""}`}
          onClick={() => onTabChange("market")}
        >
          <IconMarket size={18} className="tab-svg-icon" />
          <span>Pass đồ & Marketplace</span>
        </button>

        <button
          type="button"
          className={`group-tab-item ${activeTab === "room" ? "active" : ""}`}
          onClick={() => onTabChange("room")}
        >
          <IconHousing size={18} className="tab-svg-icon" />
          <span>Tìm trọ & Ở ghép</span>
        </button>

        <button
          type="button"
          className={`group-tab-item ${activeTab === "event" ? "active" : ""}`}
          onClick={() => onTabChange("event")}
        >
          <IconEvent size={18} className="tab-svg-icon" />
          <span>Sự kiện & Hoạt động</span>
        </button>
      </nav>
    </header>
  );
}

