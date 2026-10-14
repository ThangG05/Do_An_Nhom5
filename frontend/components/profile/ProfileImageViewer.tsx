"use client";

import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { safeImageSrc } from '@/lib/media';

interface ProfileImageViewerProps {
  src: string;
  name: string;
  kind: 'avatar' | 'cover';
  onClose: () => void;
  onEdit?: () => void;
}

export default function ProfileImageViewer({ src, name, kind, onClose, onEdit }: ProfileImageViewerProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [failed, setFailed] = useState(false);
  const title = kind === 'cover' ? 'Ảnh bìa' : 'Ảnh đại diện';

  useEffect(() => {
    const dialog = dialogRef.current;
    const previousFocus = document.activeElement as HTMLElement | null;
    const previousOverflow = document.body.style.overflow;
    dialog?.showModal();
    document.body.style.overflow = 'hidden';
    return () => {
      dialog?.close();
      document.body.style.overflow = previousOverflow;
      previousFocus?.focus({ preventScroll: true });
    };
  }, []);

  return createPortal(
    <dialog
      ref={dialogRef}
      className="profile-photo-dialog"
      aria-label={`${title} của ${name}`}
      onCancel={(event) => { event.preventDefault(); onClose(); }}
      onClick={(event) => { if (event.target === event.currentTarget) onClose(); }}
    >
      <section className="profile-photo-panel">
        <header className="profile-photo-toolbar">
          <div><h2>{title}</h2><p>{name}</p></div>
          <button type="button" className="profile-photo-close" aria-label="Đóng ảnh" onClick={onClose} autoFocus>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" /></svg>
          </button>
        </header>
        <div className="profile-photo-stage">
          {failed ? <p role="status">Không tải được ảnh. Bạn hãy đóng và mở lại để thử lại.</p> :
            <img src={safeImageSrc(src)} alt={`${title} của ${name}`} onError={() => setFailed(true)} />}
        </div>
        {onEdit && <footer className="profile-photo-footer">
          <button type="button" className="btn btn-primary" onClick={onEdit}>Đổi {title.toLowerCase()}</button>
        </footer>}
      </section>
    </dialog>,
    document.body,
  );
}
