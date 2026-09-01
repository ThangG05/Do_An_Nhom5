"use client";

import React, { useState, useRef } from 'react';
import { UserProfile } from '@/types/user';

interface EditProfileModalProps {
  profile: UserProfile;
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: Partial<UserProfile>) => Promise<void>;
}

export default function EditProfileModal({
  profile,
  isOpen,
  onClose,
  onSave,
}: EditProfileModalProps) {
  const [avatar, setAvatar] = useState(profile.avatar || '');
  const [coverBanner, setCoverBanner] = useState(profile.coverBanner || '');
  const [name, setName] = useState(profile.name || '');
  const [bio, setBio] = useState(profile.bio || '');
  const [pronouns, setPronouns] = useState(profile.pronouns || '');
  const [workplace, setWorkplace] = useState(profile.workplace || '');
  const [education, setEducation] = useState(profile.education || '');
  const [faculty, setFaculty] = useState(profile.faculty || '');
  const [courseYear, setCourseYear] = useState(profile.courseYear || '');
  const [currentCity, setCurrentCity] = useState(profile.currentCity || '');
  const [hometown, setHometown] = useState(profile.hometown || '');
  const [facebook, setFacebook] = useState(profile.socialLinks?.facebook || '');
  const [instagram, setInstagram] = useState(profile.socialLinks?.instagram || '');
  const [linkedin, setLinkedin] = useState(profile.socialLinks?.linkedin || '');

  const [avatarError, setAvatarError] = useState('');
  const [coverError, setCoverError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const avatarInputRef = useRef<HTMLInputElement | null>(null);
  const coverInputRef = useRef<HTMLInputElement | null>(null);

  if (!isOpen) return null;

  const handleAvatarFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAvatarError('');
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setAvatarError('Vui lòng chọn tệp định dạng ảnh (JPEG, PNG, WEBP).');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setAvatarError('Kích thước ảnh tối đa 5MB.');
      return;
    }

    const localPreviewUrl = URL.createObjectURL(file);
    setAvatar(localPreviewUrl);
  };

  const handleCoverFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCoverError('');
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setCoverError('Vui lòng chọn tệp định dạng ảnh (JPEG, PNG, WEBP).');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setCoverError('Kích thước ảnh tối đa 5MB.');
      return;
    }

    const localPreviewUrl = URL.createObjectURL(file);
    setCoverBanner(localPreviewUrl);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    await onSave({
      avatar,
      coverBanner,
      name,
      bio,
      pronouns,
      workplace,
      education,
      faculty,
      courseYear,
      currentCity,
      hometown,
      socialLinks: {
        facebook,
        instagram,
        linkedin,
      },
    });
    setIsSaving(false);
  };

  return (
    <div className="edit-profile-modal-backdrop" onClick={onClose}>
      <div
        className="edit-profile-modal-card"
        onClick={(e) => e.stopPropagation()}
        aria-modal="true"
        role="dialog"
      >
        <div className="modal-header">
          <h2 className="modal-title">Chỉnh sửa trang cá nhân</h2>
          <button type="button" className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form-body">
          {/* 1. Profile Picture (Native File Picker) */}
          <section className="form-section">
            <div className="section-header-row">
              <h3>Ảnh đại diện</h3>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => avatarInputRef.current?.click()}
              >
                Tải ảnh từ máy tính
              </button>
              <input
                ref={avatarInputRef}
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={handleAvatarFileSelect}
              />
            </div>
            {avatarError && <p className="file-error-msg">{avatarError}</p>}
            <div className="avatar-preview-wrapper">
              <img src={avatar} alt="Avatar preview" />
            </div>
          </section>

          {/* 3. Basic Info */}
          <section className="form-section">
            <h3>Thông tin cơ bản</h3>
            <div className="form-grid-2col">
              <div className="form-group">
                <label>Họ và tên</label>
                <input
                  type="text"
                  className="form-control"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>Danh xưng / Pronouns</label>
                <input
                  type="text"
                  className="form-control"
                  value={pronouns}
                  onChange={(e) => setPronouns(e.target.value)}
                  placeholder="she/her, he/him..."
                />
              </div>
            </div>

            <div className="form-group mt-3">
              <label>Tiểu sử (Bio)</label>
              <textarea
                className="form-control"
                rows={3}
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                maxLength={150}
              />
            </div>
          </section>

          {/* 4. Education & Work */}
          <section className="form-section">
            <h3>Học vấn & Nơi làm việc</h3>
            <div className="form-grid-2col">
              <div className="form-group">
                <label>Khoa / Chuyên ngành</label>
                <input
                  type="text"
                  className="form-control"
                  value={faculty}
                  onChange={(e) => setFaculty(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Khóa học</label>
                <input
                  type="text"
                  className="form-control"
                  value={courseYear}
                  onChange={(e) => setCourseYear(e.target.value)}
                  placeholder="K25 (2023-2027)"
                />
              </div>
            </div>

            <div className="form-grid-2col mt-3">
              <div className="form-group">
                <label>Trường đại học</label>
                <input
                  type="text"
                  className="form-control"
                  value={education}
                  onChange={(e) => setEducation(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Nơi làm việc / CLB</label>
                <input
                  type="text"
                  className="form-control"
                  value={workplace}
                  onChange={(e) => setWorkplace(e.target.value)}
                />
              </div>
            </div>
          </section>

          {/* 5. Location */}
          <section className="form-section">
            <h3>Tỉnh/Thành phố</h3>
            <div className="form-grid-2col">
              <div className="form-group">
                <label>Tỉnh/Thành phố hiện tại</label>
                <input
                  type="text"
                  className="form-control"
                  value={currentCity}
                  onChange={(e) => setCurrentCity(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Quê quán</label>
                <input
                  type="text"
                  className="form-control"
                  value={hometown}
                  onChange={(e) => setHometown(e.target.value)}
                />
              </div>
            </div>
          </section>

          {/* 6. Social Links */}
          <section className="form-section">
            <h3>Liên kết mạng xã hội</h3>
            <div className="form-group">
              <label>Facebook URL</label>
              <input
                type="text"
                className="form-control"
                value={facebook}
                onChange={(e) => setFacebook(e.target.value)}
              />
            </div>
            <div className="form-group mt-2">
              <label>Instagram URL</label>
              <input
                type="text"
                className="form-control"
                value={instagram}
                onChange={(e) => setInstagram(e.target.value)}
              />
            </div>
            <div className="form-group mt-2">
              <label>LinkedIn URL</label>
              <input
                type="text"
                className="form-control"
                value={linkedin}
                onChange={(e) => setLinkedin(e.target.value)}
              />
            </div>
          </section>

          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={isSaving}
            >
              Hủy
            </button>
            <button type="submit" className="btn btn-primary" disabled={isSaving}>
              {isSaving ? 'Đang lưu...' : 'Lưu thay đổi'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

