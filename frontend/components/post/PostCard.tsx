"use client";

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { Post, Comment, CommentMention } from '@/types/post';
import { IconHeart, IconMessage } from '@/components/ui/Icons';
import { addPostComment, fetchPostComments, fetchUserFriends, removeGroupComment, setPostLike } from '@/lib/api';
import { AuthUser, getAuthUser } from '@/lib/auth';
import { useAuthUser } from '@/components/auth/AuthProvider';
import PostActionModal from '@/components/post/PostActionModal';
import CommentActionModal from '@/components/post/CommentActionModal';
import { safeImageSrc } from '@/lib/media';
import { useDialog } from '@/components/ui/DialogProvider';
import RelativeTime from '@/components/ui/RelativeTime';
import type { UserFriend } from '@/types/user';

function renderCommentContent(content: string, mentions: CommentMention[] = []) {
  const validMentions = [...mentions]
    .filter(mention => mention.start >= 0 && mention.end <= content.length && mention.end > mention.start)
    .sort((a, b) => a.start - b.start);
  if (!validMentions.length) return content;
  const parts: React.ReactNode[] = [];
  let cursor = 0;
  validMentions.forEach((mention, index) => {
    if (mention.start < cursor || content.slice(mention.start, mention.end) !== `@${mention.name}`) return;
    if (mention.start > cursor) parts.push(content.slice(cursor, mention.start));
    parts.push(<Link href={`/profile/${mention.userId}`} className="comment-mention-link" key={`${mention.userId}-${index}`}><strong className="comment-mention">{content.slice(mention.start, mention.end)}</strong></Link>);
    cursor = mention.end;
  });
  if (cursor < content.length) parts.push(content.slice(cursor));
  return parts.length ? parts : content;
}

const privacyLabel = {
  public: { icon: '🌐', label: 'Công khai' },
  friends: { icon: '👥', label: 'Bạn bè' },
  private: { icon: '🔒', label: 'Chỉ mình tôi' },
} as const;

interface PostCardProps {
  post: Post;
  onLikeToggle?: (postId: string, isLiked: boolean) => void;
  onAddComment?: (postId: string, commentText: string) => void;
  moderatorGroupId?: string;
  moderatorActions?: { isPinned: boolean; busy: boolean; onTogglePin: () => void; onRemove: () => void };
  highlightCommentId?: string | null;
}

export default function PostCard({
  post,
  onLikeToggle,
  onAddComment,
  moderatorGroupId,
  moderatorActions,
  highlightCommentId,
}: PostCardProps) {
  const dialog = useDialog();
  const [isLiked, setIsLiked] = useState(post.isLiked || false);
  const [likesCount, setLikesCount] = useState(post.likesCount || 0);
  const [commentsCount, setCommentsCount] = useState(post.commentsCount || 0);
  const [comments, setComments] = useState<Comment[]>(post.comments || []);
  const [loadingAllComments, setLoadingAllComments] = useState(false);
  const [isLiking, setIsLiking] = useState(false);
  const [isSubmittingComment, setIsSubmittingComment] = useState(false);
  const [isCommentSectionOpen, setIsCommentSectionOpen] = useState(false);
  const [commentInput, setCommentInput] = useState('');
  const [mentionQuery, setMentionQuery] = useState<string | null>(null);
  const [mentionStart, setMentionStart] = useState(0);
  const [mentionFriends, setMentionFriends] = useState<UserFriend[]>([]);
  const [mentionFriendsLoaded, setMentionFriendsLoaded] = useState(false);
  const [mentionLoading, setMentionLoading] = useState(false);
  const [mentionActiveIndex, setMentionActiveIndex] = useState(0);
  const [selectedMentions, setSelectedMentions] = useState<CommentMention[]>([]);
  const commentInputRef = useRef<HTMLInputElement>(null);
  const mentionFriendsRequestStarted = useRef(false);
  const [commentImage,setCommentImage]=useState<File|null>(null);
  const [replyTo,setReplyTo]=useState<Comment|null>(null);
  const [content, setContent] = useState(post.content);
  const [privacy,setPrivacy]=useState(post.privacy);
  const [actionMode,setActionMode]=useState<'edit'|'delete'|'report'|null>(null);
  const [commentAction,setCommentAction]=useState<{comment:Comment;mode:'edit'|'delete'|'report'}|null>(null);
  const [isOwner, setIsOwner] = useState(false);
  const [isDeleted, setIsDeleted] = useState(false);
  const [actionError, setActionError] = useState('');
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [viewer, setViewer] = useState<AuthUser | null>(null);
  const authenticatedUser = useAuthUser();
  const mentionMatches = mentionQuery === null ? [] : mentionFriends.filter((friend) => {
    const query = mentionQuery.trim().toLocaleLowerCase();
    return !query || friend.name.toLocaleLowerCase().includes(query) || friend.username.toLocaleLowerCase().includes(query);
  }).slice(0, 8);

  useEffect(() => {
    if (mentionQuery === null || !authenticatedUser?.id || mentionFriendsLoaded || mentionFriendsRequestStarted.current) return;
    mentionFriendsRequestStarted.current = true;
    setMentionLoading(true);
    void fetchUserFriends(authenticatedUser.id).then((friends) => {
      setMentionFriends(friends);
      setMentionFriendsLoaded(true);
    }).catch(() => {
      setMentionFriendsLoaded(true);
    }).finally(() => {
      setMentionLoading(false);
    });
  }, [mentionQuery, authenticatedUser?.id, mentionFriendsLoaded]);

  useEffect(() => setMentionActiveIndex(0), [mentionQuery]);

  const updateMentionQuery = (value: string, caret: number) => {
    const beforeCaret = value.slice(0, caret);
    const atIndex = beforeCaret.lastIndexOf('@');
    if (atIndex < 0 || (atIndex > 0 && !/\s/.test(beforeCaret[atIndex - 1]))) {
      setMentionQuery(null);
      return;
    }
    const query = beforeCaret.slice(atIndex + 1);
    if (/[\n@]/.test(query)) {
      setMentionQuery(null);
      return;
    }
    setMentionStart(atIndex);
    setMentionQuery(query);
  };

  const updateSelectedMentions = (value: string) => {
    const previous = commentInput;
    let prefix = 0;
    while (prefix < previous.length && prefix < value.length && previous[prefix] === value[prefix]) prefix += 1;
    let suffix = 0;
    while (suffix < previous.length - prefix && suffix < value.length - prefix && previous[previous.length - suffix - 1] === value[value.length - suffix - 1]) suffix += 1;
    const replacedEnd = previous.length - suffix;
    const delta = value.length - previous.length;
    setSelectedMentions(current => current.flatMap(mention => {
      let next = mention;
      if (mention.start >= replacedEnd && mention.start >= prefix) next = { ...mention, start: mention.start + delta, end: mention.end + delta };
      else if (mention.end > prefix) return [];
      return value.slice(next.start, next.end) === `@${next.name}` ? [next] : [];
    }));
  };

  const insertMention = (friend: UserFriend) => {
    const input = commentInputRef.current;
    const caret = input?.selectionStart ?? commentInput.length;
    const label = `@${friend.name}`;
    const next = `${commentInput.slice(0, mentionStart)}${label} ${commentInput.slice(caret)}`;
    const end = mentionStart + label.length;
    setSelectedMentions(current => [...current.filter(mention => mention.end <= mentionStart || mention.start >= caret), {
      userId: friend.id, name: friend.name, username: friend.username, start: mentionStart, end,
    }].sort((a, b) => a.start - b.start));
    const nextCaret = end + 1;
    setCommentInput(next);
    setMentionQuery(null);
    requestAnimationFrame(() => {
      input?.focus();
      input?.setSelectionRange(nextCaret, nextCaret);
    });
  };

  const handleCommentKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (mentionQuery === null || mentionMatches.length === 0) {
      if (event.key === 'Escape') setMentionQuery(null);
      return;
    }
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setMentionActiveIndex(index => (index + 1) % mentionMatches.length);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setMentionActiveIndex(index => (index - 1 + mentionMatches.length) % mentionMatches.length);
    } else if (event.key === 'Enter' || event.key === 'Tab') {
      event.preventDefault();
      insertMention(mentionMatches[mentionActiveIndex] || mentionMatches[0]);
    } else if (event.key === 'Escape') {
      setMentionQuery(null);
    }
  };
  const loadAllComments = async () => {
    if (loadingAllComments || comments.length >= commentsCount) return;
    setLoadingAllComments(true);
    try { setComments(await fetchPostComments(post.id)); }
    catch (error) { setActionError(error instanceof Error ? error.message : 'Không thể tải thêm bình luận.'); }
    finally { setLoadingAllComments(false); }
  };
  useEffect(() => {
    if (!highlightCommentId) return;
    setIsCommentSectionOpen(true);
    void fetchPostComments(post.id, 100, highlightCommentId).then(setComments).catch(error => setActionError(error instanceof Error ? error.message : 'Không thể tải bình luận.'));
  }, [highlightCommentId, post.id]);
  useEffect(() => {
    if (!highlightCommentId || !comments.some(comment => comment.id === highlightCommentId)) return;
    const timer = window.setTimeout(() => document.getElementById(`comment-${highlightCommentId}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 120);
    return () => window.clearTimeout(timer);
  }, [comments, highlightCommentId]);
  const imageMedia = (post.media || []).filter((item) => item.type === 'image');
  const visualMedia = (post.media || []).filter((item) => item.type === 'image' || item.type === 'video');
  const attachmentMedia = (post.media || []).filter((item) => item.type === 'audio' || item.type === 'file');
  const currentPrivacy = privacyLabel[privacy as keyof typeof privacyLabel] || privacyLabel.public;

  useEffect(() => {
    setViewer(authenticatedUser);
    setIsOwner(authenticatedUser?.id === post.author.id);
  }, [authenticatedUser, post.author.id]);
  useEffect(() => {
    if (!actionError) return;
    const timer = window.setTimeout(() => setActionError(''), 6000);
    return () => window.clearTimeout(timer);
  }, [actionError]);
  useEffect(()=>{if(lightboxIndex===null)return;const handle=(event:KeyboardEvent)=>{if(event.key==='Escape')setLightboxIndex(null);if(event.key==='ArrowLeft')setLightboxIndex(current=>current===null?null:(current-1+imageMedia.length)%imageMedia.length);if(event.key==='ArrowRight')setLightboxIndex(current=>current===null?null:(current+1)%imageMedia.length);};document.body.style.overflow='hidden';window.addEventListener('keydown',handle);return()=>{document.body.style.overflow='';window.removeEventListener('keydown',handle);};},[lightboxIndex,imageMedia.length]);

  const handleLike = async () => {
    if (isLiking) return;
    setIsLiking(true);
    const nextIsLiked = !isLiked;
    setIsLiked(nextIsLiked);
    setLikesCount((prev) => (nextIsLiked ? prev + 1 : Math.max(0, prev - 1)));
    try {
      const result = await setPostLike(post.id, nextIsLiked);
      setIsLiked(result.isLiked);
      setLikesCount(result.likesCount);
      onLikeToggle?.(post.id, result.isLiked);
    } catch (error) {
      setIsLiked(!nextIsLiked);
      setLikesCount((prev) => nextIsLiked ? Math.max(0, prev - 1) : prev + 1);
      setActionError(error instanceof Error ? error.message : 'Không thể cập nhật lượt thích.');
    } finally { setIsLiking(false); }
  };

  const handleCommentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((!commentInput.trim() && !commentImage) || isSubmittingComment) return;

    const value = commentInput.trim();
    const leadingTrim = commentInput.length - commentInput.trimStart().length;
    const mentions = selectedMentions
      .filter(mention => commentInput.slice(mention.start, mention.end) === `@${mention.name}`)
      .map(mention => ({ user_id: mention.userId, start: mention.start - leadingTrim, end: mention.end - leadingTrim }))
      .filter(mention => mention.start >= 0 && mention.end <= value.length);
    setIsSubmittingComment(true);
    setActionError('');
    try {
      const created = await addPostComment(post.id, value, replyTo?.id, commentImage || undefined, mentions);
      setComments((prev) => [...prev, created]);
      setCommentsCount((prev) => prev + 1);
      onAddComment?.(post.id, value);
      setCommentInput('');
      setSelectedMentions([]);
      setMentionQuery(null);
      setCommentImage(null);
      setReplyTo(null);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Không thể gửi bình luận.');
    } finally { setIsSubmittingComment(false); }
  };

  const handleEdit = () => setActionMode('edit');
  const handleDelete = () => setActionMode('delete');
  const handleReport = () => setActionMode('report');

  if (isDeleted) return null;

  return (
    <article className="post-card-item">
      {/* 1. Post Header */}
      <div className="post-card-header post-card-header-facebook">
        <Link href={`/profile/${post.author.id}`} className="author-avatar-link">
          <img
            src={post.author.avatar || '/assets/logo.png'}
            alt={post.author.name}
            className="author-avatar-img"
          />
        </Link>
        <div className="author-meta">
          <div className="author-name-row">
            <Link href={`/profile/${post.author.id}`} className="author-name">
              {post.author.name}
            </Link>
            {post.groupId && post.groupName && <><span className="post-group-arrow">›</span><Link href={`/groups?group=${post.groupId}`} className="post-group-link">{post.groupName}</Link></>}
          </div>
          <div className="post-time-privacy">
            <RelativeTime className="post-time" value={post.createdAt}/>
            <span className="dot-sep">·</span>
            <span className="privacy-badge" title={currentPrivacy.label} aria-label={currentPrivacy.label}>{currentPrivacy.icon}</span>
          </div>
        </div>
        <div className="post-more-wrap">
          <button type="button" className="post-more-button" aria-label="Tùy chọn bài viết" aria-expanded={menuOpen} onClick={() => setMenuOpen(value => !value)}>•••</button>
          {menuOpen && <div className="post-more-menu">
            {moderatorActions ? <>
              <button type="button" disabled={moderatorActions.busy} onClick={() => { setMenuOpen(false); moderatorActions.onTogglePin(); }}>{moderatorActions.isPinned ? 'Bỏ ghim bài' : 'Ghim bài'}</button>
              <button type="button" disabled={moderatorActions.busy} className="danger" onClick={() => { setMenuOpen(false); moderatorActions.onRemove(); }}>Gỡ bài khỏi nhóm</button>
            </> : isOwner ? <>
              <button type="button" onClick={() => { setMenuOpen(false); handleEdit(); }}>✏️ Chỉnh sửa bài viết</button>
              <button type="button" className="danger" onClick={() => { setMenuOpen(false); handleDelete(); }}>🗑️ Xóa bài viết</button>
            </> : !moderatorGroupId && <button type="button" onClick={() => { setMenuOpen(false); handleReport(); }}>⚑ Báo cáo bài viết</button>}
          </div>}
        </div>
      </div>

      {/* 2. Post Body Content */}
      <div className="post-card-body">
        <p className="post-text-content">{content}</p>

        {post.location && (
          post.location.latitude != null && post.location.longitude != null ? (
            <a
              className="post-location-link"
              href={`https://www.openstreetmap.org/?mlat=${post.location.latitude}&mlon=${post.location.longitude}#map=16/${post.location.latitude}/${post.location.longitude}`}
              target="_blank"
              rel="noreferrer"
              title={post.location.address || post.location.name}
            >
              <span aria-hidden="true">📍</span> {post.location.name}
            </a>
          ) : <span className="post-location-link" title={post.location.address || post.location.name}><span aria-hidden="true">📍</span> {post.location.name}</span>
        )}

        {post.marketListing && (
          <div className="post-special-badge market-badge">
            <span>
              🛒 Pass đồ: <strong>{post.marketListing.price}</strong> — {post.marketListing.location}
            </span>
          </div>
        )}

        {visualMedia.length > 0 && (
          <div className={`post-media-gallery count-${visualMedia.length}`}>
            {visualMedia.map((item) => (
              <div key={item.id} className={`media-item media-${item.type}`} onClick={()=>item.type==='image'&&setLightboxIndex(imageMedia.findIndex(image=>image.id===item.id))}>
                {item.type === 'image' ? (
                  <img src={safeImageSrc(item.url)} alt="Nội dung bài viết" />
                ) : (
                  <video src={item.url} controls preload="metadata" />
                )}
              </div>
            ))}
          </div>
        )}
        {attachmentMedia.length > 0 && <div className="post-attachments-list">
          {attachmentMedia.map(item => item.type === 'audio' ?
            <div key={item.id} className="post-audio-attachment"><span aria-hidden="true">🎵</span><div><strong>Âm thanh</strong><audio src={item.url} controls preload="metadata" /></div></div> :
            <a key={item.id} className="post-file-attachment" href={item.url} target="_blank" rel="noreferrer"><span aria-hidden="true">📎</span><span><strong>{item.name || 'Tệp đính kèm'}</strong><small>Mở tệp trong tab mới</small></span></a>
          )}
        </div>}
      </div>

      {/* 3. Post Footer Interaction Bar */}
      <div className="post-card-footer">
        {/* Like & Comment Counters Row */}
        <div className="post-stats-row">
          <span className="likes-count">👍 {likesCount} lượt thích</span>
          <button
            type="button"
            className="comments-count-btn"
            onClick={() => { setIsCommentSectionOpen(!isCommentSectionOpen); if (!isCommentSectionOpen) void loadAllComments(); }}
          >
            {commentsCount} bình luận
          </button>
        </div>

        <div className="post-action-divider" />

        {/* Primary Action Buttons: Like and Comment */}
        <div className="post-action-buttons-row">
          <button
            type="button"
            className={`post-action-btn ${isLiked ? 'liked' : ''}`}
            onClick={handleLike}
            disabled={isLiking}
            aria-busy={isLiking}
          >
            <IconHeart
              size={18}
              color={isLiked ? '#ef4444' : '#002855'}
              className="action-icon"
            />
            <span>{isLiked ? 'Đã thích' : 'Thích'}</span>
          </button>

          <button
            type="button"
            className="post-action-btn"
            onClick={() => { setIsCommentSectionOpen(!isCommentSectionOpen); if (!isCommentSectionOpen) void loadAllComments(); }}
          >
            <IconMessage size={18} color="#002855" className="action-icon" />
            <span>Bình luận</span>
          </button>
        </div>

        {/* 4. Expandable Comment Section */}
        {isCommentSectionOpen && (
          <div className="post-comments-section">
            {/* Comment Form Input */}
            <form onSubmit={handleCommentSubmit} className="comment-form-row">
              {replyTo&&<div className="comment-replying">Đang trả lời {replyTo.author.name}<button type="button" onClick={()=>setReplyTo(null)}>×</button></div>}
              {viewer?.avatar_url ? <img className="comment-composer-avatar" src={safeImageSrc(viewer.avatar_url)} alt={viewer.full_name || 'Avatar của bạn'} /> : <span className="comment-composer-avatar comment-avatar-initials">{(viewer?.full_name || viewer?.username || 'U').trim().split(/\s+/).slice(-2).map(part => part[0]).join('').toUpperCase()}</span>}
              <div className="comment-composer-shell">
                <input
                  type="text"
                  className="comment-input-field"
                  placeholder={replyTo ? `Trả lời ${replyTo.author.name}...` : 'Viết bình luận...'}
                  value={commentInput}
                  ref={commentInputRef}
                  onChange={(e) => {
                    updateSelectedMentions(e.target.value);
                    setCommentInput(e.target.value);
                    updateMentionQuery(e.target.value, e.target.selectionStart ?? e.target.value.length);
                  }}
                  onKeyDown={handleCommentKeyDown}
                  disabled={isSubmittingComment}
                />
                {mentionQuery !== null && (mentionLoading || mentionMatches.length > 0) && <div className="comment-mention-menu" role="listbox" aria-label="Gợi ý bạn bè để gắn thẻ">
                  {mentionLoading && <div className="comment-mention-loading">Đang tìm bạn bè…</div>}
                  {!mentionLoading && mentionMatches.map((friend, index) => <button type="button" role="option" aria-selected={index === mentionActiveIndex} className={index === mentionActiveIndex ? 'active' : ''} key={friend.id} onMouseDown={event => event.preventDefault()} onClick={() => insertMention(friend)}>
                    <img src={friend.avatar || '/assets/logo.png'} alt="" />
                    <span><strong>{friend.name}</strong><small>@{friend.username}</small></span>
                  </button>)}
                </div>}
                <label className="comment-image-button" title="Thêm ảnh" aria-label="Thêm ảnh">📷<input type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={e=>setCommentImage(e.target.files?.[0]||null)}/></label>
              </div>
              <button
                type="submit"
                className="comment-submit-btn"
                disabled={isSubmittingComment||(!commentInput.trim()&&!commentImage)}
                aria-label="Gửi bình luận"
                aria-busy={isSubmittingComment}
              >
                {isSubmittingComment ? '…' : '➤'}
              </button>
            </form>

            {/* Comments List Stream */}
            {comments.length > 0 ? (
              <div className="comments-stream-list">
                {commentsCount > comments.length && <button type="button" className="comments-count-btn" onClick={() => void loadAllComments()} disabled={loadingAllComments}>{loadingAllComments ? 'Đang tải bình luận...' : `Xem thêm ${commentsCount - comments.length} bình luận`}</button>}
                {comments.map((c) => (
                  <div id={`comment-${c.id}`} key={c.id} className={`comment-item-row ${c.parentId?'comment-reply-row':''} ${c.id===highlightCommentId?'notification-target-comment':''}`}>
                    <img
                      src={c.author.avatar || '/assets/logo.png'}
                      alt={c.author.name}
                      className="comment-author-avatar"
                    />
                    <div className="comment-content-column">
                      <div className="comment-bubble">
                        <Link href={`/profile/${c.author.id}`} className="comment-author-name">{c.author.name}</Link>
                        <p className="comment-text-body">{renderCommentContent(c.content, c.mentions)}</p>
                        {c.imageUrl&&<img className="comment-attached-image" src={safeImageSrc(c.imageUrl)} alt="Ảnh bình luận"/>}
                      </div>
                      <div className="comment-meta-row">
                        <RelativeTime className="comment-timestamp" value={c.createdAt}/>
                        <button type="button" className="comment-reply-button" onClick={()=>{const label=`@${c.author.name}`;setReplyTo(c);setCommentInput(`${label} `);setSelectedMentions([{userId:c.author.id,name:c.author.name,start:0,end:label.length}]);setMentionQuery(null);}}>Trả lời</button>
                        {moderatorGroupId&&c.author.id!==getAuthUser()?.id&&<button type="button" className="comment-reply-button" onClick={()=>{void dialog.confirm({title:'Xóa bình luận khỏi nhóm?',message:'Bình luận sẽ không còn hiển thị với thành viên.',confirmLabel:'Xóa bình luận',tone:'danger'}).then(ok=>{if(ok)return removeGroupComment(moderatorGroupId,c.id).then(()=>{setComments(current=>current.filter(item=>item.id!==c.id));setCommentsCount(current=>Math.max(0,current-1));dialog.notify({title:'Đã xóa bình luận',tone:'success'});});}).catch(e=>setActionError(e instanceof Error?e.message:'Không thể xóa bình luận.'));}}>Xóa khỏi nhóm</button>}
                        <div className="comment-manage-actions">{c.author.id===getAuthUser()?.id?<><button onClick={()=>setCommentAction({comment:c,mode:'edit'})}>Sửa</button><button onClick={()=>setCommentAction({comment:c,mode:'delete'})}>Xóa</button></>:<button onClick={()=>setCommentAction({comment:c,mode:'report'})}>Báo cáo</button>}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-comments-yet">Chưa có bình luận nào. Hãy là người đầu tiên bình luận!</p>
            )}
          </div>
        )}
        {actionError && <div className="post-error-banner">{actionError}</div>}
      </div>
      {lightboxIndex!==null&&imageMedia[lightboxIndex]&&<div className="post-media-lightbox" role="dialog" aria-modal="true" aria-label="Xem ảnh bài viết" onClick={()=>setLightboxIndex(null)}><button type="button" className="lightbox-close" onClick={()=>setLightboxIndex(null)} aria-label="Đóng">×</button>{imageMedia.length>1&&<button type="button" className="lightbox-prev" onClick={event=>{event.stopPropagation();setLightboxIndex((lightboxIndex-1+imageMedia.length)%imageMedia.length);}} aria-label="Ảnh trước">‹</button>}<img src={safeImageSrc(imageMedia[lightboxIndex].url)} alt="Nội dung bài viết" onClick={event=>event.stopPropagation()}/>{imageMedia.length>1&&<button type="button" className="lightbox-next" onClick={event=>{event.stopPropagation();setLightboxIndex((lightboxIndex+1)%imageMedia.length);}} aria-label="Ảnh tiếp theo">›</button>}<span className="lightbox-counter">{lightboxIndex+1} / {imageMedia.length}</span></div>}
      <PostActionModal mode={actionMode} post={post} content={content} privacy={privacy} onClose={()=>setActionMode(null)} onUpdated={updated=>{setContent(updated.content);setPrivacy(updated.privacy);}} onDeleted={()=>setIsDeleted(true)} onMessage={message=>dialog.notify({title:message,tone:'success'})}/>
      <CommentActionModal comment={commentAction?.comment||null} mode={commentAction?.mode||null} onClose={()=>setCommentAction(null)} onUpdated={updated=>setComments(current=>current.map(item=>item.id===updated.id?updated:item))} onDeleted={()=>{if(commentAction){setComments(current=>current.filter(item=>item.id!==commentAction.comment.id));setCommentsCount(current=>Math.max(0,current-1));}}} onMessage={message=>dialog.notify({title:message,tone:'success'})}/>
    </article>
  );
}
