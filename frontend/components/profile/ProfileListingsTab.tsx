"use client";

import React, { useState } from 'react';
import { UserListing } from '@/types/user';

interface ProfileListingsTabProps {
  listings: UserListing[];
  isOwnProfile: boolean;
  categoryFilter: string;
  onCategoryChange: (category: string) => void;
}

export default function ProfileListingsTab({
  listings,
  isOwnProfile,
  categoryFilter,
  onCategoryChange,
}: ProfileListingsTabProps) {
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'sold'>('all');

  const filteredListings = listings.filter((item) => {
    if (categoryFilter !== 'all' && item.category !== categoryFilter) return false;
    if (statusFilter === 'active' && item.status !== 'active') return false;
    if (statusFilter === 'sold' && item.status === 'active') return false;
    return true;
  });

  const getCategoryBadge = (cat: string) => {
    switch (cat) {
      case 'market':
        return { label: 'Pass đồ', className: 'badge-market' };
      case 'roommate':
        return { label: 'Trọ / Ghép phòng', className: 'badge-roommate' };
      case 'event':
        return { label: 'Sự kiện', className: 'badge-event' };
      default:
        return { label: 'Bài niêm yết', className: 'badge-default' };
    }
  };

  const getStatusBadge = (status: string, category: string) => {
    if (status === 'sold') {
      return category === 'roommate'
        ? { label: 'Đã cho thuê', className: 'status-badge-sold' }
        : { label: 'Đã bán', className: 'status-badge-sold' };
    }
    return { label: 'Đang hiển thị', className: 'status-badge-active' };
  };

  return (
    <div className="profile-listings-tab-container">
      {/* Header Bar */}
      <div className="listings-header-card">
        <div className="title-group">
          <h2 className="tab-main-title">Bài niêm yết của tôi</h2>
          <span className="listings-count-pill">{listings.length} bài đăng</span>
        </div>

        <div className="subnav-filter-tabs">
          <button
            type="button"
            className={`subnav-tab ${categoryFilter === 'all' ? 'active' : ''}`}
            onClick={() => onCategoryChange('all')}
          >
            Tất cả danh mục
          </button>
          <button
            type="button"
            className={`subnav-tab ${categoryFilter === 'market' ? 'active' : ''}`}
            onClick={() => onCategoryChange('market')}
          >
            Pass đồ (Marketplace)
          </button>
          <button
            type="button"
            className={`subnav-tab ${categoryFilter === 'roommate' ? 'active' : ''}`}
            onClick={() => onCategoryChange('roommate')}
          >
            Tìm trọ / Ghép phòng
          </button>
          <button
            type="button"
            className={`subnav-tab ${categoryFilter === 'event' ? 'active' : ''}`}
            onClick={() => onCategoryChange('event')}
          >
            Sự kiện
          </button>
        </div>
      </div>

      {/* Sub-status filter row */}
      <div className="status-filter-pills-row">
        <button
          type="button"
          className={`status-pill ${statusFilter === 'all' ? 'active' : ''}`}
          onClick={() => setStatusFilter('all')}
        >
          Tất cả trạng thái
        </button>
        <button
          type="button"
          className={`status-pill ${statusFilter === 'active' ? 'active' : ''}`}
          onClick={() => setStatusFilter('active')}
        >
          Đang hiển thị
        </button>
        <button
          type="button"
          className={`status-pill ${statusFilter === 'sold' ? 'active' : ''}`}
          onClick={() => setStatusFilter('sold')}
        >
          Đã bán / Đã cho thuê
        </button>
      </div>

      {/* Matrix Cards Grid */}
      {filteredListings.length > 0 ? (
        <div className="listings-cards-matrix">
          {filteredListings.map((item) => {
            const catBadge = getCategoryBadge(item.category);
            const statusBadge = getStatusBadge(item.status, item.category);
            return (
              <div key={item.id} className="listing-matrix-card">
                <div className="listing-card-image-wrap">
                  <img src={item.imageUrl} alt={item.title} />
                  <span className={`category-tag ${catBadge.className}`}>{catBadge.label}</span>
                  <span className={`status-tag-badge ${statusBadge.className}`}>{statusBadge.label}</span>
                </div>

                <div className="listing-card-content">
                  <span className="listing-card-date">{item.createdAt}</span>
                  <h3 className="listing-card-title">{item.title}</h3>
                  <div className="listing-card-price-row">
                    <span className="listing-card-price">{item.price}</span>
                  </div>
                  <p className="listing-card-location">📍 {item.location}</p>

                  {isOwnProfile && (
                    <div className="listing-card-owner-actions">
                      <button type="button" className="btn btn-secondary btn-sm">
                        <span>Chỉnh sửa</span>
                      </button>
                      <button type="button" className="btn btn-secondary btn-sm">
                        <span>{item.status === 'active' ? 'Đánh dấu đã bán' : 'Kích hoạt lại'}</span>
                      </button>
                      <button type="button" className="btn btn-secondary btn-sm text-danger">
                        <span>Xóa</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="empty-listings-card">
          <h3 className="empty-title">Không tìm thấy bài niêm yết nào</h3>
          <p className="empty-desc">Bạn chưa đăng bài niêm yết nào trong danh mục này.</p>
        </div>
      )}
    </div>
  );
}
