"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Post, Comment } from '@/types/post';
import { IconHeart, IconMessage } from '@/components/ui/Icons';
import { addPostComment, removeGroupComment, setPostLike } from '@/lib/api';
import { AuthUser, getAuthUser, getCurrentUser } from '@/lib/auth';
import PostActionModal from '@/components/post/PostActionModal';
import CommentActionModal from '@/components/post/CommentActionModal';
import { safeImageSrc } from '@/lib/media';
import { useDialog } from '@/components/ui/DialogProvider';
import RelativeTime from '@/components/ui/RelativeTime';

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
}

export default function PostCard({
  post,
  onLikeToggle,
  onAddComment,
  moderatorGroupId,
}: PostCardProps) {
  const dialog = useDialog();
  const [isLiked, setIsLiked] = useState(post.isLiked || false);
  const [likesCount, setLikesCount] = useState(post.likesCount || 0);
  const [commentsCount, setCommentsCount] = useState(post.commentsCount || 0);
  const [comments, setComments] = useState<Comment[]>(post.comments || []);
  const [isCommentSectionOpen, setIsCommentSectionOpen] = useState(false);
  const [commentInput, setCommentInput] = useState('');
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
  const imageMedia = (post.media || []).filter((item) => item.type === 'image');
  const visualMedia = (post.media || []).filter((item) => item.type === 'image' || item.type === 'video');
  const attachmentMedia = (post.media || []).filter((item) => item.type === 'audio' || item.type === 'file');
  const currentPrivacy = privacyLabel[privacy as keyof typeof privacyLabel] || privacyLabel.public;

  useEffect(() => {
    const stored = getAuthUser();
    setViewer(stored);
    setIsOwner(stored?.id === post.author.id);
    void getCurrentUser().then(user => { setViewer(user); setIsOwner(user.id === post.author.id); }).catch(() => undefined);
  }, [post.author.id]);
  useEffect(()=>{if(lightboxIndex===null)return;const handle=(event:KeyboardEvent)=>{if(event.key==='Escape')setLightboxIndex(null);if(event.key==='ArrowLeft')setLightboxIndex(current=>current===null?null:(current-1+imageMedia.length)%imageMedia.length);if(event.key==='ArrowRight')setLightboxIndex(current=>current===null?null:(current+1)%imageMedia.length);};document.body.style.overflow='hidden';window.addEventListener('keydown',handle);return()=>{document.body.style.overflow='';window.removeEventListener('keydown',handle);};},[lightboxIndex,imageMedia.length]);

  const handleLike = async () => {
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
    }
  };

  const handleCommentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentInput.trim() && !commentImage) return;

    const value = commentInput.trim();
    try {
      const created = await addPostComment(post.id, value, replyTo?.id, commentImage || undefined);
      setComments((prev) => [...prev, created]);
      setCommentsCount((prev) => prev + 1);
      onAddComment?.(post.id, value);
      setCommentInput('');
      setCommentImage(null);
      setReplyTo(null);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Không thể gửi bình luận.');
    }
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
            {isOwner ? <>
              <button type="button" onClick={() => { setMenuOpen(false); handleEdit(); }}>✏️ Chỉnh sửa bài viết</button>
              <button type="button" className="danger" onClick={() => { setMenuOpen(false); handleDelete(); }}>🗑️ Xóa bài viết</button>
            </> : <button type="button" onClick={() => { setMenuOpen(false); handleReport(); }}>⚑ Báo cáo bài viết</button>}
          </div>}
        </div>
      </div>

      {/* 2. Post Body Content */}
      <div className="post-card-body">
        <p className="post-text-content">{content}</p>

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
            onClick={() => setIsCommentSectionOpen(!isCommentSectionOpen)}
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
            onClick={() => setIsCommentSectionOpen(!isCommentSectionOpen)}
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
                  onChange={(e) => setCommentInput(e.target.value)}
                />
                <label className="comment-image-button" title="Thêm ảnh" aria-label="Thêm ảnh">📷<input type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={e=>setCommentImage(e.target.files?.[0]||null)}/></label>
              </div>
              <button
                type="submit"
                className="comment-submit-btn"
                disabled={!commentInput.trim()&&!commentImage}
                aria-label="Gửi bình luận"
              >
                ➤
              </button>
            </form>

            {/* Comments List Stream */}
            {comments.length > 0 ? (
              <div className="comments-stream-list">
                {comments.map((c) => (
                  <div key={c.id} className={`comment-item-row ${c.parentId?'comment-reply-row':''}`}>
                    <img
                      src={c.author.avatar || '/assets/logo.png'}
                      alt={c.author.name}
                      className="comment-author-avatar"
                    />
                    <div className="comment-content-column">
                      <div className="comment-bubble">
                        <div className="comment-author-name">{c.author.name}</div>
                        <p className="comment-text-body">{c.content}</p>
                        {c.imageUrl&&<img className="comment-attached-image" src={safeImageSrc(c.imageUrl)} alt="Ảnh bình luận"/>}
                      </div>
                      <div className="comment-meta-row">
                        <RelativeTime className="comment-timestamp" value={c.createdAt}/>
                        <button type="button" className="comment-reply-button" onClick={()=>{setReplyTo(c);setCommentInput(`@${c.author.name} `);}}>Trả lời</button>
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
      <PostActionModal mode={actionMode} post={post} content={content} privacy={privacy} onClose={()=>setActionMode(null)} onUpdated={updated=>{setContent(updated.content);setPrivacy(updated.privacy);}} onDeleted={()=>setIsDeleted(true)} onMessage={setActionError}/>
      <CommentActionModal comment={commentAction?.comment||null} mode={commentAction?.mode||null} onClose={()=>setCommentAction(null)} onUpdated={updated=>setComments(current=>current.map(item=>item.id===updated.id?updated:item))} onDeleted={()=>{if(commentAction){setComments(current=>current.filter(item=>item.id!==commentAction.comment.id));setCommentsCount(current=>Math.max(0,current-1));}}} onMessage={setActionError}/>
    </article>
  );
}
