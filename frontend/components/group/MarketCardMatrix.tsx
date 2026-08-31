"use client";

import React from "react";
import { MarketItem } from "@/types/group";
import { IconSearch, IconMessage } from "@/components/ui/Icons";

interface MarketCardMatrixProps {
  items: MarketItem[];
  searchQuery: string;
  onSearchChange: (q: string) => void;
  conditionFilter: string;
  onConditionFilterChange: (cond: string) => void;
  statusFilter: string;
  onStatusFilterChange: (st: string) => void;
  onToggleSold: (id: string) => void;
  onMessageSeller: (sellerName: string) => void;
}

export default function MarketCardMatrix({
  items,
  searchQuery,
  onSearchChange,
  conditionFilter,
  onConditionFilterChange,
  statusFilter,
  onStatusFilterChange,
  onToggleSold,
  onMessageSeller,
}: MarketCardMatrixProps) {
  return (
    <section className="group-module-section" aria-label="Chợ Pass Đồ Sinh Viên">
      {/* Filter Bar */}
      <div className="matrix-filter-bar">
        <div className="filter-search-box">
          <IconSearch size={16} color="#0F172A" className="search-icon-svg" />
          <input
            type="text"
            placeholder="Tìm kiếm sách, đồ điện tử, đồ dùng..."
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

        <div className="filter-selects-row">
          <select
            value={conditionFilter}
            onChange={(e) => onConditionFilterChange(e.target.value)}
            className="matrix-filter-select"
            aria-label="Lọc theo tình trạng"
          >
            <option value="all">Tất cả tình trạng</option>
            <option value="Like New">Lướt 99% / Như mới</option>
            <option value="Brand New">Mới 100%</option>
            <option value="Used">Đã qua sử dụng</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => onStatusFilterChange(e.target.value)}
            className="matrix-filter-select"
            aria-label="Lọc theo trạng thái tin"
          >
            <option value="all">Tất cả trạng thái</option>
            <option value="available">Còn hàng</option>
            <option value="sold">Đã bán</option>
          </select>
        </div>
      </div>

      {/* Empty State */}
      {items.length === 0 && (
        <div className="matrix-empty-state">
          <div className="empty-icon">🏷️</div>
          <h3>Không tìm thấy sản phẩm phù hợp</h3>
          <p>Thử thay đổi từ khóa tìm kiếm hoặc bỏ bớt bộ lọc.</p>
        </div>
      )}

      {/* Items Matrix Grid */}
      <div className="market-grid-matrix">
        {items.map((item) => (
          <article
            key={item.id}
            className={`market-item-card ${item.status === "sold" ? "item-sold" : ""}`}
          >
            {/* Image & Price Overlay */}
            <div className="item-thumbnail-wrap">
              <img src={item.image} alt={item.title} loading="lazy" />
              <div className="price-tag-badge">{item.price}</div>
              {item.status === "sold" && (
                <div className="sold-overlay-badge">ĐÃ BÁN</div>
              )}
              <span className={`condition-tag condition-${item.condition.toLowerCase().replace(/\s+/g, "-")}`}>
                {item.condition === "Like New"
                  ? "Lướt 99%"
                  : item.condition === "Brand New"
                  ? "Mới 100%"
                  : "Đã dùng"}
              </span>
            </div>

            {/* Content Body */}
            <div className="item-card-body">
              <div className="item-meta-top">
                <span className="item-category-chip">{item.category}</span>
                <small>{item.createdAt}</small>
              </div>

              <h3 className="item-card-title">{item.title}</h3>

              <div className="item-location-snippet">
                <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="#64748B" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ display: 'inline-block', verticalAlign: 'middle', marginRight: 4 }}>
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                  <circle cx="12" cy="10" r="3" />
                </svg>
                <span>{item.location}</span>
              </div>

              <div className="seller-profile-snippet">
                <img
                  src={item.sellerAvatar && item.sellerAvatar.length > 5 ? item.sellerAvatar : "/assets/logo.png"}
                  alt={item.sellerName}
                  className="author-avatar-img"
                />
                <span className="seller-name">{item.sellerName}</span>
              </div>

              {/* Card Action Buttons */}
              <div className="item-card-actions">
                <button
                  type="button"
                  className="msg-seller-btn"
                  disabled={item.status === "sold"}
                  onClick={() => onMessageSeller(item.sellerName)}
                >
                  <IconMessage size={16} color="#ffffff" strokeWidth={1.8} />
                  <span>Nhắn người bán</span>
                </button>

                <button
                  type="button"
                  className="toggle-status-btn"
                  onClick={() => onToggleSold(item.id)}
                  title={item.status === "sold" ? "Đánh dấu còn hàng" : "Đánh dấu đã bán"}
                >
                  {item.status === "sold" ? "Mở lại" : "Đã bán"}
                </button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
