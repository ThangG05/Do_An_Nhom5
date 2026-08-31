"use client";

import React from 'react';
import { Post, CreatePostPayload } from '@/types/post';
import { UserProfile } from '@/types/user';
import CreatePostCard from '@/components/post/CreatePostCard';
import CreatePostModal from '@/components/post/CreatePostModal';
import PostCard from '@/components/post/PostCard';
import { useCreatePost } from '@/hooks/useCreatePost';

interface ProfilePostsTabProps {
  profile: UserProfile;
  posts: Post[];
  isOwnProfile: boolean;
  postFilter: string;
  postViewMode: 'list' | 'grid';
  onFilterChange: (filter: string) => void;
  onViewModeChange: (mode: 'list' | 'grid') => void;
  onCreatePost: (payload: CreatePostPayload) => Promise<Post | null>;
}

export default function ProfilePostsTab({
  profile,
  posts,
  isOwnProfile,
  postFilter,
  postViewMode,
  onFilterChange,
  onViewModeChange,
  onCreatePost,
}: ProfilePostsTabProps) {
  const createPostState = useCreatePost((newPost: Post) => {
    onCreatePost({
      content: newPost.content,
      category: newPost.category,
      privacy: newPost.privacy,
      media: newPost.media || [],
      taggedFriends: [],
    });
  });

  const filteredPosts = posts.filter((p) => {
    if (postFilter === 'market') return p.category === 'market';
    if (postFilter === 'roommate') return p.category === 'roommate';
    if (postFilter === 'event') return p.category === 'event';
    return true;
  });

  return (
    <div className="profile-posts-tab-content">
      {/* 1. Feed Filters & Management Bar */}
      <div className="feed-filters-bar-card">
        <div className="filters-left-group">
          <h2 className="feed-section-title">Bài viết</h2>
          <div className="filter-chips-row">
            <button
              type="button"
              className={`filter-chip ${postFilter === 'all' ? 'active' : ''}`}
              onClick={() => onFilterChange('all')}
            >
              Tất cả bài viết
            </button>
            <button
              type="button"
              className={`filter-chip ${postFilter === 'market' ? 'active' : ''}`}
              onClick={() => onFilterChange('market')}
            >
              Pass đồ
            </button>
            <button
              type="button"
              className={`filter-chip ${postFilter === 'roommate' ? 'active' : ''}`}
              onClick={() => onFilterChange('roommate')}
            >
              Ghép phòng
            </button>
          </div>
        </div>

        <div className="filters-right-group">
          {isOwnProfile && (
            <button type="button" className="btn btn-secondary btn-sm btn-has-icon">
              ⚙️ Quản lý bài viết
            </button>
          )}

          <div className="view-mode-toggle-group">
            <button
              type="button"
              className={`toggle-btn ${postViewMode === 'list' ? 'active' : ''}`}
              onClick={() => onViewModeChange('list')}
              title="Chế độ danh sách"
            >
              ☰
            </button>
            <button
              type="button"
              className={`toggle-btn ${postViewMode === 'grid' ? 'active' : ''}`}
              onClick={() => onViewModeChange('grid')}
              title="Chế độ lưới"
            >
              ▦
            </button>
          </div>
        </div>
      </div>

      {/* 2. In-Profile Create Post Card (Own Profile only) */}
      {isOwnProfile && (
        <div className="in-profile-create-post-wrapper">
          <CreatePostCard
            onOpenModal={createPostState.openModal}
            userAvatar={profile.avatar}
            userName={profile.name}
          />
        </div>
      )}

      {/* 3. Chronological Post Stream */}
      {filteredPosts.length > 0 ? (
        <div className={`posts-stream-container ${postViewMode === 'grid' ? 'grid-layout' : 'list-layout'}`}>
          {filteredPosts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      ) : (
        /* 4. Empty State */
        <div className="empty-feed-card">
          <div className="empty-feed-icon">📝</div>
          <h3 className="empty-feed-title">Chưa có bài viết nào</h3>
          <p className="empty-feed-desc">
            {isOwnProfile
              ? 'Hãy chia sẻ suy nghĩ, thông tin học tập hoặc bài niêm yết đầu tiên của bạn!'
              : 'Người dùng này chưa đăng bài viết nào.'}
          </p>
        </div>
      )}

      {/* Create Post Modal Integration */}
      {createPostState.isOpen && (
        <CreatePostModal postState={createPostState} />
      )}
    </div>
  );
}
