"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { fetchConversations, fetchNotifications, setNotificationRead, type ApiNotification } from "@/lib/api";
import { safeImageSrc } from "@/lib/media";
import RelativeTime from "@/components/ui/RelativeTime";
import type { Conversation } from "@/types/message";

interface Props {
  kind: "messages" | "notifications";
  onClose: () => void;
  onChat: (user: { id: string; name: string; avatar: string }) => void;
}

export default function NavbarQuickPanel({ kind, onClose, onChat }: Props) {
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [notifications, setNotifications] = useState<ApiNotification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    let mounted = true;
    const request = kind === "messages" ? fetchConversations() : fetchNotifications(12, 0, "all");
    void request.then(result => {
      if (!mounted) return;
      if (kind === "messages") setConversations(result as Conversation[]);
      else setNotifications((result as Awaited<ReturnType<typeof fetchNotifications>>).items);
    }).catch(reason => { if (mounted) setError(reason instanceof Error ? reason.message : "Không thể tải dữ liệu."); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, [kind]);

  const openNotification = async (item: ApiNotification) => {
    try { if (item.is_unread) { await setNotificationRead(item.id, true); window.dispatchEvent(new Event("notifications-changed")); } }
    catch { /* Navigation remains available when marking read fails. */ }
    const commentId = typeof item.payload?.comment_id === "string" ? item.payload.comment_id : null;
    const target = (item.type === "POST_LIKE" || item.type === "COMMENT") && item.reference_id
      ? `/home?post=${encodeURIComponent(item.reference_id)}${commentId ? `&comment=${encodeURIComponent(commentId)}` : ""}`
      : item.link;
    onClose();
    if (target?.startsWith("/")) router.push(target);
  };

  return <section className="navbar-quick-panel" aria-label={kind === "messages" ? "Tin nhắn gần đây" : "Thông báo gần đây"}>
    <header><h2>{kind === "messages" ? "Đoạn chat" : "Thông báo"}</h2><button type="button" onClick={onClose} aria-label="Đóng">×</button></header>
    <div className="navbar-quick-list">
      {loading && <p className="navbar-quick-empty">Đang tải...</p>}
      {error && <p className="navbar-quick-empty" role="alert">{error}</p>}
      {!loading && !error && kind === "messages" && (conversations.length ? conversations.slice(0, 10).map(item => <button type="button" className="navbar-quick-row" key={item.id} onClick={() => { onClose(); onChat({ id: item.participantId, name: item.participantName, avatar: item.participantAvatar }); }}><img src={safeImageSrc(item.participantAvatar)} alt="" /><span><strong>{item.participantName}</strong><small>{item.lastMessageSnippet || "Bắt đầu trò chuyện"}</small></span>{item.unreadCount > 0 && <b className="navbar-quick-dot" aria-label={`${item.unreadCount} tin chưa đọc`}/>}</button>) : <p className="navbar-quick-empty">Bạn chưa có cuộc trò chuyện nào.</p>)}
      {!loading && !error && kind === "notifications" && (notifications.length ? notifications.map(item => <button type="button" className={`navbar-quick-row ${item.is_unread ? "unread" : ""}`} key={item.id} onClick={() => void openNotification(item)}><img src={safeImageSrc(item.actor_avatar)} alt="" /><span><strong>{item.actor_name}</strong><small>{item.content}</small><RelativeTime value={item.created_at}/></span>{item.is_unread && <b className="navbar-quick-dot" aria-label="Chưa đọc"/>}</button>) : <p className="navbar-quick-empty">Bạn chưa có thông báo nào.</p>)}
    </div>
    <Link href={kind === "messages" ? "/messages" : "/notifications"} onClick={onClose} className="navbar-quick-footer">{kind === "messages" ? "Xem tất cả tin nhắn" : "Xem tất cả thông báo"}</Link>
  </section>;
}
