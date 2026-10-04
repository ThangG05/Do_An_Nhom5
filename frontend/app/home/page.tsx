"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import CreatePostCard from "@/components/post/CreatePostCard";
import CreatePostModal from "@/components/post/CreatePostModal";
import PostCard from "@/components/post/PostCard";
import { useCreatePost } from "@/hooks/useCreatePost";
import type { Post, PostCategory } from "@/types/post";
import { getAuthUser, type AuthUser } from "@/lib/auth";
import { createProfilePost, fetchFeedPage, fetchPost } from "@/lib/api";
import AIPet from "@/components/ai/AIPet";

const PAGE_SIZE = 10;
const filters: { value: "" | PostCategory; label: string }[] = [
  { value: "", label: "Tất cả" }, { value: "general", label: "Bài chung" }, { value: "market", label: "Pass đồ" },
  { value: "roommate", label: "Phòng trọ" }, { value: "event", label: "Sự kiện" }, { value: "study", label: "Học tập" },
];
function FeedSkeleton() { return <div className="feed-skeleton" aria-hidden="true"><div className="skeleton-head"><i /><div><b /><span /></div></div><p /><p /><div className="skeleton-media" /></div>; }

export default function HomePage() {
  const searchParams = useSearchParams();
  const highlightedPostId = searchParams.get("post");
  const highlightedCommentId = searchParams.get("comment");
  const [posts, setPosts] = useState<Post[]>([]), [authUser, setAuthUser] = useState<AuthUser | null>(null), [loading, setLoading] = useState(false), [hasMore, setHasMore] = useState(true), [feedError, setFeedError] = useState(""), [category, setCategory] = useState<"" | PostCategory>("");
  const cursorRef = useRef<string | null>(null), sentinelRef = useRef<HTMLDivElement | null>(null), loadingRef = useRef(false);
  const loadMore = useCallback(async (reset = false) => { if (loadingRef.current || (!reset && !hasMore)) return; loadingRef.current = true; setLoading(true); try { const page = await fetchFeedPage(PAGE_SIZE, reset ? "" : (cursorRef.current || ""), category); const target = reset && highlightedPostId ? await fetchPost(highlightedPostId).catch(() => null) : null; setPosts(previous => { const incoming = target ? [target, ...page.items.filter(item => item.id !== target.id)] : page.items; return reset ? incoming : [...previous, ...incoming.filter(item => !previous.some(current => current.id === item.id))]; }); cursorRef.current = page.nextCursor; setHasMore(Boolean(page.nextCursor)); setFeedError(""); } catch (error) { setFeedError(error instanceof Error ? error.message : "Không thể tải bảng tin."); } finally { loadingRef.current = false; setLoading(false); } }, [hasMore, category, highlightedPostId]);
  useEffect(() => setAuthUser(getAuthUser()), []);
  useEffect(() => { cursorRef.current = null; setHasMore(true); setPosts([]); void loadMore(true); }, [category, highlightedPostId]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (!highlightedPostId || !posts.some(post => post.id === highlightedPostId)) return; const timer = window.setTimeout(() => document.getElementById(`post-${highlightedPostId}`)?.scrollIntoView({ behavior: "smooth", block: "center" }), 80); return () => window.clearTimeout(timer); }, [highlightedPostId, posts]);
  useEffect(() => { const target = sentinelRef.current; if (!target) return; const observer = new IntersectionObserver(entries => { if (entries[0]?.isIntersecting) void loadMore(); }, { rootMargin: "500px 0px" }); observer.observe(target); return () => observer.disconnect(); }, [loadMore]);
  const handlePostCreated = async (payload: Parameters<typeof createProfilePost>[0]) => { const created = await createProfilePost(payload); if (!category || created.category === category) setPosts(previous => [created, ...previous]); return created; };
  const createPostState = useCreatePost(handlePostCreated);
  return <main className="home-page-single-column">
    <section className="home-welcome"><p>CỘNG ĐỒNG HVNH</p><h1>Chào mừng trở lại{authUser?.full_name ? `, ${authUser.full_name}` : ""}</h1><span>Cập nhật bài đăng, hoạt động và thông tin mới nhất trong cộng đồng.</span></section>
    <div className="home-layout">
      <aside className="home-left-rail" aria-label="Lối tắt"><Link href="/profile" className="home-user-shortcut"><img src={authUser?.avatar_url || "/assets/logo.png"} alt="" /><span><b>{authUser?.full_name || "Sinh viên HVNH"}</b><small>Trang cá nhân</small></span></Link><nav className="home-shortcut-list"><Link href="/profile"><i>👤</i><span>Trang cá nhân</span></Link><Link href="/groups"><i>👥</i><span>Hội nhóm</span></Link><Link href="/messages"><i>💬</i><span>Tin nhắn</span></Link><Link href="/assistant"><i>✦</i><span>Trợ lý AI</span></Link><Link href="/notifications"><i>🔔</i><span>Thông báo</span></Link></nav><p className="home-left-note">HVNH Hub · Cộng đồng sinh viên</p></aside>
      <section className="home-feed" aria-label="Bài viết mới"><CreatePostCard onOpenModal={createPostState.openModal} userAvatar={authUser?.avatar_url || undefined} userName={authUser?.full_name || undefined} /><div className="feed-filter-bar" role="tablist" aria-label="Lọc bảng tin">{filters.map(item => <button type="button" role="tab" aria-selected={category === item.value} className={category === item.value ? "active" : ""} key={item.value || "all"} onClick={() => setCategory(item.value)}>{item.label}</button>)}</div>{loading && !posts.length ? <><FeedSkeleton /><FeedSkeleton /><FeedSkeleton /></> : posts.map(post => <div id={`post-${post.id}`} key={post.id} className={post.id === highlightedPostId ? "notification-target-post" : ""}><PostCard post={post} highlightCommentId={post.id === highlightedPostId ? highlightedCommentId : null} /></div>)}<div ref={sentinelRef} className="feed-load-sentinel" aria-live="polite">{loading && posts.length > 0 && <span><i />Đang tải thêm bài viết...</span>}{feedError && <><p>{feedError}</p><button type="button" className="btn btn-secondary" onClick={() => void loadMore()}>Thử lại</button></>}{!loading && !feedError && !hasMore && posts.length > 0 && <small>Bạn đã xem hết bài viết.</small>}{!loading && !feedError && !posts.length && <small>Chưa có bài viết trong chuyên mục này.</small>}</div></section>
      <aside className="home-side-panel"><section className="home-side-card"><div className="home-side-heading"><i className="home-side-icon">👥</i><h2>Khám phá cộng đồng</h2></div><p>Tham gia Pass đồ, Phòng trọ, Sự kiện và Học tập để không bỏ lỡ thông tin phù hợp.</p><Link href="/groups" className="btn btn-primary btn-block">Xem các nhóm</Link></section><section className="home-side-card home-quick-links"><h3>Lối tắt nhanh</h3><Link href="/groups">Pass đồ <span>›</span></Link><Link href="/groups">Tìm trọ / Ghép phòng <span>›</span></Link><Link href="/groups">Sự kiện sinh viên <span>›</span></Link></section><section className="home-side-tip"><strong>✦ Mẹo cho bạn</strong><p>Hãy chọn đúng chuyên mục khi đăng để bài viết dễ được tìm thấy hơn.</p></section></aside>
    </div><CreatePostModal postState={createPostState} /><AIPet userName={authUser?.full_name} />
  </main>;
}
