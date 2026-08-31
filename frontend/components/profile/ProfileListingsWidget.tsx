"use client";

import React from 'react';
import { UserListing, ProfileTabType } from '@/types/user';

interface ProfileListingsWidgetProps {
  listings: UserListing[];
  onSeeAllListings: (tab: ProfileTabType) => void;
}

export default function ProfileListingsWidget({
  listings,
  onSeeAllListings,
}: ProfileListingsWidgetProps) {
  const activeListings = listings.filter((l) => l.status === 'active').slice(0, 3);

  const getCategoryBadge = (cat: string) => {
    switch (cat) {
      case 'market':
        return { label: 'Pass đồ', className: 'badge-market' };
      case 'roommate':
        return { label: 'Trọ / Ghép phòng', className: 'badge-roommate' };
      case 'event':
        return { label: 'Sự kiện', className: 'badge-event' };
      default:
        return { label: 'Niêm yết', className: 'badge-default' };
    }
  };

  return (
    <div className="profile-widget-card listings-widget">
      <div className="widget-header-row">
        <div className="widget-title-group">
          <h2 className="widget-title">Bài niêm yết đang hoạt động</h2>
          <span className="widget-count-tag">{activeListings.length} mục</span>
        </div>
        <button
          type="button"
          className="widget-see-all-link"
          onClick={() => onSeeAllListings('listings')}
        >
          Xem tất cả
        </button>
      </div>

      {activeListings.length > 0 ? (
        <div className="listings-mini-cards-stack">
          {activeListings.map((item) => {
            const badge = getCategoryBadge(item.category);
            return (
              <div key={item.id} className="listing-mini-card">
                <div className="mini-card-thumb">
                  <img src={item.imageUrl} alt={item.title} />
                  <span className={`category-tag ${badge.className}`}>{badge.label}</span>
                </div>
                <div className="mini-card-info">
                  <h3 className="mini-card-title">{item.title}</h3>
                  <span className="mini-card-price">{item.price}</span>
                  <span className="mini-card-location">📍 {item.location}</span>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="widget-empty-text">Hiện chưa có bài niêm yết nào đang hoạt động.</p>
      )}
    </div>
  );
}
