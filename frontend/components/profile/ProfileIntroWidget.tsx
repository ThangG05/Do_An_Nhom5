"use client";

import React, { useState } from 'react';
import { UserProfile } from '@/types/user';
import { IconHousing, IconInfo } from '@/components/ui/Icons';

interface ProfileIntroWidgetProps {
  profile: UserProfile;
  isOwnProfile: boolean;
  onUpdateBio: (newBio: string) => Promise<void>;
  onOpenEditModal: () => void;
}

export default function ProfileIntroWidget({
  profile,
  isOwnProfile,
  onUpdateBio,
  onOpenEditModal,
}: ProfileIntroWidgetProps) {
  const [isEditingBio, setIsEditingBio] = useState(false);
  const [bioInput, setBioInput] = useState(profile.bio || '');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSaveBio = async () => {
    setIsSubmitting(true);
    await onUpdateBio(bioInput);
    setIsSubmitting(false);
    setIsEditingBio(false);
  };

  return (
    <div className="profile-widget-card intro-widget">
      <h2 className="widget-title">Giới thiệu</h2>

      {/* Bio Statement */}
      <div className="widget-bio-section">
        {isEditingBio ? (
          <div className="bio-edit-box">
            <textarea
              className="bio-textarea"
              value={bioInput}
              onChange={(e) => setBioInput(e.target.value)}
              placeholder="Mô tả bản thân của bạn..."
              maxLength={150}
              rows={3}
            />
            <div className="bio-edit-footer">
              <span className="char-count">{150 - bioInput.length} ký tự còn lại</span>
              <div className="bio-btn-group">
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => {
                    setBioInput(profile.bio || '');
                    setIsEditingBio(false);
                  }}
                  disabled={isSubmitting}
                >
                  Hủy
                </button>
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={handleSaveBio}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Đang lưu...' : 'Lưu'}
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="bio-display-box">
            <p className="bio-text">{profile.bio || 'Chưa có tiểu sử.'}</p>
            {isOwnProfile && (
              <button
                type="button"
                className="btn btn-secondary btn-block btn-sm"
                onClick={() => setIsEditingBio(true)}
              >
                Chỉnh sửa tiểu sử
              </button>
            )}
          </div>
        )}
      </div>

      <div className="widget-divider" />

      {/* Structured Metadata Rows with Line SVG Stroke Navy Icons */}
      <ul className="intro-metadata-list">
        {profile.workplace && (
          <li className="metadata-item">
            <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="#1E3A8A" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" className="meta-svg-icon">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
            </svg>
            <div className="metadata-content">
              <span>Làm việc tại <strong>{profile.workplace}</strong></span>
            </div>
          </li>
        )}

        {profile.education && (
          <li className="metadata-item">
            <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="#1E3A8A" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" className="meta-svg-icon">
              <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
              <path d="M6 12v5c0 2 6 3 6 3s6-1 6-3v-5" />
            </svg>
            <div className="metadata-content">
              <span>Học tại <strong>{profile.education}</strong></span>
            </div>
          </li>
        )}

        {profile.faculty && (
          <li className="metadata-item">
            <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="#1E3A8A" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" className="meta-svg-icon">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
            <div className="metadata-content">
              <span>Khoa <strong>{profile.faculty}</strong></span>
            </div>
          </li>
        )}

        {profile.currentCity && (
          <li className="metadata-item">
            <IconHousing size={16} color="#1E3A8A" strokeWidth={1.8} className="meta-svg-icon" />
            <div className="metadata-content">
              <span>Sống tại <strong>{profile.currentCity}</strong></span>
            </div>
          </li>
        )}

        {profile.hometown && (
          <li className="metadata-item">
            <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="#1E3A8A" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" className="meta-svg-icon">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
              <circle cx="12" cy="10" r="3" />
            </svg>
            <div className="metadata-content">
              <span>Đến từ <strong>{profile.hometown}</strong></span>
            </div>
          </li>
        )}

        {profile.joinedDate && (
          <li className="metadata-item">
            <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="#1E3A8A" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" className="meta-svg-icon">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
              <line x1="16" y1="2" x2="16" y2="6" />
              <line x1="8" y1="2" x2="8" y2="6" />
              <line x1="3" y1="10" x2="21" y2="10" />
            </svg>
            <div className="metadata-content">
              <span>Đã tham gia vào <strong>{profile.joinedDate}</strong></span>
            </div>
          </li>
        )}
      </ul>

      {isOwnProfile && (
        <button
          type="button"
          className="btn btn-secondary btn-block btn-edit-details"
          onClick={onOpenEditModal}
        >
          Chỉnh sửa chi tiết
        </button>
      )}
    </div>
  );
}

