"use client";

import React, { useEffect, useState, useRef } from 'react';
import { UserProfile } from '@/types/user';
import { safeImageSrc } from '@/lib/media';
import {
  deriveCourseYear,
  HVNH_FACULTIES,
  HVNH_SCHOOL_NAME,
  normalizeSocialUrl,
  VIETNAM_PROVINCES,
} from '@/lib/profile-options';

interface EditProfileModalProps {
  profile: UserProfile;
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: Partial<UserProfile>) => Promise<void>;
  onUploadAvatar?: (file: File, caption: string, visibility: 'PUBLIC' | 'FRIENDS' | 'PRIVATE') => Promise<void>;
  onUploadCover?: (file: File) => Promise<void>;
}

export default function EditProfileModal({
  profile,
  isOpen,
  onClose,
  onSave,
  onUploadAvatar,
  onUploadCover,
}: EditProfileModalProps) {
  const [avatar, setAvatar] = useState(profile.avatar || '');
  const [coverBanner, setCoverBanner] = useState(profile.coverBanner || '');
  const [name, setName] = useState(profile.name || '');
  const [bio, setBio] = useState(profile.bio || '');
  const [pronouns, setPronouns] = useState(profile.pronouns || '');
  const [workplace, setWorkplace] = useState(profile.workplace || '');
  const [education] = useState(HVNH_SCHOOL_NAME);
  const [faculty, setFaculty] = useState(profile.faculty || '');
  const [courseYear, setCourseYear] = useState(deriveCourseYear(profile.studentCode) || profile.courseYear || '');
  const [currentCity, setCurrentCity] = useState(profile.currentCity || '');
  const [hometown, setHometown] = useState(profile.hometown || '');
  const [facebook, setFacebook] = useState(profile.socialLinks?.facebook || '');
  const [instagram, setInstagram] = useState(profile.socialLinks?.instagram || '');
  const [linkedin, setLinkedin] = useState(profile.socialLinks?.linkedin || '');

  const [avatarError, setAvatarError] = useState('');
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarCaption, setAvatarCaption] = useState('');
  const [avatarVisibility, setAvatarVisibility] = useState<'PUBLIC' | 'FRIENDS' | 'PRIVATE'>('PUBLIC');
  const [coverError, setCoverError] = useState('');
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState('');

  const avatarInputRef = useRef<HTMLInputElement | null>(null);
  const coverInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    setAvatar(profile.avatar || '');
    setCoverBanner(profile.coverBanner || '');
    setName(profile.name || '');
    setBio(profile.bio || '');
    setPronouns(profile.pronouns || '');
    setWorkplace(profile.workplace || '');
    const fixedCourseYear = deriveCourseYear(profile.studentCode) || profile.courseYear || '';
    setFaculty(profile.faculty || '');
    setCourseYear(fixedCourseYear);
    setCurrentCity(profile.currentCity || '');
    setHometown(profile.hometown || '');
    setFacebook(profile.socialLinks?.facebook || '');
    setInstagram(profile.socialLinks?.instagram || '');
    setLinkedin(profile.socialLinks?.linkedin || '');
    setAvatarFile(null);
    setCoverFile(null);
    setAvatarCaption('');
    setAvatarError('');
    setCoverError('');
    setSaveError('');
  }, [isOpen, profile]);

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
    setAvatarFile(file);
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
    setCoverFile(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSaveError('');
    try {
      if (avatarFile && onUploadAvatar) {
        await onUploadAvatar(avatarFile, avatarCaption, avatarVisibility);
      }
      if (coverFile && onUploadCover) {
        await onUploadCover(coverFile);
      }
      await onSave({
      name: name.trim(),
      bio,
      pronouns,
      workplace,
      education,
      faculty,
      courseYear: deriveCourseYear(profile.studentCode) || courseYear,
      currentCity,
      hometown,
      socialLinks: {
        facebook: normalizeSocialUrl(facebook),
        instagram: normalizeSocialUrl(instagram),
        linkedin: normalizeSocialUrl(linkedin),
      },
      });
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Không thể lưu thay đổi. Vui lòng thử lại.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="edit-profile-modal-backdrop" onClick={() => { if (!isSaving) onClose(); }}>
      <div
        className="edit-profile-modal-card"
        onClick={(e) => e.stopPropagation()}
        aria-modal="true"
        role="dialog"
      >
        <div className="modal-header">
          <h2 className="modal-title">Chỉnh sửa trang cá nhân</h2>
          <button type="button" className="close-btn" onClick={onClose} disabled={isSaving}>
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
              <img src={safeImageSrc(avatar)} alt="Avatar preview" />
            </div>
            {avatarFile && (
              <div className="form-group mt-3">
                <label>Chú thích bài viết ảnh đại diện</label>
                <textarea className="form-control" rows={3} maxLength={5000} value={avatarCaption} onChange={(event) => setAvatarCaption(event.target.value)} placeholder="Bạn đang nghĩ gì?" />
                <label className="mt-2">Ai có thể xem bài viết này?</label>
                <select className="form-control" value={avatarVisibility} onChange={(event) => setAvatarVisibility(event.target.value as 'PUBLIC' | 'FRIENDS' | 'PRIVATE')}>
                  <option value="PUBLIC">Công khai</option>
                  <option value="FRIENDS">Bạn bè</option>
                  <option value="PRIVATE">Chỉ mình tôi</option>
                </select>
              </div>
            )}
          </section>

          <section className="form-section">
            <div className="section-header-row">
              <h3>Ảnh bìa</h3>
              <button type="button" className="btn btn-secondary" onClick={() => coverInputRef.current?.click()}>
                Tải ảnh bìa từ máy tính
              </button>
              <input ref={coverInputRef} type="file" accept="image/jpeg,image/png,image/webp" style={{ display: 'none' }} onChange={handleCoverFileSelect} />
            </div>
            {coverError && <p className="file-error-msg">{coverError}</p>}
            <div className="cover-preview-wrapper">
              <img src={safeImageSrc(coverBanner)} alt="Xem trước ảnh bìa" />
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
                  minLength={2}
                  maxLength={150}
                  required
                  aria-describedby="identity-name-help"
                />
                <small id="identity-name-help">Bạn có thể đổi tên hiển thị. Mã sinh viên luôn cố định theo email HVNH và không thể chỉnh sửa.</small>
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
                <select
                  className="form-control"
                  value={faculty}
                  onChange={(e) => setFaculty(e.target.value)}
                >
                  <option value="">Chọn khoa/chuyên ngành</option>
                  {HVNH_FACULTIES.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </div>

              <div className="form-group">
                <label>Khóa học</label>
                <input
                  type="text"
                  className="form-control"
                  value={courseYear}
                  readOnly
                  aria-readonly="true"
                  placeholder="Tự động xác định từ mã sinh viên"
                />
                <small>Khóa học được xác định tự động từ mã sinh viên {profile.studentCode || ''}.</small>
              </div>
            </div>

            <div className="form-grid-2col mt-3">
              <div className="form-group">
                <label>Trường đại học</label>
                <input
                  type="text"
                  className="form-control"
                  value={education}
                  readOnly
                  aria-readonly="true"
                />
                <small>Thông tin trường được cố định cho tài khoản HVNH.</small>
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
                <select
                  className="form-control"
                  value={currentCity}
                  onChange={(e) => setCurrentCity(e.target.value)}
                >
                  <option value="">Chọn tỉnh/thành phố</option>
                  {VIETNAM_PROVINCES.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </div>

              <div className="form-group">
                <label>Quê quán</label>
                <select
                  className="form-control"
                  value={hometown}
                  onChange={(e) => setHometown(e.target.value)}
                >
                  <option value="">Chọn tỉnh/thành phố</option>
                  {VIETNAM_PROVINCES.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </div>
            </div>
          </section>

          {/* 6. Social Links */}
          <section className="form-section">
            <h3>Liên kết mạng xã hội</h3>
            <div className="form-group">
              <label>Facebook URL</label>
              <input
                type="url"
                className="form-control"
                value={facebook}
                onChange={(e) => setFacebook(e.target.value)}
                placeholder="https://facebook.com/ten-cua-ban"
              />
            </div>
            <div className="form-group mt-2">
              <label>Instagram URL</label>
              <input
                type="url"
                className="form-control"
                value={instagram}
                onChange={(e) => setInstagram(e.target.value)}
                placeholder="https://instagram.com/ten-cua-ban"
              />
            </div>
            <div className="form-group mt-2">
              <label>LinkedIn URL</label>
              <input
                type="url"
                className="form-control"
                value={linkedin}
                onChange={(e) => setLinkedin(e.target.value)}
                placeholder="https://linkedin.com/in/ten-cua-ban"
              />
            </div>
          </section>

          {saveError && <p className="profile-save-error" role="alert">{saveError}</p>}
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

