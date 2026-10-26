"use client";

import { useEffect, useMemo, useRef, useState } from 'react';
import { createDirectConversation, createProfilePost, fetchPost, fetchUserFriends, registerPostShare, sendChatMessage } from '@/lib/api';
import { postPath } from '@/lib/post-share';
import type { Post, PostPrivacy } from '@/types/post';
import type { UserFriend } from '@/types/user';
import styles from './SharePostModal.module.css';
import { useDialog } from '@/components/ui/DialogProvider';

type ShareTab = 'message' | 'feed' | 'link';

export default function SharePostModal({ post, viewerId, onClose, onShared }: { post: Post; viewerId?: string; onClose: () => void; onShared?: (count: number) => void }) {
  const [tab, setTab] = useState<ShareTab>('message');
  const [originalPost, setOriginalPost] = useState(post);
  const [resolvingOriginal, setResolvingOriginal] = useState(Boolean(post.sharedPostId));
  const [originalUnavailable, setOriginalUnavailable] = useState(false);
  const [friends, setFriends] = useState<UserFriend[]>([]);
  const [loadingFriends, setLoadingFriends] = useState(true);
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const [caption, setCaption] = useState('');
  const [privacy, setPrivacy] = useState<PostPrivacy>('friends');
  const [busy, setBusy] = useState(false);
  const busyRef = useRef(false);
  const dialog = useDialog();
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const url = typeof window === 'undefined' ? postPath(originalPost.id) : `${window.location.origin}${postPath(originalPost.id)}`;

  useEffect(() => {
    const first = post.sharedPostId;
    if (!first) return;
    let active = true;
    const resolve = async () => {
      let id = first;
      const seen = new Set([post.id]);
      for (let depth = 0; depth < 8; depth += 1) {
        if (seen.has(id)) throw new Error('Bài viết được chia sẻ không hợp lệ.');
        seen.add(id);
        const source = await fetchPost(id);
        const next = source.sharedPostId;
        if (!next) return source;
        id = next;
      }
      throw new Error('Bài chia sẻ lồng nhau quá sâu.');
    };
    void resolve().then(source => { if (active) setOriginalPost(source); })
      .catch(() => { if (active) { setOriginalUnavailable(true); setError('Không thể xác minh bài viết gốc để chia sẻ.'); } })
      .finally(() => { if (active) setResolvingOriginal(false); });
    return () => { active = false; };
  }, [post]);

  useEffect(() => {
    if (!viewerId) { setLoadingFriends(false); return; }
    let active = true;
    void fetchUserFriends(viewerId).then(rows => { if (active) setFriends(rows.filter(row => row.id !== viewerId && (!row.accountStatus || row.accountStatus === 'ACTIVE'))); })
      .catch(() => { if (active) setError('Không tải được danh sách bạn bè.'); })
      .finally(() => { if (active) setLoadingFriends(false); });
    return () => { active = false; };
  }, [viewerId]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape' && !busy) onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [busy, onClose]);

  const filtered = useMemo(() => {
    const normalize = (value: string) => value.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLocaleLowerCase().replace(/đ/g, 'd');
    return friends.filter(friend => normalize(`${friend.name} ${friend.username}`).includes(normalize(query.trim())));
  }, [friends, query]);
  const toggle = (id: string) => setSelected(current => current.includes(id) ? current.filter(item => item !== id) : [...current, id]);
  const send = async () => {
    if (!selected.length || busyRef.current || resolvingOriginal || originalUnavailable) return;
    busyRef.current = true;
    setBusy(true); setError(''); setSuccess('');
    let sent = 0;
    let shareCountErrors = 0;
    let currentId = '';
    let delivered = false;
    try {
      for (const id of selected) {
        currentId = id;
        delivered = false;
        const conversation = await createDirectConversation(id);
        const message = await sendChatMessage(conversation.id, `${caption.trim() ? `${caption.trim()}\n` : ''}${url}`);
        sent += 1;
        delivered = true;
        try {
          const result = await registerPostShare(originalPost.id, 'MESSAGE', message.id);
          if (post.id === originalPost.id) onShared?.(result.sharesCount);
        } catch { shareCountErrors += 1; }
      }
      dialog.notify({ title: `Đã gửi bài viết cho ${sent} người bạn`, tone: 'success' });
      if (shareCountErrors) dialog.notify({ title: 'Lượt chia sẻ chưa cập nhật', message: 'Tin nhắn đã được gửi; bạn không cần gửi lại.', tone: 'danger' });
      onClose();
    } catch (cause) {
      setSelected(current => current.slice(sent));
      const detail = cause instanceof Error ? cause.message : 'Không thể gửi bài viết.';
      if (!delivered && currentId && detail.includes('Không tìm thấy người dùng')) {
        setFriends(current => current.filter(friend => friend.id !== currentId));
        setSelected(current => current.filter(id => id !== currentId));
        setError(`${sent ? `Đã gửi cho ${sent} người. ` : ''}Tài khoản bạn chọn không còn khả dụng để nhắn tin. Danh sách bạn bè đã được cập nhật.`);
      } else {
        setError(`${sent ? `Đã gửi cho ${sent} người. ` : ''}${detail}`);
      }
      if (!sent && viewerId) void fetchUserFriends(viewerId).then(rows => setFriends(rows.filter(row => row.id !== viewerId && (!row.accountStatus || row.accountStatus === 'ACTIVE')))).catch(() => undefined);
    } finally { busyRef.current = false; setBusy(false); }
  };
  const publish = async () => {
    if (busyRef.current || resolvingOriginal || originalUnavailable) return;
    busyRef.current = true;
    setBusy(true); setError(''); setSuccess('');
    try {
      const created = await createProfilePost({ content: `${caption.trim() ? `${caption.trim()}\n` : ''}${url}`, category: 'general', privacy, media: [], taggedFriends: [] });
      try {
        const result = await registerPostShare(originalPost.id, 'POST', created.id);
        if (post.id === originalPost.id) onShared?.(result.sharesCount);
      } catch {
        dialog.notify({ title: 'Bài đã đăng', message: 'Lượt chia sẻ chưa cập nhật. Bạn không cần đăng lại.', tone: 'danger' });
      }
      window.dispatchEvent(new Event('hvnh-post-shared'));
      dialog.notify({ title: 'Đã chia sẻ lên trang cá nhân', tone: 'success' });
      onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Không thể chia sẻ bài viết.'); }
    finally { busyRef.current = false; setBusy(false); }
  };
  const copy = async () => {
    if (resolvingOriginal || originalUnavailable) return;
    setError(''); setSuccess('');
    try { await navigator.clipboard.writeText(url); setSuccess('Đã sao chép liên kết bài viết.'); }
    catch { setError('Trình duyệt không cho sao chép. Hãy chọn và sao chép liên kết bên dưới.'); }
  };

  return <div className={styles.overlay} role="presentation" onMouseDown={event => { if (event.target === event.currentTarget && !busy) onClose(); }}>
    <section className={styles.dialog} role="dialog" aria-modal="true" aria-label="Chia sẻ bài viết">
      <header className={styles.header}><div><span>HVNH HUB</span><h2>Chia sẻ bài viết</h2></div><button type="button" onClick={onClose} disabled={busy} aria-label="Đóng">×</button></header>
      <div className={styles.preview}><strong>{originalPost.author.name}</strong><span>{originalPost.groupName ? `Trong nhóm ${originalPost.groupName}` : 'Bài viết cá nhân'} · {originalPost.privacy === 'public' ? 'Công khai' : originalPost.privacy === 'friends' ? 'Bạn bè' : 'Chỉ mình tôi'}</span><p>{resolvingOriginal ? 'Đang tìm bài viết gốc…' : originalPost.content?.trim() || 'Bài viết có ảnh hoặc tệp đính kèm'}</p></div>
      <div className={styles.tabs} role="tablist" aria-label="Cách chia sẻ">
        <button type="button" role="tab" aria-selected={tab === 'message'} className={tab === 'message' ? styles.active : ''} onClick={() => { setTab('message'); setError(''); setSuccess(''); }}>Tin nhắn</button>
        <button type="button" role="tab" aria-selected={tab === 'feed'} className={tab === 'feed' ? styles.active : ''} onClick={() => { setTab('feed'); setError(''); setSuccess(''); }}>Trang cá nhân</button>
        <button type="button" role="tab" aria-selected={tab === 'link'} className={tab === 'link' ? styles.active : ''} onClick={() => { setTab('link'); setError(''); setSuccess(''); }}>Sao chép link</button>
      </div>
      <div className={styles.body}>
        {tab === 'message' && <><label htmlFor={`share-search-${post.id}`}>Gửi cho bạn bè</label><input id={`share-search-${post.id}`} value={query} onChange={event => setQuery(event.target.value)} placeholder="Tìm tên bạn bè…" /><div className={styles.friends}>{loadingFriends ? <p>Đang tải bạn bè…</p> : filtered.length ? filtered.map(friend => <label key={friend.id} className={styles.friend}><input type="checkbox" checked={selected.includes(friend.id)} onChange={() => toggle(friend.id)} /><img src={friend.avatar || '/assets/logo.png'} alt="" /><span>{friend.name}<small>@{friend.username}</small></span></label>) : <p>{friends.length ? 'Không tìm thấy bạn bè phù hợp.' : 'Bạn chưa có bạn bè để gửi.'}</p>}</div><textarea value={caption} onChange={event => setCaption(event.target.value)} maxLength={500} placeholder="Thêm lời nhắn (không bắt buộc)…" /></>}
        {tab === 'feed' && <><label htmlFor={`share-caption-${post.id}`}>Bạn muốn nói gì về bài viết này?</label><textarea id={`share-caption-${post.id}`} value={caption} onChange={event => setCaption(event.target.value)} maxLength={2000} placeholder="Viết cảm nghĩ của bạn…" /><label htmlFor={`share-privacy-${post.id}`}>Ai có thể xem bài chia sẻ?</label><select id={`share-privacy-${post.id}`} value={privacy} onChange={event => setPrivacy(event.target.value as PostPrivacy)}><option value="public">Công khai</option><option value="friends">Bạn bè</option><option value="private">Chỉ mình tôi</option></select></>}
        {tab === 'link' && <><label htmlFor={`share-url-${post.id}`}>Liên kết bài viết</label><input id={`share-url-${post.id}`} value={url} readOnly onFocus={event => event.currentTarget.select()} /></>}
        <small className={styles.warning}>Người mở liên kết vẫn cần có quyền xem bài gốc; bài trong nhóm chỉ hiển thị với thành viên.</small>
        {originalUnavailable && !error && <p className={styles.error} role="alert">Không thể xác minh bài viết gốc để chia sẻ.</p>}
        {error && <p className={styles.error} role="alert">{error}</p>}{success && <p className={styles.success} role="status">{success}</p>}
      </div>
      <footer className={styles.footer}><button type="button" onClick={onClose} disabled={busy}>Đóng</button><button type="button" className={styles.primary} disabled={busy || resolvingOriginal || originalUnavailable || (tab === 'message' && !selected.length)} onClick={() => void (tab === 'message' ? send() : tab === 'feed' ? publish() : copy())}>{busy ? 'Đang xử lý…' : tab === 'message' ? `Gửi${selected.length ? ` (${selected.length})` : ''}` : tab === 'feed' ? 'Chia sẻ bài viết' : 'Sao chép'}</button></footer>
    </section>
  </div>;
}
