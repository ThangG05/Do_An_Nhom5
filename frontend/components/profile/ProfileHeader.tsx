"use client";

import React, { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { UserProfile, ProfileTabType } from '@/types/user';
import ProfileNavTabs from './ProfileNavTabs';
import { safeImageSrc } from '@/lib/media';
import { useDialog } from '@/components/ui/DialogProvider';
import { IconMoreDots } from '@/components/ui/Icons';

interface ProfileHeaderProps {
  profile: UserProfile;
  isOwnProfile: boolean;
  activeTab: ProfileTabType;
  onTabChange: (tab: ProfileTabType) => void;
  onOpenEditModal: () => void;
  onFriendAction: (action: 'add' | 'accept' | 'reject' | 'unfriend' | 'cancel') => Promise<void>;
  onUpdateAvatarPhoto?: (newAvatarUrl: string) => void;
  onMessage?: () => void;
  onReport?: () => Promise<void>;
  onBlock?: () => Promise<void>;
}

export default function ProfileHeader({
  profile,
  isOwnProfile,
  activeTab,
  onTabChange,
  onOpenEditModal,
  onFriendAction,
  onUpdateAvatarPhoto,
  onMessage,
  onReport,
  onBlock,
}: ProfileHeaderProps) {
  const dialog = useDialog();
  const [isOptionsMenuOpen, setIsOptionsMenuOpen] = useState(false);
  const [isAvatarViewerOpen, setIsAvatarViewerOpen] = useState(false);
  const [friendActionPending, setFriendActionPending] = useState(false);
  const avatarInputRef = useRef<HTMLInputElement | null>(null);
  const optionsRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (!isOptionsMenuOpen) return;
    const close = (event: MouseEvent) => { if (!optionsRef.current?.contains(event.target as Node)) setIsOptionsMenuOpen(false); };
    const escape = (event: KeyboardEvent) => { if (event.key === 'Escape') setIsOptionsMenuOpen(false); };
    document.addEventListener('mousedown', close);
    document.addEventListener('keydown', escape);
    return () => { document.removeEventListener('mousedown', close); document.removeEventListener('keydown', escape); };
  }, [isOptionsMenuOpen]);

  const handleAvatarFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      dialog.notify({title:'Tệp không hợp lệ',message:'Vui lòng chọn ảnh JPEG, PNG hoặc WEBP.',tone:'danger'});
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      dialog.notify({title:'Ảnh quá lớn',message:'Kích thước ảnh tối đa là 5 MB.',tone:'danger'});
      return;
    }

    const localPreviewUrl = URL.createObjectURL(file);
    if (onUpdateAvatarPhoto) {
      onUpdateAvatarPhoto(localPreviewUrl);
    } else {
      onOpenEditModal();
    }
  };

  const runFriendAction = async (action: 'add' | 'accept' | 'reject' | 'unfriend' | 'cancel') => {
    if (friendActionPending) return;
    setFriendActionPending(true);
    try {
      await onFriendAction(action);
    } catch (error) {
      dialog.notify({
        title: 'Không thể cập nhật quan hệ bạn bè',
        message: error instanceof Error ? error.message : 'Vui lòng thử lại sau.',
        tone: 'danger',
      });
    } finally {
      setFriendActionPending(false);
    }
  };

  const renderFriendActionButton = () => {
    switch (profile.friendshipStatus) {
      case 'friends':
        return (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => runFriendAction('unfriend')}
            disabled={friendActionPending}
          >
            <span>Bạn bè</span>
          </button>
        );
      case 'pending_sent':
        return (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => runFriendAction('cancel')}
            disabled={friendActionPending}
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
              onClick={() => runFriendAction('accept')}
              disabled={friendActionPending}
            >
              <span>Xác nhận</span>
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => runFriendAction('reject')}
              disabled={friendActionPending}
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
            onClick={() => runFriendAction('add')}
            disabled={friendActionPending}
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

      <div className="profile-cover-banner">
        <img src={safeImageSrc(profile.coverBanner)} alt={`Ảnh bìa của ${profile.name}`} className="cover-banner-img" />
        <div className="cover-banner-gradient-overlay" aria-hidden="true" />
      </div>

      {/* Elevated Profile Info Card */}
      <div className="profile-info-section">
        <div className="profile-info-content">
          {/* Avatar Container with Online Indicator */}
          <button type="button" className="profile-avatar-wrapper profile-avatar-button" onClick={() => setIsAvatarViewerOpen(true)} aria-label={`Xem ảnh đại diện của ${profile.name}`}>
            <img
              src={safeImageSrc(profile.avatar)}
              alt={profile.name}
              className="profile-avatar-img"
            />
            {profile.isOnline && (
              <span className="avatar-online-badge" title="Đang hoạt động" />
            )}
          </button>

          {/* Identity Info */}
          <div className="profile-identity-details">
            <div className="name-and-verification">
              <h1 className="profile-full-name">{profile.name}</h1>
            </div>

            <div className="profile-sub-meta">
              <span className="profile-username">Mã sinh viên: {profile.studentCode || profile.username}</span>
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
                {onMessage ? <button type="button" className="btn btn-primary" onClick={onMessage}>Nhắn tin</button> : <Link href={`/messages?userId=${profile.id}`} className="btn btn-primary">Nhắn tin</Link>}
                <div className="options-dropdown-container" ref={optionsRef}>
                  <button
                    type="button"
                    className="btn btn-secondary profile-options-trigger"
                    onClick={() => setIsOptionsMenuOpen(!isOptionsMenuOpen)}
                    aria-label="Tùy chọn trang cá nhân"
                    aria-expanded={isOptionsMenuOpen}
                    aria-haspopup="menu"
                  >
                    <IconMoreDots size={21} />
                  </button>
                  {isOptionsMenuOpen && (
                    <div className="options-menu-popup" role="menu">
                      {onReport && <button type="button" role="menuitem" className="menu-item" onClick={() => { setIsOptionsMenuOpen(false); void onReport(); }}><span aria-hidden="true">⚑</span><span>Báo cáo trang cá nhân</span></button>}
                      {onBlock && <button type="button" role="menuitem" className="menu-item danger" onClick={() => { setIsOptionsMenuOpen(false); void onBlock(); }}><span aria-hidden="true">⊘</span><span>Chặn người dùng</span></button>}
                      <button
                        type="button"
                        role="menuitem"
                        className="menu-item"
                        onClick={async () => {
                          try {
                            await navigator.clipboard.writeText(window.location.href);
                            dialog.notify({ title: 'Đã sao chép liên kết', message: 'Bạn có thể gửi liên kết trang cá nhân này cho người khác.', tone: 'success' });
                          } catch {
                            dialog.notify({ title: 'Không thể sao chép', message: 'Trình duyệt chưa cấp quyền truy cập bộ nhớ tạm.', tone: 'danger' });
                          }
                          setIsOptionsMenuOpen(false);
                        }}
                      >
                        <span aria-hidden="true">🔗</span><span>Sao chép liên kết trang cá nhân</span>
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
      {isAvatarViewerOpen && <div className="profile-avatar-viewer" role="presentation" onClick={() => setIsAvatarViewerOpen(false)}><section role="dialog" aria-modal="true" aria-label="Ảnh đại diện" onClick={(event) => event.stopPropagation()}><button type="button" className="profile-avatar-viewer-close" onClick={() => setIsAvatarViewerOpen(false)} aria-label="Đóng">×</button><img src={safeImageSrc(profile.avatar)} alt={`Ảnh đại diện của ${profile.name}`}/>{isOwnProfile && <button type="button" className="profile-avatar-change-action" onClick={() => { setIsAvatarViewerOpen(false); onOpenEditModal(); }}>Đổi ảnh đại diện</button>}</section></div>}
    </header>
  );
}

