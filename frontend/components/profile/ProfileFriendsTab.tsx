"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { UserFriend } from '@/types/user';
import { IconSearch } from '@/components/ui/Icons';
import UserAvatar from '@/components/ui/UserAvatar';

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
  const [city, setCity] = useState('');
  const [hometown, setHometown] = useState('');
  const cities = [...new Set(friends.map(friend => friend.currentCity?.trim()).filter((value): value is string => Boolean(value)))].sort();
  const hometowns = [...new Set(friends.map(friend => friend.hometown?.trim()).filter((value): value is string => Boolean(value)))].sort();
  const sortedFriends = [...friends].sort((a, b) => (b.connectedAt || '').localeCompare(a.connectedAt || ''));
  const recentIds = new Set(sortedFriends.slice(0, 12).map(friend => friend.id));
  const filteredFriends = sortedFriends.filter((f) => {
    const matchesSearch =
      f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.username.toLowerCase().includes(searchQuery.toLowerCase());
    if (!matchesSearch || (city && f.currentCity !== city) || (hometown && f.hometown !== hometown)) return false;

    if (filter === 'recent') return recentIds.has(f.id);
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
        </div>
        <div className="friends-location-filters">
          <label>Thành phố hiện tại <select value={city} onChange={event => setCity(event.target.value)}><option value="">Tất cả</option>{cities.map(value => <option key={value} value={value}>{value}</option>)}</select></label>
          <label>Quê quán <select value={hometown} onChange={event => setHometown(event.target.value)}><option value="">Tất cả</option>{hometowns.map(value => <option key={value} value={value}>{value}</option>)}</select></label>
        </div>
      </div>

      {/* Friends Card Matrix Grid */}
      {filteredFriends.length > 0 ? (
        <div className="friends-matrix-grid">
          {filteredFriends.map((friend) => (
            <div key={friend.id} className="friend-matrix-card">
              <Link href={`/profile/${friend.id}`} className="friend-card-avatar-link">
                <UserAvatar src={friend.avatar} name={friend.name} imageClassName="friend-matrix-avatar" fallbackClassName="friend-matrix-avatar user-avatar-initials" />
                {friend.isOnline && <span className="avatar-online-dot" title="Đang hoạt động" />}
              </Link>

              <div className="friend-card-details">
                <Link href={`/profile/${friend.id}`} className="friend-card-name">
                  {friend.name}
                </Link>
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
              : 'Hãy thử bỏ bộ lọc hoặc tìm bằng tên khác.'}
          </p>
        </div>
      )}
    </div>
  );
}

