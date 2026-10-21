"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchAdminPublicPosts, moderateAdminPublicPost } from "@/lib/api";
import type { AdminPublicPostPage } from "@/types/admin";
import UserAvatar from "@/components/ui/UserAvatar";
import { useDialog } from "@/components/ui/DialogProvider";
import { safeImageSrc } from "@/lib/media";

type Status = "ALL" | "APPROVED" | "HIDDEN";
const PAGE_SIZE = 10;

export default function AdminPublicPostsPage() {
  const dialog = useDialog();
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<Status>("ALL");
  const [page, setPage] = useState(0);
  const [data, setData] = useState<AdminPublicPostPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await fetchAdminPublicPosts(search, status, page * PAGE_SIZE, PAGE_SIZE));
      setError("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không tải được bài viết công khai.");
    } finally {
      setLoading(false);
    }
  }, [search, status, page]);

  useEffect(() => { void load(); }, [load]);

  const moderate = async (postId: string, action: "HIDE" | "RESTORE") => {
    if (busy) return;
    const reason = await dialog.prompt({
      title: action === "HIDE" ? "Gỡ bài khỏi Feed công khai?" : "Khôi phục bài lên Feed?",
      message: action === "HIDE" ? "Bài sẽ không còn hiển thị cho người dùng. Ghi rõ lý do để lưu nhật ký quản trị." : "Bài sẽ hiển thị trở lại trên Feed công khai. Ghi rõ căn cứ khôi phục.",
      placeholder: "Lý do xử lý...", multiline: true, minLength: 3,
      confirmLabel: action === "HIDE" ? "Gỡ khỏi Feed" : "Khôi phục",
      tone: action === "HIDE" ? "danger" : "default",
    });
    if (!reason) return;
    setBusy(postId);
    try {
      await moderateAdminPublicPost(postId, action, reason);
      await load();
      dialog.notify({ title: action === "HIDE" ? "Đã gỡ bài khỏi Feed" : "Đã khôi phục bài viết", tone: "success" });
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : "Không xử lý được bài viết.";
      setError(message);
      dialog.notify({ title: "Xử lý thất bại", message, tone: "danger" });
    } finally {
      setBusy(null);
    }
  };

  return <main className="admin-console">
    <header className="admin-page-heading"><div><span>KIỂM DUYỆT CHỦ ĐỘNG</span><h1>Feed công khai</h1><p>Kiểm tra bài viết ngoài hội nhóm kể cả khi chưa có báo cáo. Bài trong nhóm vẫn do quản trị nhóm phụ trách.</p></div></header>
    <form className="admin-public-toolbar" onSubmit={event => { event.preventDefault(); setPage(0); setSearch(query.trim()); }}>
      <input value={query} onChange={event => setQuery(event.target.value)} placeholder="Tìm theo nội dung hoặc tác giả" aria-label="Tìm bài viết công khai" />
      <button type="submit">Tìm kiếm</button>
      <select value={status} onChange={event => { setStatus(event.target.value as Status); setPage(0); }} aria-label="Lọc trạng thái">
        <option value="ALL">Tất cả trạng thái</option><option value="APPROVED">Đang hiển thị</option><option value="HIDDEN">Đã gỡ</option>
      </select>
    </form>
    {error && <div className="admin-error" role="alert">{error}</div>}
    <div className="admin-public-summary">{loading ? "Đang tải..." : `${data?.total ?? 0} bài viết`}</div>
    <section className="admin-public-list">
      {!loading && !data?.items.length && <p className="admin-empty-state">Không có bài viết phù hợp.</p>}
      {data?.items.map(post => <article key={post.id} className="admin-public-card">
        <header><UserAvatar src={post.author.avatar} name={post.author.name} imageClassName="admin-public-avatar" fallbackClassName="admin-public-avatar admin-public-avatar-fallback" /><div><Link href={`/admin/users/${post.author.id}`}>{post.author.name}</Link><small>{new Date(post.createdAt).toLocaleString("vi-VN")} · {post.privacy === "public" ? "Công khai" : post.privacy}</small></div><span className={post.status === "HIDDEN" ? "is-hidden" : "is-visible"}>{post.status === "HIDDEN" ? "Đã gỡ" : "Đang hiển thị"}</span></header>
        <p className="admin-public-content">{post.content || "Bài viết không có nội dung chữ."}</p>
        {post.status === "HIDDEN" && post.rejectionReason && <p className="admin-public-reason"><strong>Lý do đã gỡ:</strong> {post.rejectionReason}</p>}
        {!!post.media?.length && <div className="admin-public-media">{post.media.map(media => media.type === "image" ? <img key={media.id} src={safeImageSrc(media.url)} alt={media.name || "Ảnh bài viết"} /> : media.type === "video" ? <video key={media.id} src={media.url} controls preload="metadata" /> : <a key={media.id} href={media.url} target="_blank" rel="noreferrer">{media.name || "Xem tệp đính kèm"}</a>)}</div>}
        <footer><span>{post.likesCount} lượt thích · {post.commentsCount} bình luận</span><button type="button" className={post.status === "HIDDEN" ? "restore" : "hide"} disabled={busy === post.id} onClick={() => void moderate(post.id, post.status === "HIDDEN" ? "RESTORE" : "HIDE")}>{busy === post.id ? "Đang xử lý..." : post.status === "HIDDEN" ? "Khôi phục bài" : "Gỡ khỏi Feed"}</button></footer>
      </article>)}
    </section>
    {!!data?.total && data.total > PAGE_SIZE && <nav className="admin-public-pagination" aria-label="Phân trang bài viết"><button type="button" disabled={page === 0 || loading} onClick={() => setPage(value => value - 1)}>Trang trước</button><span>Trang {page + 1} / {Math.ceil(data.total / PAGE_SIZE)}</span><button type="button" disabled={(page + 1) * PAGE_SIZE >= data.total || loading} onClick={() => setPage(value => value + 1)}>Trang sau</button></nav>}
  </main>;
}
