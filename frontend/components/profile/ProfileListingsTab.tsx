"use client";

import PostCard from "@/components/post/PostCard";
import type { Post } from "@/types/post";
import PostPagination, { type PostPaginationProps } from '@/components/ui/PostPagination';

interface ProfileListingsTabProps {
  groupPosts: Post[];
  pagination: PostPaginationProps;
}

export default function ProfileListingsTab({ groupPosts, pagination }: ProfileListingsTabProps) {
  return (
    <section className="profile-group-posts-tab">
      <header className="profile-group-posts-header">
        <div>
          <span className="profile-section-eyebrow">HOẠT ĐỘNG CỘNG ĐỒNG</span>
          <h2>Bài đăng hội nhóm</h2>
          <p>Các bài viết của bạn đã được duyệt trong những nhóm có quyền truy cập.</p>
        </div>
        <span className="profile-group-posts-count">{groupPosts.length} bài trên trang</span>
      </header>
      {groupPosts.length ? (
        <div className="profile-group-posts-stream">
          {groupPosts.map((post) => <PostCard key={post.id} post={post} />)}
        </div>
      ) : pagination.loading || pagination.error ? null : (
        <div className="empty-listings-card">
          <h3>Chưa có bài đăng hội nhóm</h3>
          <p>Bài viết sẽ xuất hiện ở đây sau khi quản trị viên nhóm phê duyệt.</p>
        </div>
      )}
      <PostPagination {...pagination} />
    </section>
  );
}
