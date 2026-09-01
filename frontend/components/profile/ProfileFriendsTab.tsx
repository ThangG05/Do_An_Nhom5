"use client";

import React from 'react';
import Link from 'next/link';
import { UserFriend } from '@/types/user';
import { IconSearch } from '@/components/ui/Icons';

interface ProfileFriendsTabProps {
  friends: UserFriend[];
  isOwnProfile: boolean;
  searchQuery: string;
  filter: string;
  onSearchChange: (query: string) => void;
  onFilterChange: (filter: string) => void;
  onUnfriend?: (friendId: string) => void;
}

export default function ProfileFriendsTab({
  friends,
  isOwnProfile,
  searchQuery,
  filter,
  onSearchChange,
  onFilterChange,
  onUnfriend,
}: ProfileFriendsTabProps) {
  const filteredFriends = friends.filter((f) => {
    const matchesSearch =
      f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.username.toLowerCase().includes(searchQuery.toLowerCase());
    if (!matchesSearch) return false;

    if (filter === 'recent') return f.mutualCount > 20;
    if (filter === 'mutual') return f.mutualCount > 0;
    return true;
  });

  return (
    <div className="profile-friends-tab-container">
      {/* Header Bar with Search & Tabs */}
      <div className="friends-header-card">
        <div className="header-top-row">
          <div className="title-group">
            <h2 className="tab-main-title">Bạn bè</h2>
            <span className="friends-count-pill">{friends.length} người bạn</span>
          </div>

          <div className="friends-search-box">
            <IconSearch size={16} color="#64748B" className="search-icon-svg" />
            <input
              type="text"
              className="friends-search-input"
              placeholder="Tìm kiếm bạn bè..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
            />
          </div>
        </div>

        <div className="subnav-filter-tabs">
          <button
            type="button"
            className={`subnav-tab ${filter === 'all' ? 'active' : ''}`}
            onClick={() => onFilterChange('all')}
          >
            Tất cả bạn bè
          </button>
          <button
            type="button"
            className={`subnav-tab ${filter === 'recent' ? 'active' : ''}`}
            onClick={() => onFilterChange('recent')}
          >
            Đã thêm gần đây
          </button>
          <button
            type="button"
            className={`subnav-tab ${filter === 'mutual' ? 'active' : ''}`}
            onClick={() => onFilterChange('mutual')}
          >
            Bạn chung
          </button>
        </div>
      </div>

      {/* Friends Card Matrix Grid */}
      {filteredFriends.length > 0 ? (
        <div className="friends-matrix-grid">
          {filteredFriends.map((friend) => (
            <div key={friend.id} className="friend-matrix-card">
              <Link href={`/profile/${friend.id}`} className="friend-card-avatar-link">
                <img src={friend.avatar} alt={friend.name} className="friend-matrix-avatar" />
                {friend.isOnline && <span className="avatar-online-dot" title="Đang hoạt động" />}
              </Link>

              <div className="friend-card-details">
                <Link href={`/profile/${friend.id}`} className="friend-card-name">
                  {friend.name}
                </Link>
                <span className="friend-card-username">@{friend.username}</span>
                {friend.faculty && <span className="friend-card-faculty">{friend.faculty}</span>}
                {friend.mutualCount > 0 && (
                  <span className="friend-card-mutual">{friend.mutualCount} bạn chung</span>
                )}
              </div>

              <div className="friend-card-actions">
                <Link href={`/messages?userId=${friend.id}`} className="btn btn-secondary btn-sm">
                  <span>Nhắn tin</span>
                </Link>
                {isOwnProfile && onUnfriend && (
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => onUnfriend(friend.id)}
                    title="Hủy kết bạn"
                  >
                    <span>Hủy kết bạn</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-friends-card">
          <h3 className="empty-title">Không tìm thấy bạn bè phù hợp</h3>
          <p className="empty-desc">
            {searchQuery
              ? `Không có kết quả nào khớp với "${searchQuery}".`
              : 'Danh sách bạn bè trống.'}
          </p>
        </div>
      )}
    </div>
  );
}

