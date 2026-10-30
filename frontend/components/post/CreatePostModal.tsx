"use client";

import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import Link from 'next/link';
import type { UseCreatePostReturn } from '@/hooks/useCreatePost';
import { getAuthUser } from '@/lib/auth';
import { useAuthUser } from '@/components/auth/AuthProvider';
import { fetchGroups } from '@/lib/api';
import { GROUP_POST_KINDS, validatePostDraft, type PostFieldErrors } from '@/lib/group-post';
import type { ApiGroup } from '@/types/group-api';
import UserAvatar from '@/components/ui/UserAvatar';
import LocationPicker from './LocationPicker';
import GroupPostFields from './GroupPostFields';
import PostCategoryDetails, { CategoryIcon } from './PostCategoryDetails';
import { useDialog } from '@/components/ui/DialogProvider';
import styles from './GroupPost.module.css';
import { IconClose } from '@/components/ui/Icons';

export default function CreatePostModal({ postState: s, group }: { postState: UseCreatePostReturn; group?: ApiGroup }) {
  const currentUser = useAuthUser();
  const dialog = useDialog();
  const [author, setAuthor] = useState(currentUser);
  const [groups, setGroups] = useState<ApiGroup[]>([]);
  const [groupsLoading, setGroupsLoading] = useState(false);
  const [groupsError, setGroupsError] = useState(false);
  const [errors, setErrors] = useState<PostFieldErrors>({});
  const [locationOpen, setLocationOpen] = useState(false);
  const [preview, setPreview] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const shell = useRef<HTMLElement>(null);
  const form = useRef<HTMLFormElement>(null);

  useEffect(() => {
    if (!s.isOpen) return;
    setAuthor(currentUser || getAuthUser());
    setErrors({}); setPreview(false);
    const lastFocus = document.activeElement as HTMLElement;
    const before = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const timer = window.setTimeout(() => shell.current?.focus(), 0);
    return () => { window.clearTimeout(timer); document.body.style.overflow = before; lastFocus?.focus(); };
  }, [s.isOpen, currentUser]);

  useEffect(() => {
    if (!s.isOpen || group) return;
    let active = true;
    setGroupsLoading(true); setGroupsError(false);
    void fetchGroups().then(rows => { if (active) setGroups(rows); }).catch(() => { if (active) setGroupsError(true); }).finally(() => { if (active) setGroupsLoading(false); });
    return () => { active = false; };
  }, [s.isOpen, group]);

  if (!s.isOpen) return null;
  const kind = GROUP_POST_KINDS.find(item => item.category === s.category);
  const availableKinds = GROUP_POST_KINDS.filter(item => {
    const joined = groups.find(candidate => candidate.slug === item.slug);
    return joined?.membership === 'MEMBER' || joined?.membership === 'ADMIN' || joined?.membership === 'PUBLIC';
  });
  const selectedGroup = group || groups.find(item => item.slug === kind?.slug);
  const isGroup = s.category !== 'general';
  const unavailable = isGroup && !group && (groupsLoading || groupsError || !selectedGroup);
  const needsMembership = isGroup && !!selectedGroup && !['MEMBER', 'ADMIN', 'PUBLIC'].includes(selectedGroup.membership);
  const validate = () => {
    const next = validatePostDraft(s, s.mediaList.length);
    setErrors(next);
    if (Object.keys(next).length) {
      setPreview(false);
      window.setTimeout(() => {
        const invalid = form.current?.querySelector<HTMLElement>('[aria-invalid="true"]');
        invalid?.scrollIntoView({ block: 'center', behavior: 'smooth' }); invalid?.focus();
      }, 0);
      return false;
    }
    return true;
  };
  const publish = async () => {
    if (!validate() || unavailable || needsMembership || s.isSubmitting) return;
    const created = await s.submitPost();
    if (created?.status === 'PENDING') dialog.notify({ title: 'Đã gửi bài chờ duyệt', message: 'Bài viết trong ' + (created.groupName || kind?.label) + ' sẽ xuất hiện sau khi quản trị viên phê duyệt.', tone: 'success' });
  };
  const draft = { category: s.category, marketListing: s.category === 'market' ? s.marketListing : undefined, roomListing: s.category === 'roommate' ? s.roomListing : undefined, eventListing: s.category === 'event' ? s.eventListing : undefined, studyListing: s.category === 'study' ? s.studyListing : undefined, media: s.mediaList };

  return createPortal(<div className={styles.overlay} onMouseDown={e => { if (e.target === e.currentTarget && !locationOpen) s.closeModal(); }}>
    <section ref={shell} tabIndex={-1} className={styles.shell} data-category={s.category} role="dialog" aria-modal="true" aria-labelledby="gp-dialog-title" onKeyDown={e => {
      if (e.key === 'Escape') { e.stopPropagation(); if (locationOpen) setLocationOpen(false); else s.closeModal(); }
      if (e.key === 'Tab') {
        const nodes = Array.from(shell.current?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), textarea:not(:disabled), select:not(:disabled), a[href]') || []).filter(el => el.getClientRects().length);
        const first = nodes[0], last = nodes[nodes.length - 1];
        if (e.shiftKey && (document.activeElement === first || document.activeElement === shell.current)) { e.preventDefault(); last?.focus(); }
        else if (!e.shiftKey && (document.activeElement === last || document.activeElement === shell.current)) { e.preventDefault(); first?.focus(); }
      }
    }}>
      <header className={styles.header}><div className={styles.headerTitle}><span className={styles.iconTile}>{kind ? <CategoryIcon category={s.category} size={25} /> : '＋'}</span><div><small>CHIA SẺ CÙNG CỘNG ĐỒNG</small><h2 id="gp-dialog-title">{kind ? 'Tạo bài · ' + kind.label : 'Tạo bài viết'}</h2></div></div><button type="button" className={styles.close} disabled={s.isSubmitting} onClick={s.closeModal} aria-label="Đóng bảng tạo bài viết"><IconClose size={18} /></button></header>
      {!group && <nav className={styles.kindGrid} aria-label="Chọn nơi đăng bài">{availableKinds.map(item => <button key={item.category} type="button" disabled={s.isSubmitting} data-category={item.category} aria-pressed={s.category === item.category} className={styles.kindCard} onClick={() => { s.setCategory(item.category); s.setLocation(null); setErrors({}); setPreview(false); }}><span className={styles.iconTile}><CategoryIcon category={item.category} /></span><span><strong>{item.label}</strong><small>{item.description}</small></span></button>)}{!availableKinds.length && <p className={styles.noGroups}>Bạn chưa tham gia nhóm nào. <Link href="/groups" onClick={s.closeModal}>Khám phá và tham gia nhóm →</Link></p>}<button type="button" className={styles.textButton} disabled={s.isSubmitting} aria-pressed={s.category === 'general'} onClick={() => { s.setCategory('general'); setErrors({}); setPreview(false); }}>Bài viết cá nhân</button></nav>}
      <div className={styles.author}><UserAvatar src={author?.avatar_url} name={author?.full_name || author?.username} imageClassName={styles.avatar} fallbackClassName={styles.avatar} /><div><strong>{author?.full_name || author?.username || 'Bạn'}</strong><span>{isGroup ? 'Đăng trong ' + (selectedGroup?.name || kind?.label) + ' · Chờ quản trị viên duyệt' : 'Chia sẻ trên trang cá nhân của bạn'}</span></div></div>
      {(unavailable || needsMembership) && <div className={styles.notice} role="status">{unavailable ? groupsLoading ? 'Đang kiểm tra nhóm đăng bài…' : 'Không tải được nhóm. Hãy đóng và mở lại để thử lại.' : <>Bạn cần tham gia nhóm trước khi đăng bài. <Link href={'/groups?group=' + selectedGroup?.id} onClick={s.closeModal}>Đi tới nhóm →</Link></>}</div>}
      <form ref={form} noValidate onSubmit={e => { e.preventDefault(); void publish(); }} className={styles.form}>
        <div className={styles.workspace}>
          <fieldset disabled={s.isSubmitting} className={styles.editor} hidden={preview}>
            <div className={styles.sectionHeading}><strong>Thông tin bài đăng</strong><small><span className={styles.required}>*</span> Bắt buộc</small></div>
            {!isGroup && <label className={styles.privacy}>Ai có thể xem?<select value={s.privacy} onChange={e => s.setPrivacy(e.target.value as typeof s.privacy)}><option value="public">Công khai</option><option value="friends">Bạn bè</option><option value="private">Chỉ mình tôi</option></select></label>}
            <GroupPostFields state={s} errors={errors} onPickLocation={() => setLocationOpen(true)} />
            {s.category === 'general' && <button type="button" className={styles.textButton} onClick={() => setLocationOpen(true)}>⌖ {s.location?.name || 'Thêm vị trí (tùy chọn)'}</button>}
            <div className={styles.uploadSection}><div className={styles.sectionHeading}><strong>Ảnh / Video / Tài liệu</strong><small>Tùy chọn · {s.mediaList.length}/10</small></div><button type="button" className={styles.dropzone} onClick={() => fileInput.current?.click()}><span aria-hidden="true">＋</span><strong>Thêm tệp đính kèm</strong><small>Ảnh, video hoặc tài liệu · Tối đa 10 tệp</small></button><input ref={fileInput} type="file" hidden multiple accept="image/jpeg,image/png,image/webp,video/mp4,video/webm,video/quicktime,audio/mpeg,audio/mp4,audio/ogg,audio/wav,audio/webm,application/pdf,text/plain,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.zip" onChange={e => { if (e.target.files) s.addMediaFiles(e.target.files); e.target.value = ''; }} />
              {s.mediaList.length > 0 && <div className={styles.attachments}>{s.mediaList.map(item => <div key={item.id} className={styles.attachment}>{item.type === 'image' ? <img src={item.url} alt={item.name || 'Ảnh đính kèm'} /> : <span className={styles.fileIcon}>{item.type === 'video' ? '▶' : item.type === 'audio' ? '♫' : '▤'}</span>}<div><strong>{item.name}</strong><small>{item.uploadStatus === 'uploading' ? 'Đang tải ' + (item.uploadProgress || 0) + '%' : item.uploadStatus === 'complete' ? 'Đã tải lên' : item.uploadStatus === 'error' ? item.uploadError || 'Tải lên lỗi' : ((item.size || 0) / 1024 / 1024).toFixed(1) + ' MB'}</small></div><button type="button" onClick={() => s.removeMedia(item.id)} aria-label={'Xóa ' + item.name}>×</button></div>)}</div>}
            </div>
          </fieldset>
          <aside className={styles.previewPanel + (preview ? ' ' + styles.previewExpanded : '')} aria-label="Xem trước bài đăng">
            <div className={styles.sectionHeading}><strong>Xem trước bài đăng</strong><span className={styles.liveDot}>Trực tiếp</span></div><article className={styles.previewCard}><div className={styles.previewAuthor}><UserAvatar src={author?.avatar_url} name={author?.full_name || author?.username} imageClassName={styles.avatar} fallbackClassName={styles.avatar} /><div><strong>{author?.full_name || author?.username || 'Bạn'}</strong><small>{kind?.label || 'Trang cá nhân'} · Vừa xong</small></div></div><PostCategoryDetails post={draft} /><p className={styles.previewText}>{s.content || 'Nội dung chia sẻ sẽ hiển thị tại đây.'}</p>{s.mediaList.slice(0, preview ? 10 : 2).map(item => <div key={item.id} className={styles.previewMedia}>{item.type === 'image' ? <img src={item.url} alt={item.name || 'Ảnh xem trước'} /> : item.type === 'video' ? <video src={item.url} controls preload="metadata" /> : item.type === 'audio' ? <audio src={item.url} controls /> : <span>▤ {item.name}</span>}</div>)}{!preview && s.mediaList.length > 2 && <small className={styles.moreFiles}>+{s.mediaList.length - 2} tệp khác</small>}<div className={styles.previewFooter}><span>♡ Thích</span><span>◯ Bình luận</span></div></article><p className={styles.previewHint}>{isGroup ? 'Bài đăng sẽ hiển thị trong nhóm và các bảng tin được phép sau khi duyệt.' : 'Kiểm tra nội dung và quyền riêng tư trước khi chia sẻ.'}</p>
          </aside>
        </div>
        {s.error && <div className={styles.errorBanner} role="alert">{s.error}</div>}
        <footer className={styles.footer}><span>{isGroup ? 'Chia sẻ đúng nhóm, kết nối đúng người.' : 'Một chia sẻ nhỏ, thêm một kết nối.'}</span><button type="button" className={styles.secondary} disabled={s.isSubmitting} onClick={() => { if (preview) setPreview(false); else if (validate()) setPreview(true); }}>{preview ? '← Chỉnh sửa' : 'Xem trước'}</button><button type="submit" className={styles.primary} disabled={s.isSubmitting || unavailable || needsMembership}>{s.isSubmitting ? 'Đang gửi…' : isGroup ? 'Gửi bài chờ duyệt' : 'Đăng bài'}</button></footer>
      </form>
      <LocationPicker open={locationOpen} onClose={() => setLocationOpen(false)} onSelect={place => { s.setLocation(place); const label = place.address || place.name; if (s.category === 'market') s.setMarketListing(p => ({ ...p, location: label })); if (s.category === 'roommate') s.setRoomListing(p => ({ ...p, location: label })); if (s.category === 'event') s.setEventListing(p => ({ ...p, location: label })); setLocationOpen(false); }} />
    </section>
  </div>, document.body);
}
