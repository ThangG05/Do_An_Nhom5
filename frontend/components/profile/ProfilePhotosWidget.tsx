"use client";

import React from 'react';
import { UserPhoto, ProfileTabType } from '@/types/user';

interface ProfilePhotosWidgetProps {
  photos: UserPhoto[];
  onSeeAllPhotos: (tab: ProfileTabType) => void;
}

export default function ProfilePhotosWidget({
  photos,
  onSeeAllPhotos,
}: ProfilePhotosWidgetProps) {
  const recentPhotos = photos.slice(0, 9);

  return (
    <div className="profile-widget-card photos-widget">
      <div className="widget-header-row">
        <div className="widget-title-group">
          <h2 className="widget-title">Ảnh</h2>
          <span className="widget-count-tag">{photos.length} ảnh</span>
        </div>
        <button
          type="button"
          className="widget-see-all-link"
          onClick={() => onSeeAllPhotos('photos')}
        >
          Xem tất cả ảnh
        </button>
      </div>

      {recentPhotos.length > 0 ? (
        <div className="photos-grid-3x3">
          {recentPhotos.map((photo) => (
            <div key={photo.id} className="photo-grid-item">
              <img src={photo.url} alt={photo.caption || 'Ảnh người dùng'} />
            </div>
          ))}
        </div>
      ) : (
        <p className="widget-empty-text">Chưa có ảnh nào được tải lên.</p>
      )}
    </div>
  );
}
