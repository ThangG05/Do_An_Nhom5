"use client";

import React, { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { UserProfile, ProfileTabType } from '@/types/user';
import ProfileNavTabs from './ProfileNavTabs';
import ProfileImageViewer from './ProfileImageViewer';
import type { ProfileEditSection } from './EditProfileModal';
import { safeImageSrc } from '@/lib/media';
import { useDialog } from '@/components/ui/DialogProvider';
import { IconChevronDown, IconMoreDots } from '@/components/ui/Icons';

interface ProfileHeaderProps {
  profile: UserProfile;
  isOwnProfile: boolean;
  activeTab: ProfileTabType;
  onTabChange: (tab: ProfileTabType) => void;
  onOpenEditModal: (section?: ProfileEditSection) => void;
  onFriendAction: (action: 'add' | 'accept' | 'reject' | 'unfriend' | 'cancel') => Promise<void>;
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
  onMessage,
  onReport,
  onBlock,
}: ProfileHeaderProps) {
  const dialog = useDialog();
  const [isOptionsMenuOpen, setIsOptionsMenuOpen] = useState(false);
  const [isFriendMenuOpen, setIsFriendMenuOpen] = useState(false);
  const [viewingImage, setViewingImage] = useState<'avatar' | 'cover' | null>(null);
  const [friendActionPending, setFriendActionPending] = useState(false);
  const optionsRef = useRef<HTMLDivElement | null>(null);
  const friendMenuRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (!isOptionsMenuOpen) return;
    const close = (event: MouseEvent) => { if (!optionsRef.current?.contains(event.target as Node)) setIsOptionsMenuOpen(false); };
    const escape = (event: KeyboardEvent) => { if (event.key === 'Escape') setIsOptionsMenuOpen(false); };
    document.addEventListener('mousedown', close);
    document.addEventListener('keydown', escape);
    return () => { document.removeEventListener('mousedown', close); document.removeEventListener('keydown', escape); };
  }, [isOptionsMenuOpen]);
  useEffect(() => {
    if (!isFriendMenuOpen) return;
    const close = (event: MouseEvent) => { if (!friendMenuRef.current?.contains(event.target as Node)) setIsFriendMenuOpen(false); };
    const escape = (event: KeyboardEvent) => { if (event.key === 'Escape') setIsFriendMenuOpen(false); };
    document.addEventListener('mousedown', close);
    document.addEventListener('keydown', escape);
    return () => { document.removeEventListener('mousedown', close); document.removeEventListener('keydown', escape); };
  }, [isFriendMenuOpen]);

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
    if (profile.accountStatus && profile.accountStatus !== 'ACTIVE' && profile.friendshipStatus !== 'friends') return null;
    switch (profile.friendshipStatus) {
      case 'friends':
        return (
          <div className="options-dropdown-container profile-friend-menu" ref={friendMenuRef}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsFriendMenuOpen(value => !value)} disabled={friendActionPending} aria-expanded={isFriendMenuOpen} aria-haspopup="menu">
              <span>Bạn bè</span><IconChevronDown size={16} className={`dropdown-chevron ${isFriendMenuOpen ? 'is-open' : ''}`} />
            </button>
            {isFriendMenuOpen && <div className="options-menu-popup" role="menu">
              <button type="button" role="menuitem" className="menu-item danger" onClick={async () => {
                setIsFriendMenuOpen(false);
                if (await dialog.confirm({ title: 'Hủy kết bạn?', message: `Bạn và ${profile.name} sẽ không còn trong danh sách bạn bè.`, confirmLabel: 'Hủy kết bạn', tone: 'danger' })) void runFriendAction('unfriend');
              }}>Hủy kết bạn</button>
            </div>}
          </div>
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
      <div className="profile-cover-banner">
        <button type="button" className="profile-cover-view" onClick={() => setViewingImage('cover')} aria-label={`Xem ảnh bìa của ${profile.name}`}>
          <img src={safeImageSrc(profile.coverBanner)} alt={`Ảnh bìa của ${profile.name}`} className="cover-banner-img" />
          <span className="cover-banner-gradient-overlay" aria-hidden="true" />
          <span className="profile-cover-view-label" aria-hidden="true">Xem ảnh bìa</span>
        </button>
        {isOwnProfile && <button type="button" className="profile-cover-edit" onClick={() => onOpenEditModal('cover')}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M4 6h4l2-3h4l2 3h4a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1Z" /><circle cx="12" cy="12" r="4" /></svg>
          <span>Đổi ảnh bìa</span>
        </button>}
      </div>

      {/* Elevated Profile Info Card */}
      <div className="profile-info-section">
        <div className="profile-info-content">
          {/* Avatar Container with Online Indicator */}
          <button type="button" className="profile-avatar-wrapper profile-avatar-button" onClick={() => setViewingImage('avatar')} aria-label={`Xem ảnh đại diện của ${profile.name}`}>
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
              {profile.accountStatus && profile.accountStatus !== 'ACTIVE' && <span className="profile-faculty-tag">Tài khoản tạm ngừng hoạt động</span>}
            </div>

            {profile.bio && <p className="profile-bio-snippet">{profile.bio}</p>}
          </div>

          {/* Text-Only Action Buttons Row */}
          <div className="profile-actions-wrapper">
            {isOwnProfile ? (
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => onOpenEditModal()}
              >
                <span>Chỉnh sửa trang cá nhân</span>
              </button>
            ) : (
              <>
                {renderFriendActionButton()}
                {(!profile.accountStatus || profile.accountStatus === 'ACTIVE') && (onMessage ? <button type="button" className="btn btn-primary" onClick={onMessage}>Nhắn tin</button> : <Link href={`/messages?userId=${profile.id}`} className="btn btn-primary">Nhắn tin</Link>)}
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
      {viewingImage && <ProfileImageViewer
        key={`${profile.id}-${viewingImage}`}
        src={viewingImage === 'cover' ? profile.coverBanner : profile.avatar}
        name={profile.name}
        kind={viewingImage}
        onClose={() => setViewingImage(null)}
        onEdit={isOwnProfile ? () => { setViewingImage(null); onOpenEditModal(viewingImage); } : undefined}
      />}
    </header>
  );
}

