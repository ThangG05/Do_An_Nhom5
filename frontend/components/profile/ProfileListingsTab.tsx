"use client";

import PostCard from "@/components/post/PostCard";
import type { Post } from "@/types/post";

interface ProfileListingsTabProps {
  groupPosts: Post[];
}

export default function ProfileListingsTab({ groupPosts }: ProfileListingsTabProps) {
  return (
    <section className="profile-group-posts-tab">
      <header className="profile-group-posts-header">
        <div>
          <span className="profile-section-eyebrow">HOẠT ĐỘNG CỘNG ĐỒNG</span>
          <h2>Bài đăng hội nhóm</h2>
          <p>Các bài viết của bạn đã được duyệt trong những nhóm có quyền truy cập.</p>
        </div>
        <span className="profile-group-posts-count">{groupPosts.length} bài</span>
      </header>
      {groupPosts.length ? (
        <div className="profile-group-posts-stream">
          {groupPosts.map((post) => <PostCard key={post.id} post={post} />)}
        </div>
      ) : (
        <div className="empty-listings-card">
          <h3>Chưa có bài đăng hội nhóm</h3>
          <p>Bài viết sẽ xuất hiện ở đây sau khi quản trị viên nhóm phê duyệt.</p>
        </div>
      )}
    </section>
  );
}
