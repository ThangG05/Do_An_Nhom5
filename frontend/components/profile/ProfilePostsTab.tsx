"use client";

import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Post, CreatePostPayload } from '@/types/post';
import { UserProfile } from '@/types/user';
import CreatePostCard from '@/components/post/CreatePostCard';
import CreatePostModal from '@/components/post/CreatePostModal';
import PostCard from '@/components/post/PostCard';
import { useCreatePost } from '@/hooks/useCreatePost';
import PostPagination, { type PostPaginationProps } from '@/components/ui/PostPagination';
import { fetchPost } from '@/lib/api';

interface ProfilePostsTabProps {
  profile: UserProfile;
  posts: Post[];
  pagination: PostPaginationProps;
  isOwnProfile: boolean;
  postFilter: string;
  onFilterChange: (filter: string) => void;
  onCreatePost: (payload: CreatePostPayload) => Promise<Post | null>;
}

export default function ProfilePostsTab({
  profile,
  posts,
  pagination,
  isOwnProfile,
  postFilter,
  onFilterChange,
  onCreatePost,
}: ProfilePostsTabProps) {
  const createPostState = useCreatePost(onCreatePost);
  const focusedPostId = useSearchParams().get('post');
  const [focusedPost, setFocusedPost] = useState<Post | null>(null);
  const [focusError, setFocusError] = useState('');

  useEffect(() => {
    let active = true;
    setFocusedPost(null);
    setFocusError('');
    if (focusedPostId) {
      void fetchPost(focusedPostId).then(result => {
        if (!active) return;
        if (result.author.id !== profile.id || result.groupId) {
          setFocusError('Bài viết không thuộc trang cá nhân này.');
        } else {
          setFocusedPost(result);
        }
      }).catch(() => { if (active) setFocusError('Bài viết không khả dụng hoặc bạn không có quyền xem.'); });
    }
    return () => { active = false; };
  }, [focusedPostId, profile.id]);

  useEffect(() => {
    if (!focusedPost) return;
    const timer = window.setTimeout(() => document.getElementById(`post-${focusedPost.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 80);
    return () => window.clearTimeout(timer);
  }, [focusedPost]);

  const filteredPosts = posts.filter((p) => {
    if (postFilter === 'market') return p.category === 'market';
    if (postFilter === 'roommate') return p.category === 'roommate';
    if (postFilter === 'event') return p.category === 'event';
    return true;
  });

  const visiblePosts = focusedPost && !filteredPosts.some(post => post.id === focusedPost.id)
    ? [focusedPost, ...filteredPosts]
    : filteredPosts;

  return (
    <div className="profile-posts-tab-content">
      {isOwnProfile && (
        <div className="in-profile-create-post-wrapper">
          <CreatePostCard
            onOpenModal={createPostState.openModal}
            userAvatar={profile.avatar}
            userName={profile.name}
          />
        </div>
      )}

      <div className="feed-filters-bar-card">
        <div className="profile-feed-heading">
          <h2 className="feed-section-title">Bài viết</h2>
          <span className="profile-feed-count">{filteredPosts.length} bài trên trang</span>
        </div>
        <div className="filter-chips-row" role="group" aria-label="Lọc bài viết theo danh mục">
          <button
            type="button"
            className={`filter-chip ${postFilter === 'all' ? 'active' : ''}`}
            onClick={() => onFilterChange('all')}
            aria-pressed={postFilter === 'all'}
          >
            Tất cả
          </button>
          <button
            type="button"
            className={`filter-chip ${postFilter === 'market' ? 'active' : ''}`}
            onClick={() => onFilterChange('market')}
            aria-pressed={postFilter === 'market'}
          >
            Pass đồ
          </button>
          <button
            type="button"
            className={`filter-chip ${postFilter === 'roommate' ? 'active' : ''}`}
            onClick={() => onFilterChange('roommate')}
            aria-pressed={postFilter === 'roommate'}
          >
            Ghép phòng
          </button>
          <button
            type="button"
            className={`filter-chip ${postFilter === 'event' ? 'active' : ''}`}
            onClick={() => onFilterChange('event')}
            aria-pressed={postFilter === 'event'}
          >
            Sự kiện
          </button>
        </div>
      </div>

      {focusError && <p role="alert" className="profile-post-focus-error">{focusError}</p>}
      {visiblePosts.length > 0 ? (
        <div className="posts-stream-container list-layout">
          {visiblePosts.map((post) => (
            <div id={`post-${post.id}`} key={post.id} className={post.id === focusedPostId ? 'notification-target-post' : undefined}>
              <PostCard post={post} />
            </div>
          ))}
        </div>
      ) : pagination.loading || pagination.error ? null : (
        <div className="empty-feed-card">
          <div className="empty-feed-icon" aria-hidden="true">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M8 4h8a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z" />
              <path d="M9 9h6M9 13h6M9 17h4" />
            </svg>
          </div>
          <h3 className="empty-feed-title">
            {postFilter === 'all' ? 'Chưa có bài viết nào' : 'Chưa có bài viết trong mục này'}
          </h3>
          <p className="empty-feed-desc">
            {postFilter !== 'all'
              ? 'Thử chọn danh mục khác để xem những bài đã đăng.'
              : isOwnProfile
              ? 'Chia sẻ một khoảnh khắc hoặc điều thú vị với bạn bè HVNH.'
              : 'Chưa có bài viết nào được chia sẻ với bạn.'}
          </p>
        </div>
      )}

      <PostPagination {...pagination} />
      {/* Create Post Modal Integration */}
      {createPostState.isOpen && (
        <CreatePostModal postState={createPostState} />
      )}
    </div>
  );
}
