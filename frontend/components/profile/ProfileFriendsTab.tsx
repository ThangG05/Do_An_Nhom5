"use client";

import { useState } from 'react';
import Link from 'next/link';
import { updateFriendshipStatus } from '@/lib/api';
import { useAuthUser } from '@/components/auth/AuthProvider';
import UserAvatar from '@/components/ui/UserAvatar';
import { IconSearch } from '@/components/ui/Icons';
import type { FriendshipStatus, UserFriend } from '@/types/user';

interface ProfileFriendsTabProps {
  friends: UserFriend[];
  isOwnProfile: boolean;
  searchQuery: string;
  filter: string;
  onSearchChange: (query: string) => void;
  onFilterChange: (filter: string) => void;
  onUnfriend?: (friendId: string) => void;
}

const RECENT_DAYS = 7;

function normalizeLocation(value?: string | null) {
  const location = value?.trim() || '';
  return /^hà\s+lội$/iu.test(location) || /^hà\s+nội$/iu.test(location) ? 'Hà Nội' : location;
}

export default function ProfileFriendsTab({
  friends, isOwnProfile, searchQuery, filter, onSearchChange, onFilterChange, onUnfriend,
}: ProfileFriendsTabProps) {
  const viewer = useAuthUser();
  const [city, setCity] = useState('');
  const [hometown, setHometown] = useState('');
  const [statusOverrides, setStatusOverrides] = useState<Record<string, FriendshipStatus>>({});
  const [busyId, setBusyId] = useState<string | null>(null);
  const [actionError, setActionError] = useState('');
  const effectiveFilter = isOwnProfile ? filter : 'all';
  const cities = [...new Set(friends.map(friend => normalizeLocation(friend.currentCity)).filter(Boolean))].sort();
  const hometowns = [...new Set(friends.map(friend => normalizeLocation(friend.hometown)).filter(Boolean))].sort();
  const recentCutoff = Date.now() - RECENT_DAYS * 24 * 60 * 60 * 1000;
  const filteredFriends = [...friends]
    .sort((a, b) => (b.connectedAt || '').localeCompare(a.connectedAt || ''))
    .filter(friend => {
      const query = searchQuery.toLocaleLowerCase().trim();
      if (query && !friend.name.toLocaleLowerCase().includes(query) && !friend.username.toLocaleLowerCase().includes(query)) return false;
      if (city && normalizeLocation(friend.currentCity) !== city) return false;
      if (hometown && normalizeLocation(friend.hometown) !== hometown) return false;
      if (effectiveFilter === 'recent') {
        const connectedAt = friend.connectedAt ? Date.parse(friend.connectedAt) : NaN;
        return Number.isFinite(connectedAt) && connectedAt >= recentCutoff;
      }
      return true;
    });

  const actOnFriend = async (friendId: string, action: 'add' | 'accept' | 'cancel') => {
    setBusyId(friendId);
    setActionError('');
    try {
      const result = await updateFriendshipStatus(friendId, action);
      setStatusOverrides(previous => ({ ...previous, [friendId]: result.status }));
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Không thể cập nhật lời mời kết bạn.');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="profile-friends-tab-container">
      <div className="friends-header-card">
        <div className="header-top-row">
          <div className="title-group">
            <h2 className="tab-main-title">Bạn bè</h2>
            <span className="friends-count-pill">{friends.length} người bạn</span>
          </div>
          <div className="friends-search-box">
            <IconSearch size={16} color="#64748B" className="search-icon-svg" />
            <input type="search" className="friends-search-input" placeholder="Tìm kiếm bạn bè..." value={searchQuery} onChange={event => onSearchChange(event.target.value)} />
          </div>
        </div>
        <div className="subnav-filter-tabs">
          <button type="button" className={`subnav-tab ${effectiveFilter === 'all' ? 'active' : ''}`} onClick={() => onFilterChange('all')}>Tất cả bạn bè</button>
          {isOwnProfile && <button type="button" className={`subnav-tab ${effectiveFilter === 'recent' ? 'active' : ''}`} onClick={() => onFilterChange('recent')} title={`Kết bạn trong ${RECENT_DAYS} ngày qua`}>Đã thêm gần đây · {RECENT_DAYS} ngày</button>}
        </div>
        <div className="friends-location-filters">
          <label>Thành phố hiện tại <select value={city} onChange={event => setCity(event.target.value)}><option value="">Tất cả</option>{cities.map(value => <option key={value} value={value}>{value}</option>)}</select></label>
          <label>Quê quán <select value={hometown} onChange={event => setHometown(event.target.value)}><option value="">Tất cả</option>{hometowns.map(value => <option key={value} value={value}>{value}</option>)}</select></label>
        </div>
      </div>

      {actionError && <p className="friends-action-error" role="alert">{actionError}</p>}
      {filteredFriends.length ? (
        <div className="friends-matrix-grid">
          {filteredFriends.map(friend => {
            const status = friend.id === viewer?.id ? 'self' : statusOverrides[friend.id] || friend.friendshipStatus;
            return <div key={friend.id} className="friend-matrix-card">
              <Link href={`/profile/${friend.id}`} className="friend-card-avatar-link">
                <UserAvatar src={friend.avatar} name={friend.name} imageClassName="friend-matrix-avatar" fallbackClassName="friend-matrix-avatar user-avatar-initials" />
                {friend.isOnline && <span className="avatar-online-dot" title="Đang hoạt động" />}
              </Link>
              <div className="friend-card-details">
                <Link href={`/profile/${friend.id}`} className="friend-card-name">{friend.name}</Link>
                {friend.faculty && <span className="friend-card-faculty">{friend.faculty}</span>}
                {friend.mutualCount > 0 && <span className="friend-card-mutual">{friend.mutualCount} bạn chung</span>}
              </div>
              <div className="friend-card-actions">
                {status === 'friends' && <Link href={`/messages?userId=${friend.id}`} className="btn btn-secondary btn-sm">Nhắn tin</Link>}
                {!isOwnProfile && status === 'none' && <button type="button" className="btn btn-primary btn-sm" disabled={busyId === friend.id} onClick={() => void actOnFriend(friend.id, 'add')}>Thêm bạn bè</button>}
                {!isOwnProfile && status === 'pending_sent' && <button type="button" className="btn btn-secondary btn-sm" disabled={busyId === friend.id} onClick={() => void actOnFriend(friend.id, 'cancel')}>Hủy lời mời</button>}
                {!isOwnProfile && status === 'pending_received' && <button type="button" className="btn btn-primary btn-sm" disabled={busyId === friend.id} onClick={() => void actOnFriend(friend.id, 'accept')}>Chấp nhận</button>}
                {isOwnProfile && status === 'friends' && onUnfriend && <button type="button" className="btn btn-secondary btn-sm" onClick={() => onUnfriend(friend.id)} title="Hủy kết bạn">Hủy kết bạn</button>}
              </div>
            </div>;
          })}
        </div>
      ) : (
        <div className="empty-friends-card">
          <h3 className="empty-title">Không tìm thấy bạn bè phù hợp</h3>
          <p className="empty-desc">{searchQuery ? `Không có kết quả nào khớp với "${searchQuery}".` : effectiveFilter === 'recent' ? `Không có bạn bè mới trong ${RECENT_DAYS} ngày qua.` : 'Hãy thử bỏ bộ lọc hoặc tìm bằng tên khác.'}</p>
        </div>
      )}
    </div>
  );
}
