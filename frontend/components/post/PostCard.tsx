"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { Post, Comment } from '@/types/post';
import { IconHeart, IconMessage } from '@/components/ui/Icons';

interface PostCardProps {
  post: Post;
  onLikeToggle?: (postId: string, isLiked: boolean) => void;
  onAddComment?: (postId: string, commentText: string) => void;
}

export default function PostCard({
  post,
  onLikeToggle,
  onAddComment,
}: PostCardProps) {
  const [isLiked, setIsLiked] = useState(post.isLiked || false);
  const [likesCount, setLikesCount] = useState(post.likesCount || 0);
  const [commentsCount, setCommentsCount] = useState(post.commentsCount || 0);
  const [comments, setComments] = useState<Comment[]>(post.comments || []);
  const [isCommentSectionOpen, setIsCommentSectionOpen] = useState(false);
  const [commentInput, setCommentInput] = useState('');

  const handleLike = () => {
    const nextIsLiked = !isLiked;
    setIsLiked(nextIsLiked);
    setLikesCount((prev) => (nextIsLiked ? prev + 1 : Math.max(0, prev - 1)));
    if (onLikeToggle) {
      onLikeToggle(post.id, nextIsLiked);
    }
  };

  const handleCommentSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentInput.trim()) return;

    const newCommentObj: Comment = {
      id: `comment-${Date.now()}`,
      author: {
        id: 'me',
        name: 'Bạn',
        avatar: '/assets/logo.png',
      },
      content: commentInput.trim(),
      createdAt: 'Vừa xong',
    };

    setComments((prev) => [...prev, newCommentObj]);
    setCommentsCount((prev) => prev + 1);
    if (onAddComment) {
      onAddComment(post.id, commentInput.trim());
    }
    setCommentInput('');
  };

  return (
    <article className="post-card-item">
      {/* 1. Post Header */}
      <div className="post-card-header">
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
            {post.author.isVerified && (
              <span className="verified-icon" title="Tài khoản HVNH đã xác thực">
                ✓
              </span>
            )}
          </div>
          <div className="post-time-privacy">
            <span className="post-time">{post.createdAt}</span>
            <span className="dot-sep">•</span>
            <span className="privacy-badge">
              {post.privacy === 'public' ? '🌐 Công khai' : '👥 Bạn bè'}
            </span>
          </div>
        </div>
      </div>

      {/* 2. Post Body Content */}
      <div className="post-card-body">
        <p className="post-text-content">{post.content}</p>

        {post.marketListing && (
          <div className="post-special-badge market-badge">
            <span>
              🛒 Pass đồ: <strong>{post.marketListing.price}</strong> — {post.marketListing.location}
            </span>
          </div>
        )}

        {post.media && post.media.length > 0 && (
          <div className={`post-media-gallery count-${post.media.length}`}>
            {post.media.map((item) => (
              <div key={item.id} className="media-item">
                <img src={item.url} alt="Nội dung bài viết" />
              </div>
            ))}
          </div>
        )}
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
              <input
                type="text"
                className="comment-input-field"
                placeholder="Viết bình luận của bạn..."
                value={commentInput}
                onChange={(e) => setCommentInput(e.target.value)}
              />
              <button
                type="submit"
                className="btn btn-primary btn-sm comment-submit-btn"
                disabled={!commentInput.trim()}
              >
                Gửi
              </button>
            </form>

            {/* Comments List Stream */}
            {comments.length > 0 ? (
              <div className="comments-stream-list">
                {comments.map((c) => (
                  <div key={c.id} className="comment-item-row">
                    <img
                      src={c.author.avatar || '/assets/logo.png'}
                      alt={c.author.name}
                      className="comment-author-avatar"
                    />
                    <div className="comment-bubble">
                      <div className="comment-author-name">{c.author.name}</div>
                      <p className="comment-text-body">{c.content}</p>
                      <span className="comment-timestamp">{c.createdAt}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-comments-yet">Chưa có bình luận nào. Hãy là người đầu tiên bình luận!</p>
            )}
          </div>
        )}
      </div>
    </article>
  );
}
