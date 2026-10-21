"use client";

import React from 'react';
import Link from 'next/link';
import { UserFriend, ProfileTabType } from '@/types/user';
import UserAvatar from '@/components/ui/UserAvatar';

interface ProfileFriendsWidgetProps {
  friends: UserFriend[];
  friendsCount: number;
  isLoading?: boolean;
  error?: string;
  onRetry?: () => void;
  onSeeAllFriends: (tab: ProfileTabType) => void;
}

export default function ProfileFriendsWidget({
  friends,
  friendsCount,
  isLoading = false,
  error = '',
  onRetry,
  onSeeAllFriends,
}: ProfileFriendsWidgetProps) {
  const topFriends = friends.slice(0, 9);

  return (
    <div className="profile-widget-card friends-widget">
      <div className="widget-header-row">
        <div className="widget-title-group">
          <h2 className="widget-title">Bạn bè</h2>
          <span className="widget-count-tag">{isLoading ? 'Đang tải…' : `${friendsCount} người bạn`}</span>
        </div>
        <button
          type="button"
          className="widget-see-all-link"
          onClick={() => onSeeAllFriends('friends')}
        >
          Xem tất cả bạn bè
        </button>
      </div>

      {error ? (
        <div className="widget-empty-text" role="alert">
          <p>Không tải được danh sách bạn bè.</p>
          {onRetry && <button type="button" className="btn btn-secondary btn-sm" onClick={onRetry}>Thử lại</button>}
        </div>
      ) : isLoading ? (
        <p className="widget-empty-text" role="status">Đang tải danh sách bạn bè…</p>
      ) : topFriends.length > 0 ? (
        <div className="friends-grid-3x3">
          {topFriends.map((friend) => (
            <Link
              key={friend.id}
              href={`/profile/${friend.id}`}
              className="friend-grid-card"
            >
              <div className="friend-avatar-wrapper">
                <UserAvatar src={friend.avatar} name={friend.name} fallbackClassName="user-avatar-initials" />
                {friend.isOnline && <span className="online-indicator" />}
              </div>
              <span className="friend-name-label">{friend.name}</span>
            </Link>
          ))}
        </div>
      ) : (
        <p className="widget-empty-text">Chưa có bạn bè nào.</p>
      )}
    </div>
  );
}
