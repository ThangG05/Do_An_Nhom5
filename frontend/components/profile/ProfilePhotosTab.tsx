"use client";

import React, { useState } from 'react';
import { UserPhoto } from '@/types/user';

interface ProfilePhotosTabProps {
  photos: UserPhoto[];
  subTab: 'of_you' | 'your_photos' | 'albums';
  onSubTabChange: (subTab: 'of_you' | 'your_photos' | 'albums') => void;
}

export default function ProfilePhotosTab({
  photos,
  subTab,
  onSubTabChange,
}: ProfilePhotosTabProps) {
  const [selectedPhoto, setSelectedPhoto] = useState<UserPhoto | null>(null);

  // Group photos into Albums for the Albums subtab view
  const albumsMap = photos.reduce((acc, photo) => {
    const albumName = photo.albumName || 'Ảnh tải lên';
    if (!acc[albumName]) {
      acc[albumName] = { name: albumName, coverUrl: photo.url, count: 0 };
    }
    acc[albumName].count += 1;
    return acc;
  }, {} as Record<string, { name: string; coverUrl: string; count: number }>);

  const albumsList = Object.values(albumsMap);

  return (
    <div className="profile-photos-tab-container">
      {/* Header Bar */}
      <div className="photos-header-card">
        <div className="title-group">
          <h2 className="tab-main-title">Ảnh & Media</h2>
          <span className="photos-count-pill">{photos.length} hình ảnh</span>
        </div>

        <div className="subnav-filter-tabs">
          <button
            type="button"
            className={`subnav-tab ${subTab === 'your_photos' ? 'active' : ''}`}
            onClick={() => onSubTabChange('your_photos')}
          >
            Ảnh của bạn
          </button>
          <button
            type="button"
            className={`subnav-tab ${subTab === 'of_you' ? 'active' : ''}`}
            onClick={() => onSubTabChange('of_you')}
          >
            Ảnh có mặt bạn
          </button>
          <button
            type="button"
            className={`subnav-tab ${subTab === 'albums' ? 'active' : ''}`}
            onClick={() => onSubTabChange('albums')}
          >
            Album
          </button>
        </div>
      </div>

      {/* Content Area */}
      {subTab === 'albums' ? (
        <div className="albums-grid-container">
          {albumsList.length > 0 ? (
            albumsList.map((album, idx) => (
              <div key={idx} className="album-card">
                <div className="album-cover-thumb">
                  <img src={album.coverUrl} alt={album.name} />
                  <span className="album-count-badge">{album.count} mục</span>
                </div>
                <div className="album-meta">
                  <strong className="album-title">{album.name}</strong>
                </div>
              </div>
            ))
          ) : (
            <p className="empty-subtext">Chưa có album nào.</p>
          )}
        </div>
      ) : (
        <div className="photos-gallery-grid">
          {photos.length > 0 ? (
            photos.map((photo) => (
              <div
                key={photo.id}
                className="gallery-photo-item"
                onClick={() => setSelectedPhoto(photo)}
              >
                <img src={photo.url} alt={photo.caption || 'Ảnh người dùng'} />
                <div className="photo-hover-overlay">
                  {photo.likesCount && <span>❤️ {photo.likesCount}</span>}
                </div>
              </div>
            ))
          ) : (
            <div className="empty-photos-card">
              <div className="empty-icon">🖼</div>
              <h3 className="empty-title">Chưa có ảnh nào</h3>
            </div>
          )}
        </div>
      )}

      {/* Lightbox Modal */}
      {selectedPhoto && (
        <div className="lightbox-modal-backdrop" onClick={() => setSelectedPhoto(null)}>
          <div className="lightbox-content-box" onClick={(e) => e.stopPropagation()}>
            <button
              type="button"
              className="lightbox-close-btn"
              onClick={() => setSelectedPhoto(null)}
            >
              ✕
            </button>
            <div className="lightbox-image-wrapper">
              <img src={selectedPhoto.url} alt={selectedPhoto.caption || 'Ảnh xem phóng to'} />
            </div>
            {selectedPhoto.caption && (
              <div className="lightbox-caption-bar">
                <p>{selectedPhoto.caption}</p>
                {selectedPhoto.createdAt && <small>{selectedPhoto.createdAt}</small>}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
