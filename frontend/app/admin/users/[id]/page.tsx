"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { fetchAdminProfile, fetchAdminPublicPosts } from "@/lib/api";
import type { AdminProfilePreview } from "@/types/admin";
import type { Post } from "@/types/post";
import UserAvatar from "@/components/ui/UserAvatar";
import { safeImageSrc } from "@/lib/media";

export default function AdminUserProfilePage() {
  const { id } = useParams<{ id: string }>();
  const [profile, setProfile] = useState<AdminProfilePreview | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    Promise.all([fetchAdminProfile(id), fetchAdminPublicPosts("", "APPROVED", 0, 5, id).catch(() => ({ items: [] as Post[] }))])
      .then(([value, feed]) => { if (active) { setProfile(value); setPosts(feed.items); } })
      .catch(cause => { if (active) setError(cause instanceof Error ? cause.message : "Không tải được hồ sơ."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [id]);

  return <main className="admin-console">
    <header className="admin-page-heading"><div><span>HỒ SƠ TÀI KHOẢN</span><h1>Xem trang cá nhân</h1><p>Thông tin chỉ đọc dành cho Super Admin; không thực hiện tương tác như người dùng.</p></div><Link href="/admin/reports">← Báo cáo vi phạm</Link></header>
    {loading && <div className="admin-empty-state">Đang tải hồ sơ...</div>}
    {error && <div className="admin-error" role="alert">{error}</div>}
    {profile && <section className="admin-profile-preview">
      <div className="admin-profile-cover" style={profile.cover ? { backgroundImage: `url("${safeImageSrc(profile.cover)}")` } : undefined} />
      <div className="admin-profile-summary"><UserAvatar src={profile.avatar} name={profile.name} imageClassName="admin-profile-avatar" fallbackClassName="admin-profile-avatar admin-profile-avatar-fallback" /><div><h2>{profile.name}</h2><p>@{profile.username}{profile.student_code ? ` · ${profile.student_code}` : ""}</p><span className="admin-profile-status">{profile.status}</span></div></div>
      <dl className="admin-profile-facts"><div><dt>Khoa</dt><dd>{profile.faculty || "Chưa cập nhật"}</dd></div><div><dt>Tham gia</dt><dd>{new Date(profile.joined_at).toLocaleDateString("vi-VN")}</dd></div><div><dt>Giới thiệu</dt><dd>{profile.bio || "Chưa có giới thiệu"}</dd></div></dl>
      <div className="admin-profile-posts"><h3>Bài viết công khai gần đây</h3>{posts.length ? posts.map(post => <article key={post.id}><small>{new Date(post.createdAt).toLocaleString("vi-VN")}</small><p>{post.content || "Bài viết có tệp đính kèm"}</p>{post.media?.filter(media => media.type === "image").slice(0, 3).map(media => <img key={media.id} src={safeImageSrc(media.url)} alt={media.name || "Ảnh bài viết"} />)}</article>) : <p>Chưa có bài viết công khai.</p>}</div>
    </section>}
  </main>;
}
