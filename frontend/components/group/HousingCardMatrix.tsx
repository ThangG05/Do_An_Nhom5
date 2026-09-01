"use client";

import React from "react";
import { RoomItem } from "@/types/group";
import { IconSearch, IconHousing } from "@/components/ui/Icons";

interface HousingCardMatrixProps {
  items: RoomItem[];
  searchQuery: string;
  onSearchChange: (q: string) => void;
  statusFilter: string;
  onStatusFilterChange: (st: string) => void;
  onContactLandlord: (name: string, phone: string) => void;
}

export default function HousingCardMatrix({
  items,
  searchQuery,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  onContactLandlord,
}: HousingCardMatrixProps) {
  return (
    <section className="group-module-section" aria-label="Tìm Trọ & Ở Ghép Sinh Viên">
      {/* Filter Bar */}
      <div className="matrix-filter-bar">
        <div className="filter-search-box">
          <IconSearch size={16} color="#0F172A" className="search-icon-svg" />
          <input
            type="text"
            placeholder="Tìm theo khu vực (Chùa Bộc, Tây Sơn, Phạm Ngọc Thạch)..."
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
            value={statusFilter}
            onChange={(e) => onStatusFilterChange(e.target.value)}
            className="matrix-filter-select"
            aria-label="Lọc theo trạng thái phòng"
          >
            <option value="all">Tất cả phòng trọ</option>
            <option value="available">Còn phòng / Đang tìm ở ghép</option>
            <option value="rented">Đã cho thuê</option>
          </select>
        </div>
      </div>

      {/* Empty State */}
      {items.length === 0 && (
        <div className="matrix-empty-state">
          <div className="empty-icon"><IconHousing size={32} color="#64748B" /></div>
          <h3>Chưa tìm thấy phòng trọ phù hợp</h3>
          <p>Thử tìm kiếm với khu vực khác gần Học viện Ngân hàng.</p>
        </div>
      )}

      {/* Housing Items Matrix Grid */}
      <div className="housing-grid-matrix">
        {items.map((room) => (
          <article
            key={room.id}
            className={`housing-card ${room.status === "rented" ? "room-rented" : ""}`}
          >
            {/* Image Wrap */}
            <div className="room-image-wrap">
              <img src={room.image} alt={room.title} loading="lazy" />

              <div className="rent-badge-overlay">{room.rentPerMonth}</div>

              <div className="area-badge-overlay">📐 {room.area}</div>

              <span className={`room-status-tag status-${room.status}`}>
                {room.status === "available" ? "Còn phòng" : "Đã cho thuê"}
              </span>
            </div>

            {/* Content Body */}
            <div className="room-card-body">
              <div className="room-time-meta">
                <span>Cách HVNH {room.distanceToSchool}</span>
                <small>{room.createdAt}</small>
              </div>

              <h3 className="room-card-title">{room.title}</h3>

              <div className="room-address-text">
                <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="#64748B" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ display: 'inline-block', verticalAlign: 'middle', marginRight: 4 }}>
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                  <circle cx="12" cy="10" r="3" />
                </svg>
                <span>{room.address}</span>
              </div>

              {/* Amenity Chips */}
              <div className="amenity-chips-wrap">
                {room.amenities.map((amenity) => (
                  <span key={amenity} className="amenity-chip">
                    ✓ {amenity}
                  </span>
                ))}
              </div>

              {/* Landlord Contact & Action Bar */}
              <div className="room-card-footer">
                <div className="landlord-meta" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <img src="/assets/logo.png" alt={room.landlordName} className="author-avatar-img" />
                  <div>
                    <strong>{room.landlordName}</strong>
                    <small>LH: {room.landlordPhone}</small>
                  </div>
                </div>

                <div className="room-actions-flex">
                  <button
                    type="button"
                    className="contact-landlord-btn"
                    disabled={room.status === "rented"}
                    onClick={() => onContactLandlord(room.landlordName, room.landlordPhone)}
                  >
                    <span>Liên hệ</span>
                  </button>

                  <button
                    type="button"
                    className="view-map-btn"
                    onClick={() =>
                      alert(`Xem vị trí phòng trọ trên bản đồ: ${room.address}`)
                    }
                  >
                    <span>Bản đồ</span>
                  </button>
                </div>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

