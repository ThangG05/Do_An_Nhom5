"use client";

import Link from "next/link";
import UserAvatar from "@/components/ui/UserAvatar";
import RelativeTime from "@/components/ui/RelativeTime";
import {safeImageSrc} from "@/lib/media";
import type {GroupPost} from "@/types/group-api";
import PostCategoryDetails from "@/components/post/PostCategoryDetails";

const categoryLabels: Record<string, string> = {
  general: "Bài viết",
  market: "Pass đồ",
  roommate: "Ghép phòng",
  event: "Sự kiện",
  study: "Học tập",
};

export default function PendingGroupPostCard({post, groupName, busy, onApprove, onReject}: {
  post: GroupPost;
  groupName: string;
  busy: boolean;
  onApprove: () => void;
  onReject: () => void;
}) {
  const visuals = (post.media || []).filter(item => item.type === "image" || item.type === "video");
  const attachments = (post.media || []).filter(item => item.type === "audio" || item.type === "file");

  return <article className="pending-group-post" aria-label={`Bài chờ duyệt của ${post.author.name}`}>
    <header className="pending-group-post-header">
      <Link href={`/profile/${post.author.id}`} className="pending-group-post-avatar-link" aria-label={`Xem trang cá nhân ${post.author.name}`}>
        <UserAvatar src={post.author.avatar} name={post.author.name} imageClassName="pending-group-post-avatar" fallbackClassName="pending-group-post-avatar pending-group-post-avatar-fallback" />
      </Link>
      <div className="pending-group-post-author">
        <div className="pending-group-post-author-line"><Link href={`/profile/${post.author.id}`}>{post.author.name}</Link><span aria-hidden="true">›</span><strong>{post.groupName || groupName}</strong></div>
        <div className="pending-group-post-meta"><RelativeTime value={post.createdAt} /><span aria-hidden="true">·</span><span>{categoryLabels[post.category] || "Bài viết"}</span></div>
      </div>
      <span className="pending-group-post-status">Chờ duyệt</span>
    </header>

    <div className="pending-group-post-body">
      <PostCategoryDetails post={post} />
      {post.content && <p className="pending-group-post-text">{post.content}</p>}
      {post.location?.name && <p className="pending-group-post-location">📍 {post.location.name}</p>}
      {!!visuals.length && <div className={`pending-group-post-media ${visuals.length === 1 ? "single" : "multiple"}`}>
        {visuals.map(item => item.type === "image"
          ? <img key={item.id} src={safeImageSrc(item.url)} alt={item.name || "Ảnh đính kèm bài viết"} />
          : <video key={item.id} src={item.url} controls preload="metadata" aria-label={item.name || "Video đính kèm bài viết"} />)}
      </div>}
      {!!attachments.length && <div className="pending-group-post-attachments">{attachments.map(item => item.type === "audio"
        ? <div key={item.id} className="pending-group-post-attachment"><span aria-hidden="true">♫</span><div><strong>{item.name || "Âm thanh"}</strong><audio src={item.url} controls preload="metadata" /></div></div>
        : <a key={item.id} className="pending-group-post-attachment" href={item.url} target="_blank" rel="noreferrer"><span aria-hidden="true">↗</span><strong>{item.name || "Tệp đính kèm"}</strong></a>)}</div>}
      {!post.content && !post.marketListing?.productName && !visuals.length && !attachments.length && <p className="pending-group-post-text pending-group-post-empty">Bài viết không có nội dung hiển thị.</p>}
    </div>

    <footer className="pending-group-post-footer">
      <span>Bài viết chỉ hiển thị với thành viên sau khi được phê duyệt.</span>
      <div><button type="button" className="pending-group-post-reject" disabled={busy} onClick={onReject}>Từ chối</button><button type="button" className="pending-group-post-approve" disabled={busy} onClick={onApprove}>{busy ? "Đang xử lý..." : "Phê duyệt"}</button></div>
    </footer>
  </article>;
}
