"use client";

import React, { useState } from 'react';
import { UserProfile } from '@/types/user';

interface ProfileAboutTabProps {
  profile: UserProfile;
  isOwnProfile: boolean;
  onOpenEditModal: () => void;
}

type AboutSection = 'overview' | 'work_edu' | 'places' | 'contact' | 'details';

export default function ProfileAboutTab({
  profile,
  isOwnProfile,
  onOpenEditModal,
}: ProfileAboutTabProps) {
  const [activeSection, setActiveSection] = useState<AboutSection>('overview');

  const sections: { id: AboutSection; label: string; icon: string }[] = [
    { id: 'overview', label: 'Tổng quan', icon: '📋' },
    { id: 'work_edu', label: 'Công việc và Học vấn', icon: '💼' },
    { id: 'places', label: 'Nơi từng sống', icon: '📍' },
    { id: 'contact', label: 'Thông tin liên hệ và cơ bản', icon: '📞' },
    { id: 'details', label: 'Chi tiết về bạn', icon: '👤' },
  ];

  return (
    <div className="profile-about-tab-container">
      {/* Sidebar navigation inside About tab */}
      <aside className="about-subnav-sidebar">
        <h2 className="about-nav-title">Giới thiệu</h2>
        <nav className="about-subnav-menu">
          {sections.map((sec) => (
            <button
              key={sec.id}
              type="button"
              className={`subnav-item ${activeSection === sec.id ? 'active' : ''}`}
              onClick={() => setActiveSection(sec.id)}
            >
              <span className="item-icon">{sec.icon}</span>
              <span>{sec.label}</span>
            </button>
          ))}
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="about-content-area">
        {activeSection === 'overview' && (
          <section className="about-card-section">
            <h3 className="section-heading">Tổng quan</h3>

            <ul className="about-info-rows">
              {profile.workplace && (
                <li className="info-row">
                  <span className="row-icon">💼</span>
                  <div className="row-text">
                    <span>Làm việc tại <strong>{profile.workplace}</strong></span>
                  </div>
                </li>
              )}

              {profile.education && (
                <li className="info-row">
                  <span className="row-icon">🎓</span>
                  <div className="row-text">
                    <span>Học tại <strong>{profile.education}</strong> ({profile.courseYear})</span>
                  </div>
                </li>
              )}

              {profile.currentCity && (
                <li className="info-row">
                  <span className="row-icon">🏠</span>
                  <div className="row-text">
                    <span>Sống tại <strong>{profile.currentCity}</strong></span>
                  </div>
                </li>
              )}

              {profile.hometown && (
                <li className="info-row">
                  <span className="row-icon">📍</span>
                  <div className="row-text">
                    <span>Đến từ <strong>{profile.hometown}</strong></span>
                  </div>
                </li>
              )}

              {profile.email && (
                <li className="info-row">
                  <span className="row-icon">✉️</span>
                  <div className="row-text">
                    <span>Email học viện: <strong>{profile.email}</strong></span>
                  </div>
                </li>
              )}
            </ul>

            {isOwnProfile && (
              <button
                type="button"
                className="btn btn-secondary btn-sm mt-3"
                onClick={onOpenEditModal}
              >
                Chỉnh sửa thông tin tổng quan
              </button>
            )}
          </section>
        )}

        {activeSection === 'work_edu' && (
          <section className="about-card-section">
            <h3 className="section-heading">Công việc và Học vấn</h3>

            <div className="about-group-block">
              <h4 className="group-title">Công việc</h4>
              {profile.workplace ? (
                <div className="info-detail-box">
                  <span className="detail-icon">💼</span>
                  <div>
                    <strong>{profile.workplace}</strong>
                    <p className="sub-detail">{profile.role || 'Thành viên'} • Hiện tại</p>
                  </div>
                </div>
              ) : (
                <p className="empty-subtext">Chưa thêm nơi làm việc.</p>
              )}
            </div>

            <div className="about-group-block mt-4">
              <h4 className="group-title">Trường đại học / Học viện</h4>
              <div className="info-detail-box">
                <span className="detail-icon">🎓</span>
                <div>
                  <strong>{profile.education || 'Học viện Ngân hàng'}</strong>
                  <p className="sub-detail">
                    {profile.faculty} • khóa {profile.courseYear} • MSSV: {profile.studentCode || 'Đã xác thực'}
                  </p>
                </div>
              </div>
            </div>
          </section>
        )}

        {activeSection === 'places' && (
          <section className="about-card-section">
            <h3 className="section-heading">Nơi từng sống</h3>
            <ul className="about-info-rows">
              <li className="info-row">
                <span className="row-icon">🏠</span>
                <div className="row-text">
                  <strong>{profile.currentCity || 'Hà Nội'}</strong>
                  <p className="sub-detail">Thành phố hiện tại</p>
                </div>
              </li>
              <li className="info-row">
                <span className="row-icon">📍</span>
                <div className="row-text">
                  <strong>{profile.hometown || 'Chưa cập nhật'}</strong>
                  <p className="sub-detail">Quê quán</p>
                </div>
              </li>
            </ul>
          </section>
        )}

        {activeSection === 'contact' && (
          <section className="about-card-section">
            <h3 className="section-heading">Thông tin liên hệ và cơ bản</h3>

            <div className="about-group-block">
              <h4 className="group-title">Thông tin liên hệ</h4>
              <ul className="about-info-rows">
                <li className="info-row">
                  <span className="row-icon">✉️</span>
                  <div className="row-text">
                    <strong>{profile.email}</strong>
                    <p className="sub-detail">Email HVNH</p>
                  </div>
                </li>
                {profile.phone && (
                  <li className="info-row">
                    <span className="row-icon">📞</span>
                    <div className="row-text">
                      <strong>{profile.phone}</strong>
                      <p className="sub-detail">Số điện thoại</p>
                    </div>
                  </li>
                )}
              </ul>
            </div>

            <div className="about-group-block mt-4">
              <h4 className="group-title">Thông tin cơ bản</h4>
              <ul className="about-info-rows">
                {profile.gender && (
                  <li className="info-row">
                    <span className="row-icon">🚻</span>
                    <div className="row-text">
                      <strong>{profile.gender}</strong>
                      <p className="sub-detail">Giới tính</p>
                    </div>
                  </li>
                )}
                {profile.birthDate && (
                  <li className="info-row">
                    <span className="row-icon">🎂</span>
                    <div className="row-text">
                      <strong>{profile.birthDate}</strong>
                      <p className="sub-detail">Ngày sinh</p>
                    </div>
                  </li>
                )}
              </ul>
            </div>
          </section>
        )}

        {activeSection === 'details' && (
          <section className="about-card-section">
            <h3 className="section-heading">Chi tiết về bạn</h3>
            <div className="bio-full-box">
              <h4 className="group-title">Tiểu sử</h4>
              <p className="bio-full-text">{profile.bio || 'Chưa có tiểu sử.'}</p>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
