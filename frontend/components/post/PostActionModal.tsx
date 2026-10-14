"use client";

import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { createReport, deletePost, editPost } from '@/lib/api';
import type { Post, PostPrivacy, PostMedia } from '@/types/post';
import { useCreatePost } from '@/hooks/useCreatePost';
import { validatePostDraft, type PostFieldErrors } from '@/lib/group-post';
import GroupPostFields from './GroupPostFields';
import LocationPicker from './LocationPicker';
import { safeImageSrc } from '@/lib/media';
import styles from './GroupPost.module.css';

type Mode = 'edit' | 'delete' | 'report';
export default function PostActionModal({ mode, post, content, privacy, onClose, onUpdated, onDeleted, onMessage }: { mode: Mode | null; post: Post; content: string; privacy: PostPrivacy; onClose: () => void; onUpdated: (post: Post) => void; onDeleted: () => void; onMessage: (message: string) => void }) {
  const fields = useCreatePost();
  const [media, setMedia] = useState<PostMedia[]>(post.media || []);
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [errors, setErrors] = useState<PostFieldErrors>({});
  const [locationOpen, setLocationOpen] = useState(false);
  useEffect(() => {
    if (!mode) return;
    fields.setContent(content); fields.setPrivacy(privacy); fields.setCategory(post.category);
    fields.setMarketListing(post.marketListing || { productName: '', price: '', condition: '', location: '' });
    fields.setRoomListing(post.roomListing || { rentPerMonth: '', area: '', amenities: [], location: '' });
    fields.setEventListing(post.eventListing || { eventName: '', eventDate: '', eventTime: '', location: '', organizer: '' });
    fields.setStudyListing(post.studyListing || { subjectName: '' }); fields.setLocation(post.location || null);
    setMedia(post.media || []); setReason(''); setError(''); setErrors({});
    // Initialize once per opened action, not while the draft is being edited.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, post.id]);
  if (!mode) return null;
  const move = (index: number, direction: number) => setMedia(current => {
    const target = index + direction; if (target < 0 || target >= current.length) return current;
    const copy = [...current]; [copy[index], copy[target]] = [copy[target], copy[index]]; return copy;
  });
  const submit = async () => {
    if (busy) return;
    if (mode === 'edit') {
      const next = validatePostDraft(fields, media.length); setErrors(next);
      if (Object.keys(next).length) { window.setTimeout(() => document.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus(), 0); return; }
    }
    setBusy(true); setError('');
    try {
      if (mode === 'edit') {
        const updated = await editPost(post.id, fields.content.trim(), post.groupId ? 'public' : fields.privacy, post.category, media.map(item => item.id), {
          marketListing: post.category === 'market' ? fields.marketListing : undefined,
          roomListing: post.category === 'roommate' ? fields.roomListing : undefined,
          eventListing: post.category === 'event' ? fields.eventListing : undefined,
          studyListing: post.category === 'study' ? fields.studyListing : undefined,
          location: fields.location || undefined,
        });
        onUpdated(updated);
        onMessage(updated.status === 'PENDING' ? 'Đã cập nhật và gửi bài chờ duyệt lại.' : 'Đã cập nhật bài viết.');
      } else if (mode === 'delete') { await deletePost(post.id); onDeleted(); }
      else { if (reason.trim().length < 3) throw new Error('Vui lòng nhập lý do rõ ràng.'); await createReport('POST', post.id, reason.trim()); onMessage('Đã gửi báo cáo tới quản trị viên.'); }
      onClose();
    } catch (e) { setError(e instanceof Error ? e.message : 'Không thể thực hiện thao tác.'); }
    finally { setBusy(false); }
  };
  return createPortal(<div className="post-action-overlay" role="dialog" aria-modal="true" aria-labelledby="post-action-title" onClick={() => { if (!busy) onClose(); }}><section className="post-action-modal" onClick={e => e.stopPropagation()}>
    <header><div><small>QUẢN LÝ BÀI VIẾT</small><h2 id="post-action-title">{mode === 'edit' ? 'Chỉnh sửa bài viết' : mode === 'delete' ? 'Xóa bài viết' : 'Báo cáo bài viết'}</h2></div><button onClick={onClose} disabled={busy} aria-label="Đóng">×</button></header>
    <div className="post-action-content">
      {mode === 'edit' && <fieldset disabled={busy} style={{ border: 0, padding: 0, margin: 0, minWidth: 0 }}>
        {post.groupId ? <p className={styles.hint}>Bài trong {post.groupName} sẽ được duyệt lại sau khi chỉnh sửa. Không thể chuyển nhóm của bài đã đăng.</p> : <label>Quyền riêng tư<select value={fields.privacy} onChange={e => fields.setPrivacy(e.target.value as PostPrivacy)}><option value="public">Công khai</option><option value="friends">Bạn bè</option><option value="private">Chỉ mình tôi</option></select></label>}
        <GroupPostFields state={fields} errors={errors} onPickLocation={() => setLocationOpen(true)} />
        {media.length > 0 && <div className="edit-media-list"><b>Tệp trong bài</b>{media.map((item, index) => <article key={item.id}>{item.type === 'image' ? <img src={safeImageSrc(item.url)} alt="" /> : <span>{item.name || (item.type === 'video' ? 'Video' : item.type === 'audio' ? 'Âm thanh' : 'Tài liệu')}</span>}<div><button aria-label="Chuyển tệp lên trước" onClick={() => move(index, -1)} disabled={index === 0}>←</button><button aria-label="Chuyển tệp về sau" onClick={() => move(index, 1)} disabled={index === media.length - 1}>→</button><button className="danger" onClick={() => setMedia(current => current.filter(x => x.id !== item.id))}>Gỡ</button></div></article>)}</div>}
      </fieldset>}
      {mode === 'delete' && <div className="post-delete-warning"><strong>Bài viết sẽ bị xóa khỏi bảng tin.</strong><p>Thao tác này không thể hoàn tác.</p></div>}
      {mode === 'report' && <label>Lý do báo cáo<textarea value={reason} onChange={e => setReason(e.target.value)} rows={5} placeholder="Mô tả nội dung vi phạm…" /></label>}
      {error && <div className="post-error-banner" role="alert">{error}</div>}
    </div>
    <footer><button className="btn btn-secondary" onClick={onClose} disabled={busy}>Hủy</button><button className={mode === 'delete' ? 'btn btn-danger' : 'btn btn-primary'} disabled={busy || (mode === 'report' && reason.trim().length < 3)} onClick={() => void submit()}>{busy ? 'Đang xử lý…' : mode === 'edit' ? 'Lưu thay đổi' : mode === 'delete' ? 'Xóa bài viết' : 'Gửi báo cáo'}</button></footer>
    <LocationPicker open={locationOpen} onClose={() => setLocationOpen(false)} onSelect={place => { fields.setLocation(place); if (post.category === 'market') fields.setMarketListing(p => ({ ...p, location: place.name })); if (post.category === 'event') fields.setEventListing(p => ({ ...p, location: place.name })); if (post.category === 'roommate') fields.setRoomListing(p => ({ ...p, location: place.name })); setLocationOpen(false); }} />
  </section></div>, document.body);
}
