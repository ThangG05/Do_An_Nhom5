"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { IconBell, IconCheck, IconGroups, IconMessage } from "@/components/ui/Icons";

interface NotificationItem {
  id: string;
  type: "event" | "friend" | "post" | "group";
  avatar?: string;
  sender: string;
  content: string;
  time: string;
  isUnread: boolean;
  link?: string;
}

const mockNotifications: NotificationItem[] = [
  {
    id: "notif-1",
    type: "event",
    avatar: "🎓",
    sender: "CLB Chứng Khoán HVNH",
    content: "vừa đăng sự kiện mới: 'Workshop Phân Tích Kỹ Thuật 2026' tại Hội trường D.",
    time: "10 phút trước",
    isUnread: true,
    link: "/groups",
  },
  {
    id: "notif-2",
    type: "friend",
    avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&q=80",
    sender: "Lê Minh Anh",
    content: "đã gửi lời mời kết bạn cùng bạn (Sinh viên K26 Khoa Ngân hàng).",
    time: "45 phút trước",
    isUnread: true,
    link: "/profile",
  },
  {
    id: "notif-3",
    type: "post",
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=100&q=80",
    sender: "Trần Hoàng Nam",
    content: "đã bình luận về bài viết Pass giáo trình Kế toán tài chính của bạn.",
    time: "2 giờ trước",
    isUnread: false,
    link: "/groups",
  },
  {
    id: "notif-4",
    type: "group",
    avatar: "🏠",
    sender: "Nhóm Tìm Trọ & Ghép Phòng HVNH",
    content: "Bài niêm yết tìm phòng gần Chùa Bộc của bạn đã được kiểm duyệt thành công.",
    time: "5 giờ trước",
    isUnread: false,
    link: "/groups",
  },
  {
    id: "notif-5",
    type: "event",
    avatar: "⚽",
    sender: "CLB Bóng Đá HVNH",
    content: "thông báo lịch thi đấu vòng bán kết giải sinh viên BAV Cup 2026.",
    time: "1 ngày trước",
    isUnread: false,
    link: "/groups",
  },
];

export default function NotificationsPage() {
  const [checked, setChecked] = useState(false);
  const [filterTab, setFilterTab] = useState<"all" | "unread" | "friends">("all");
  const [notifs, setNotifs] = useState<NotificationItem[]>(mockNotifications);
  const router = useRouter();

  useEffect(() => {
    if (
      window.sessionStorage.getItem("hvnh-hub-mock-authenticated") !== "true"
    ) {
      router.replace("/login");
      return;
    }
    setChecked(true);
  }, [router]);

  if (!checked)
    return <main className="home-loading" aria-label="Đang tải thông báo" />;

  const handleMarkAllRead = () => {
    setNotifs((prev) => prev.map((item) => ({ ...item, isUnread: false })));
  };

  const handleToggleSingleRead = (id: string) => {
    setNotifs((prev) =>
      prev.map((item) => (item.id === id ? { ...item, isUnread: !item.isUnread } : item))
    );
  };

  const filteredNotifs = notifs.filter((item) => {
    if (filterTab === "unread") return item.isUnread;
    if (filterTab === "friends") return item.type === "friend";
    return true;
  });

  const unreadCount = notifs.filter((n) => n.isUnread).length;

  return (
    <main className="notifications-workspace-page">
      <div className="notifications-container">
        {/* Workspace Header */}
        <header className="notifications-header-card">
          <div className="notif-header-title-row">
            <div className="title-with-badge">
              <IconBell size={24} color="#0F172A" />
              <h1>Thông báo của tôi</h1>
              {unreadCount > 0 && (
                <span className="notif-unread-count-pill">{unreadCount} mới</span>
              )}
            </div>

            <button
              type="button"
              className="mark-all-read-btn"
              onClick={handleMarkAllRead}
              disabled={unreadCount === 0}
            >
              <IconCheck size={16} />
              <span>Đánh dấu tất cả đã đọc</span>
            </button>
          </div>

          {/* Sub-Filter Tabs */}
          <nav className="notif-filter-tabs" aria-label="Bộ lọc thông báo">
            <button
              type="button"
              className={`notif-tab-item ${filterTab === "all" ? "active" : ""}`}
              onClick={() => setFilterTab("all")}
            >
              Tất cả ({notifs.length})
            </button>
            <button
              type="button"
              className={`notif-tab-item ${filterTab === "unread" ? "active" : ""}`}
              onClick={() => setFilterTab("unread")}
            >
              Chưa đọc ({unreadCount})
            </button>
            <button
              type="button"
              className={`notif-tab-item ${filterTab === "friends" ? "active" : ""}`}
              onClick={() => setFilterTab("friends")}
            >
              Lời mời kết bạn
            </button>
          </nav>
        </header>

        {/* Notifications List Body */}
        <div className="notifications-list-card">
          {filteredNotifs.length === 0 ? (
            <div className="notif-empty-state">
              <div className="empty-bell-icon">
                <IconBell size={36} color="#94A3B8" />
              </div>
              <h3>Không có thông báo nào</h3>
              <p>Bạn đã xem hết tất cả thông báo trong danh mục này.</p>
            </div>
          ) : (
            filteredNotifs.map((item) => (
              <article
                key={item.id}
                className={`notif-row-item ${item.isUnread ? "unread" : ""}`}
                onClick={() => item.link && router.push(item.link)}
              >
                {/* Unread Status Dot */}
                <div className="row-status-dot-col">
                  {item.isUnread ? <span className="blue-unread-dot" /> : null}
                </div>

                {/* Avatar Icon / User Photo */}
                <div className="notif-row-avatar-wrap">
                  {item.avatar?.startsWith("http") ? (
                    <img src={item.avatar} alt={item.sender} className="notif-user-avatar-img" />
                  ) : (
                    <div className="notif-icon-badge">{item.avatar || "🔔"}</div>
                  )}
                </div>

                {/* Content Text */}
                <div className="notif-row-content">
                  <p className="notif-text-line">
                    <strong className="sender-name">{item.sender}</strong> {item.content}
                  </p>
                  <small className="notif-time-stamp">{item.time}</small>
                </div>

                {/* Action Controls */}
                <div
                  className="notif-row-actions"
                  onClick={(e) => e.stopPropagation()}
                >
                  <button
                    type="button"
                    className="single-toggle-read-btn"
                    onClick={() => handleToggleSingleRead(item.id)}
                    title={item.isUnread ? "Đánh dấu đã đọc" : "Đánh dấu chưa đọc"}
                  >
                    {item.isUnread ? "Đã đọc" : "Chưa đọc"}
                  </button>
                </div>
              </article>
            ))
          )}
        </div>
      </div>
    </main>
  );
}
