"use client";

import { useEffect, useState } from 'react';
import { UserPhoto } from '@/types/user';
import { safeImageSrc } from '@/lib/media';
import RelativeTime from '@/components/ui/RelativeTime';

interface ProfilePhotosTabProps {
  photos: UserPhoto[];
  subTab: 'your_photos' | 'albums';
  onSubTabChange: (subTab: 'your_photos' | 'albums') => void;
}

export default function ProfilePhotosTab({ photos, subTab, onSubTabChange }: ProfilePhotosTabProps) {
  const [selectedAlbum, setSelectedAlbum] = useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const albums = Object.entries(photos.reduce<Record<string, UserPhoto[]>>((groups, photo) => {
    const name = photo.albumName || 'Ảnh tải lên';
    (groups[name] ??= []).push(photo);
    return groups;
  }, {}));
  const visiblePhotos = selectedAlbum ? photos.filter(photo => (photo.albumName || 'Ảnh tải lên') === selectedAlbum) : photos;
  const selectedPhoto = selectedIndex === null ? null : visiblePhotos[selectedIndex];

  useEffect(() => {
    if (selectedIndex === null) return;
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setSelectedIndex(null);
      if (event.key === 'ArrowLeft') setSelectedIndex(current => current === null ? null : (current - 1 + visiblePhotos.length) % visiblePhotos.length);
      if (event.key === 'ArrowRight') setSelectedIndex(current => current === null ? null : (current + 1) % visiblePhotos.length);
    };
    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', handleKey);
    return () => { document.body.style.overflow = ''; window.removeEventListener('keydown', handleKey); };
  }, [selectedIndex, visiblePhotos.length]);

  return <div className="profile-photos-tab-container">
    <div className="photos-header-card">
      <div className="title-group"><h2 className="tab-main-title">Ảnh</h2><span className="photos-count-pill">{photos.length} ảnh</span></div>
      <div className="subnav-filter-tabs">
        <button type="button" className={`subnav-tab ${subTab === 'your_photos' ? 'active' : ''}`} onClick={() => { setSelectedAlbum(null); setSelectedIndex(null); onSubTabChange('your_photos'); }}>Ảnh của bạn</button>
        <button type="button" className={`subnav-tab ${subTab === 'albums' ? 'active' : ''}`} onClick={() => { setSelectedAlbum(null); setSelectedIndex(null); onSubTabChange('albums'); }}>Album</button>
      </div>
    </div>

    {subTab === 'albums' && !selectedAlbum ? <div className="albums-grid-container">
      {albums.length ? albums.map(([name, items]) => <button type="button" key={name} className="album-card" onClick={() => setSelectedAlbum(name)} aria-label={`Mở album ${name}, ${items.length} ảnh`}>
        <div className="album-cover-thumb"><img src={safeImageSrc(items[0].url)} alt="" /><span className="album-count-badge">{items.length} ảnh</span></div>
        <div className="album-meta"><strong className="album-title">{name}</strong><span>Xem album →</span></div>
      </button>) : <p className="empty-subtext">Chưa có album nào.</p>}
    </div> : <>
      {selectedAlbum && <div className="album-detail-heading"><button type="button" onClick={() => { setSelectedAlbum(null); setSelectedIndex(null); }}>← Tất cả album</button><div><h3>{selectedAlbum}</h3><span>{visiblePhotos.length} ảnh</span></div></div>}
      {visiblePhotos.length ? <div className="photos-gallery-grid">{visiblePhotos.map((photo, index) => <button type="button" key={photo.id} className="gallery-photo-item" onClick={() => setSelectedIndex(index)} aria-label={`Xem ảnh ${index + 1} trong ${visiblePhotos.length}`}>
        <img src={safeImageSrc(photo.url)} alt={photo.caption || `Ảnh ${index + 1}`} />
      </button>)}</div> : <div className="empty-photos-card"><h3>Chưa có ảnh nào</h3></div>}
    </>}

    {selectedPhoto && <div className="lightbox-modal-backdrop" onClick={() => setSelectedIndex(null)} role="presentation">
      <div className="lightbox-content-box" role="dialog" aria-modal="true" aria-label="Xem ảnh" onClick={event => event.stopPropagation()}>
        <div className="photo-lightbox-toolbar"><span>{(selectedIndex ?? 0) + 1} / {visiblePhotos.length}</span><button type="button" className="lightbox-close-btn" onClick={() => setSelectedIndex(null)} aria-label="Đóng ảnh">✕</button></div>
        <div className="photo-lightbox-stage">
          {visiblePhotos.length > 1 && <button type="button" className="photo-lightbox-arrow" onClick={() => setSelectedIndex(current => current === null ? null : (current - 1 + visiblePhotos.length) % visiblePhotos.length)} aria-label="Ảnh trước">‹</button>}
          <div className="lightbox-image-wrapper"><img src={safeImageSrc(selectedPhoto.url)} alt={selectedPhoto.caption || 'Ảnh xem phóng to'} /></div>
          {visiblePhotos.length > 1 && <button type="button" className="photo-lightbox-arrow" onClick={() => setSelectedIndex(current => current === null ? null : (current + 1) % visiblePhotos.length)} aria-label="Ảnh tiếp theo">›</button>}
        </div>
        {(selectedPhoto.caption || selectedPhoto.createdAt) && <div className="lightbox-caption-bar"><p>{selectedPhoto.caption}</p>{selectedPhoto.createdAt && <RelativeTime value={selectedPhoto.createdAt} />}</div>}
      </div>
    </div>}
  </div>;
}
