"use client";

import { useEffect, useState } from "react";
import { fetchAdminDashboard } from "@/lib/api";
import type { AdminDashboard } from "@/types/admin";
import DashboardCharts from "@/components/admin/DashboardCharts";
import "./overview.css";

const formatNumber = (value: number) => new Intl.NumberFormat("vi-VN").format(value);
const MAIN_GROUP_SLUGS = new Set(["pass-do", "ghep-phong-tim-tro", "su-kien", "hoc-tap"]);

function AccountChart({ dashboard }: { dashboard: AdminDashboard }) {
  const total = dashboard.total_users;
  const pending = Math.max(0, total - dashboard.active_users - dashboard.locked_users - dashboard.disabled_users);
  const segments = [
    { label: "Hoạt động", value: dashboard.active_users, color: "#147d68" },
    { label: "Chờ kích hoạt", value: pending, color: "#e9a433" },
    { label: "Bị khóa", value: dashboard.locked_users, color: "#e0646b" },
    { label: "Vô hiệu hóa", value: dashboard.disabled_users, color: "#8795ab" },
  ];
  let cursor = 0;
  const stops = segments.map(({ value, color }) => {
    const start = cursor;
    cursor += total > 0 ? value / total * 100 : 0;
    return `${color} ${start}% ${cursor}%`;
  });

  return <section className="admin-overview-panel" aria-label="Cơ cấu trạng thái tài khoản">
    <div className="admin-overview-panel-heading"><span>TÀI KHOẢN</span><h2>Trạng thái người dùng</h2><p>Phân bố trên {formatNumber(total)} tài khoản hiện có</p></div>
    <div className="admin-account-chart-content">
      <div className="admin-account-donut" style={{ background: total ? `conic-gradient(${stops.join(", ")})` : "#e6edf4" }} role="img" aria-label={segments.map(item => `${item.label}: ${formatNumber(item.value)}`).join(", ")}>
        <div><strong>{formatNumber(total)}</strong><small>tài khoản</small></div>
      </div>
      <ul className="admin-chart-breakdown">{segments.map(item => <li key={item.label}><span><i style={{ backgroundColor: item.color }} />{item.label}</span><strong>{formatNumber(item.value)}</strong></li>)}</ul>
    </div>
  </section>;
}

function GroupChart({ dashboard }: { dashboard: AdminDashboard }) {
  const groups = dashboard.groups.filter(group => MAIN_GROUP_SLUGS.has(group.slug));
  const max = Math.max(1, ...groups.map(group => group.members));
  return <section className="admin-overview-panel" aria-label="Thành viên theo nhóm">
    <div className="admin-overview-panel-heading"><span>HỘI NHÓM</span><h2>Quy mô cộng đồng</h2><p>Số thành viên ở từng nhóm đang hoạt động</p></div>
    <div className="admin-group-chart">
      {groups.length ? groups.map(group => <div className="admin-group-chart-row" key={group.id}>
        <div><strong>{group.name}</strong><span>{formatNumber(group.members)} thành viên</span></div>
        <div className="admin-group-chart-track" role="meter" aria-label={`${group.name}: ${group.members} thành viên`} aria-valuemin={0} aria-valuemax={max} aria-valuenow={group.members}>
          <span style={{ width: `${group.members / max * 100}%` }} />
        </div>
      </div>) : <p className="admin-overview-empty">Chưa có nhóm đang hoạt động.</p>}
    </div>
  </section>;
}

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
    ["Bài chờ duyệt", dashboard.pending_posts],
    ["Bài đã duyệt", dashboard.approved_posts],
    ["Bình luận", dashboard.total_comments],
    ["Tin nhắn", dashboard.total_messages],
  ] as const : [];

  return <main className="admin-console admin-overview-page">
    <header className="admin-page-heading"><div><span>HVNH HUB · SUPER ADMIN</span><h1>Tổng quan hệ thống</h1><p>Theo dõi người dùng và hoạt động cộng đồng qua số liệu trực quan.</p></div></header>
    {error && <div className="admin-error" role="alert">{error}</div>}
    {!dashboard && !error && <p className="admin-loading" role="status">Đang tải dữ liệu tổng quan...</p>}
    {dashboard && <>
      <section className="admin-metric-grid admin-overview-metrics" aria-label="Chỉ số chính">{cards.map(([label, value]) => <article key={label}><small>{label}</small><strong>{formatNumber(value)}</strong></article>)}</section>
      <DashboardCharts dashboard={dashboard} />
      <div className="admin-overview-panels"><AccountChart dashboard={dashboard} /><GroupChart dashboard={dashboard} /></div>
    </>}
  </main>;
}
