"use client";

import { useEffect, useState } from "react";
import { fetchAdminDashboard } from "@/lib/api";
import type { AdminDashboard } from "@/types/admin";

export default function AdminOverviewPage() {
  const [dashboard, setDashboard] = useState<AdminDashboard | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchAdminDashboard().then(setDashboard).catch(cause =>
      setError(cause instanceof Error ? cause.message : "Không tải được tổng quan."));
  }, []);

  const cards = dashboard ? [
    ["Người dùng", dashboard.total_users],
    ["Đang hoạt động", dashboard.active_users],
    ["Bị khóa", dashboard.locked_users],
    ["Bài chờ duyệt", dashboard.pending_posts],
    ["Bài đã duyệt", dashboard.approved_posts],
    ["Tin nhắn", dashboard.total_messages],
  ] as const : [];

  return <main className="admin-console">
    <header className="admin-page-heading"><div><span>DASHBOARD</span><h1>Tổng quan hệ thống</h1><p>Các chỉ số vận hành mới nhất. Chọn chức năng từ thanh điều hướng bên trái.</p></div></header>
    {error && <div className="admin-error" role="alert">{error}</div>}
    <section className="admin-metric-grid admin-overview-metrics">{cards.map(([label, value]) => <article key={label}><small>{label}</small><strong>{value}</strong></article>)}</section>
  </main>;
}
