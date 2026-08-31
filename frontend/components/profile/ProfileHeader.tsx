"use client";

import React, { useState, useRef } from 'react';
import Link from 'next/link';
import { UserProfile, ProfileTabType } from '@/types/user';
import ProfileNavTabs from './ProfileNavTabs';

interface ProfileHeaderProps {
  profile: UserProfile;
  isOwnProfile: boolean;
  activeTab: ProfileTabType;
  onTabChange: (tab: ProfileTabType) => void;
  onOpenEditModal: () => void;
  onFriendAction: (action: 'add' | 'accept' | 'reject' | 'unfriend' | 'cancel') => void;
  onUpdateAvatarPhoto?: (newAvatarUrl: string) => void;
}

export default function ProfileHeader({
  profile,
  isOwnProfile,
  activeTab,
  onTabChange,
  onOpenEditModal,
  onFriendAction,
  onUpdateAvatarPhoto,
}: ProfileHeaderProps) {
  const [isOptionsMenuOpen, setIsOptionsMenuOpen] = useState(false);
  const avatarInputRef = useRef<HTMLInputElement | null>(null);

  const handleAvatarFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      alert('Vui lòng chọn tệp định dạng ảnh (JPEG, PNG, WEBP).');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      alert('Kích thước ảnh tối đa 5MB.');
      return;
    }

    const localPreviewUrl = URL.createObjectURL(file);
    if (onUpdateAvatarPhoto) {
      onUpdateAvatarPhoto(localPreviewUrl);
    } else {
      onOpenEditModal();
    }
  };

  const renderFriendActionButton = () => {
    switch (profile.friendshipStatus) {
      case 'friends':
        return (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => onFriendAction('unfriend')}
          >
            <span>Bạn bè</span>
          </button>
        );
      case 'pending_sent':
        return (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => onFriendAction('cancel')}
          >
            <span>Đã gửi lời mời</span>
          </button>
        );
      case 'pending_received':
        return (
          <div className="friend-request-action-group">
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => onFriendAction('accept')}
            >
              <span>Xác nhận</span>
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => onFriendAction('reject')}
            >
              <span>Xóa</span>
            </button>
          </div>
        );
      case 'none':
      default:
        return (
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => onFriendAction('add')}
          >
            <span>Thêm bạn bè</span>
          </button>
        );
    }
  };

  return (
    <header className="profile-header-container">
      {/* Hidden Native Avatar File Input */}
      <input
        ref={avatarInputRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={handleAvatarFileChange}
      />

      {/* Elevated Profile Info Card */}
      <div className="profile-info-section">
        <div className="profile-info-content">
          {/* Avatar Container with Online Indicator */}
          <div className="profile-avatar-wrapper">
            <img
              src={profile.avatar}
              alt={profile.name}
              className="profile-avatar-img"
            />
            {profile.isOnline && (
              <span className="avatar-online-badge" title="Đang hoạt động" />
            )}
            {isOwnProfile && (
              <button
                type="button"
                className="edit-avatar-badge-btn text-only-badge"
                onClick={() => avatarInputRef.current?.click()}
                aria-label="Chỉnh sửa ảnh đại diện"
              >
                <span>Đổi ảnh</span>
              </button>
            )}
          </div>

          {/* Identity Info */}
          <div className="profile-identity-details">
            <div className="name-and-verification">
              <h1 className="profile-full-name">{profile.name}</h1>
              {profile.isVerified && (
                <span className="verified-badge-check" title="Tài khoản sinh viên HVNH đã xác thực">
                  ✓
                </span>
              )}
            </div>

            <div className="profile-sub-meta">
              <span className="profile-username">@{profile.username}</span>
              {profile.faculty && <span className="meta-bullet-dot">•</span>}
              {profile.faculty && <span className="profile-faculty-tag">{profile.faculty}</span>}
            </div>

            {profile.bio && <p className="profile-bio-snippet">{profile.bio}</p>}
          </div>

          {/* Text-Only Action Buttons Row */}
          <div className="profile-actions-wrapper">
            {isOwnProfile ? (
              <button
                type="button"
                className="btn btn-primary"
                onClick={onOpenEditModal}
              >
                <span>Chỉnh sửa trang cá nhân</span>
              </button>
            ) : (
              <>
                {renderFriendActionButton()}
                <Link
                  href={`/messages?userId=${profile.id}`}
                  className="btn btn-primary"
                >
                  <span>Nhắn tin</span>
                </Link>
                <div className="options-dropdown-container">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setIsOptionsMenuOpen(!isOptionsMenuOpen)}
                    aria-label="Tùy chọn khác"
                  >
                    <span>Tùy chọn</span>
                  </button>
                  {isOptionsMenuOpen && (
                    <div className="options-menu-popup">
                      <button
                        type="button"
                        className="menu-item"
                        onClick={() => {
                          navigator.clipboard.writeText(window.location.href);
                          setIsOptionsMenuOpen(false);
                        }}
                      >
                        <span>Sao chép liên kết trang cá nhân</span>
                      </button>
                      <button
                        type="button"
                        className="menu-item danger"
                        onClick={() => setIsOptionsMenuOpen(false)}
                      >
                        <span>Chặn người dùng</span>
                      </button>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>

        <div className="header-divider-line" />

        {/* Horizontal Navigation Tabs */}
        <ProfileNavTabs
          activeTab={activeTab}
          onTabChange={onTabChange}
          friendsCount={profile.friendsCount}
        />
      </div>
    </header>
  );
}

