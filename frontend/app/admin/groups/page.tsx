"use client";

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchAdminDashboard } from '@/lib/api';
import type { AdminDashboard } from '@/types/admin';

const MAIN_GROUPS: Record<string, { icon: string; label: string }> = {
  'pass-do': { icon: '◈', label: 'Trao đổi đồ dùng' },
  'ghep-phong-tim-tro': { icon: '⌂', label: 'Nhà ở sinh viên' },
  'su-kien': { icon: '✦', label: 'Hoạt động cộng đồng' },
  'hoc-tap': { icon: '▣', label: 'Chia sẻ học tập' },
};

export default function AdminGroupsPage() {
  const [data, setData] = useState<AdminDashboard | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchAdminDashboard().then(setData).catch(value => setError(value instanceof Error ? value.message : 'Không tải được dữ liệu nhóm.'));
  }, []);

  const groups = data?.groups.filter(group => Object.prototype.hasOwnProperty.call(MAIN_GROUPS, group.slug)) ?? [];
  return <main className="admin-console">
    <header className="admin-page-heading"><div><span>GROUP MANAGEMENT</span><h1>Quản lý nhóm</h1><p>Theo dõi bốn hội nhóm chính và trạng thái kiểm duyệt.</p></div></header>
    {error && <div className="admin-error">{error}</div>}
    <section className="admin-group-stats admin-main-groups">
      <div className="admin-main-groups-heading"><div><h2>Hoạt động theo nhóm</h2><p>Dữ liệu và quyền xử lý của mỗi nhóm được quản lý riêng.</p></div><span>{groups.length} nhóm</span></div>
      <div className="admin-main-groups-grid">{groups.map(group => <article key={group.id}>
        <div className="admin-group-card-top"><span className="admin-group-card-icon" aria-hidden="true">{MAIN_GROUPS[group.slug].icon}</span><span className="admin-group-card-category">{MAIN_GROUPS[group.slug].label}</span></div>
        <h3>{group.name}</h3>
        <div className="admin-group-card-metrics"><div><b>{group.members}</b><span>Thành viên</span></div><div><b>{group.approved_posts}</b><span>Bài đã duyệt</span></div><div><b>{group.pending_posts}</b><span>Chờ duyệt</span></div></div>
        <Link href={`/group-admin?groupId=${group.id}`}>Xem quản trị nhóm <span aria-hidden="true">→</span></Link>
      </article>)}</div>
      {data && !groups.length && <p className="admin-empty-state">Chưa tìm thấy bốn hội nhóm chính trong dữ liệu.</p>}
      {!data && !error && <p className="admin-loading">Đang tải dữ liệu nhóm...</p>}
    </section>
  </main>;
}
