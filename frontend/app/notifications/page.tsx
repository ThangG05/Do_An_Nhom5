"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { IconBell, IconCheck } from "@/components/ui/Icons";
import { ApiNotification, fetchNotifications, markAllNotificationsRead, removeNotification, setNotificationRead } from "@/lib/api";
import { safeImageSrc } from "@/lib/media";
import RelativeTime from "@/components/ui/RelativeTime";

type Filter = "all" | "unread" | "friends";

const notifyBadgeChanged = () => window.dispatchEvent(new Event('notifications-changed'));

function iconFor(type: ApiNotification["type"]): string {
  if (type === "FRIEND_REQUEST") return "👥";
  if (type === "POST_LIKE") return "❤️";
  if (type === "COMMENT") return "💬";
  if (type === "MESSAGE") return "✉️";
  return "🔔";
}

export default function NotificationsPage() {
  const [filter, setFilter] = useState<Filter>("all");
  const [items, setItems] = useState<ApiNotification[]>([]);
  const [total, setTotal] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const router = useRouter();

  const load = useCallback(async (offset = 0) => {
    setLoading(true);
    setError("");
    try {
      const page = await fetchNotifications(30, offset, filter);
      setItems((previous) => offset === 0 ? page.items : [...previous, ...page.items]);
      setTotal(page.total);
      setUnreadCount(page.unread_count);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tải thông báo.");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => { void load(); }, [load]);

  const openNotification = async (item: ApiNotification) => {
    if (item.is_unread) {
      await setNotificationRead(item.id, true);
      setItems((previous) => previous.map((value) => value.id === item.id ? { ...value, is_unread: false } : value));
      setUnreadCount((value) => Math.max(0, value - 1));
      notifyBadgeChanged();
    }
    if (item.link) router.push(item.link);
  };

  const markAll = async () => {
    await markAllNotificationsRead();
    setItems((previous) => previous.map((item) => ({ ...item, is_unread: false })));
    setUnreadCount(0);
    notifyBadgeChanged();
  };

  const toggleRead = async (item: ApiNotification) => {
    const updated = await setNotificationRead(item.id, item.is_unread);
    setItems((previous) => previous.map((value) => value.id === item.id ? updated : value));
    setUnreadCount((value) => Math.max(0, value + (item.is_unread ? -1 : 1)));
    notifyBadgeChanged();
  };

  const remove = async (id: string) => {
    const removed = items.find((item) => item.id === id);
    await removeNotification(id);
    setItems((previous) => previous.filter((item) => item.id !== id));
    setTotal((value) => Math.max(0, value - 1));
    if (removed?.is_unread) setUnreadCount((value) => Math.max(0, value - 1));
    notifyBadgeChanged();
  };

  return (
    <main className="notifications-workspace-page">
      <div className="notifications-container">
        <header className="notifications-header-card">
          <div className="notif-header-title-row">
            <div className="title-with-badge"><IconBell size={24} color="#0F172A" /><h1>Thông báo của tôi</h1>{unreadCount > 0 && <span className="notif-unread-count-pill">{unreadCount} mới</span>}</div>
            <button type="button" className="mark-all-read-btn" onClick={() => void markAll()} disabled={unreadCount === 0}><IconCheck size={16} /><span>Đánh dấu tất cả đã đọc</span></button>
          </div>
          <nav className="notif-filter-tabs" aria-label="Bộ lọc thông báo">
            {([['all', 'Tất cả'], ['unread', 'Chưa đọc'], ['friends', 'Lời mời kết bạn']] as const).map(([value, label]) => <button key={value} type="button" className={`notif-tab-item ${filter === value ? 'active' : ''}`} onClick={() => setFilter(value)}>{label}{value === 'unread' ? ` (${unreadCount})` : value === 'all' ? ` (${total})` : ''}</button>)}
          </nav>
        </header>

        <div className="notifications-list-card">
          {error && <div className="notif-empty-state"><h3>Không thể tải thông báo</h3><p>{error}</p><button className="btn btn-primary" onClick={() => void load()}>Thử lại</button></div>}
          {!error && !loading && items.length === 0 && <div className="notif-empty-state"><div className="empty-bell-icon"><IconBell size={36} color="#94A3B8" /></div><h3>Không có thông báo nào</h3><p>Bạn đã xem hết thông báo trong danh mục này.</p></div>}
          {items.map((item) => (
            <article key={item.id} className={`notif-row-item ${item.is_unread ? 'unread' : ''}`} onClick={() => void openNotification(item)}>
              <div className="row-status-dot-col">{item.is_unread && <span className="blue-unread-dot" />}</div>
              <div className="notif-row-avatar-wrap">{item.actor_avatar ? <img src={safeImageSrc(item.actor_avatar)} alt={item.actor_name} className="notif-user-avatar-img" /> : <div className="notif-icon-badge">{iconFor(item.type)}</div>}</div>
              <div className="notif-row-content"><p className="notif-text-line"><strong className="sender-name">{item.actor_name}</strong> {item.content}</p><RelativeTime className="notif-time-stamp" value={item.created_at}/></div>
              <div className="notif-row-actions" onClick={(event) => event.stopPropagation()}>
                <button type="button" className="single-toggle-read-btn" onClick={() => void toggleRead(item)}>{item.is_unread ? 'Đã đọc' : 'Chưa đọc'}</button>
                <button type="button" className="single-toggle-read-btn" onClick={() => void remove(item.id)}>Xóa</button>
              </div>
            </article>
          ))}
          {!loading && items.length < total && <button type="button" className="btn btn-secondary btn-block" onClick={() => void load(items.length)}>Tải thêm</button>}
          {loading && <div className="notif-empty-state"><p>Đang tải thông báo...</p></div>}
        </div>
      </div>
    </main>
  );
}
