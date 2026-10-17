"use client";

import { useEffect, useRef, useState } from 'react';
import { fetchAdminDashboard, fetchGroupAdmins } from '@/lib/api';
import type { AdminDashboard, GroupAdminInfo } from '@/types/admin';
import styles from './group-admin-info.module.css';

const MAIN_GROUPS: Record<string, { icon: string; label: string }> = {
  'pass-do': { icon: '◈', label: 'Trao đổi đồ dùng' },
  'ghep-phong-tim-tro': { icon: '⌂', label: 'Nhà ở sinh viên' },
  'su-kien': { icon: '✦', label: 'Hoạt động cộng đồng' },
  'hoc-tap': { icon: '▣', label: 'Chia sẻ học tập' },
};

export default function AdminGroupsPage() {
  const [data, setData] = useState<AdminDashboard | null>(null);
  const [error, setError] = useState('');
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null);
  const [groupAdmins, setGroupAdmins] = useState<GroupAdminInfo[]>([]);
  const [adminsLoading, setAdminsLoading] = useState(false);
  const [adminsError, setAdminsError] = useState('');
  const requestVersion = useRef(0);

  useEffect(() => {
    fetchAdminDashboard().then(setData).catch(value => setError(value instanceof Error ? value.message : 'Không tải được dữ liệu nhóm.'));
  }, []);

  const toggleAdmins = async (groupId: string) => {
    const version = ++requestVersion.current;
    if (selectedGroupId === groupId) { setSelectedGroupId(null); return; }
    setSelectedGroupId(groupId);
    setGroupAdmins([]);
    setAdminsError('');
    setAdminsLoading(true);
    try {
      const result = await fetchGroupAdmins(groupId);
      if (version === requestVersion.current) setGroupAdmins(result);
    } catch (cause) {
      if (version === requestVersion.current) setAdminsError(cause instanceof Error ? cause.message : 'Không tải được quản trị viên nhóm.');
    } finally {
      if (version === requestVersion.current) setAdminsLoading(false);
    }
  };

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
        <button type="button" className={styles.trigger} onClick={() => void toggleAdmins(group.id)} aria-expanded={selectedGroupId === group.id} aria-controls={`group-admins-${group.id}`}>Xem quản trị viên <span aria-hidden="true">{selectedGroupId === group.id ? '−' : '→'}</span></button>
        {selectedGroupId === group.id && <div id={`group-admins-${group.id}`} className={styles.panel}>
          <h4>Quản trị viên của {group.name}</h4>
          {adminsLoading ? <p>Đang tải thông tin…</p> : adminsError ? <p role="alert" className={styles.error}>{adminsError}</p> : groupAdmins.length ? <ul className={styles.list}>{groupAdmins.map(admin => <li key={admin.id}>
            {admin.avatar_url ? <img src={admin.avatar_url} alt="" className={styles.avatar} /> : <span className={styles.avatarFallback} aria-hidden="true">{admin.full_name.charAt(0).toUpperCase()}</span>}
            <div><strong>{admin.full_name}</strong><span>{admin.email}</span><small>{[admin.student_code && `Mã SV: ${admin.student_code}`, admin.faculty].filter(Boolean).join(' · ') || 'Quản trị nhóm'}</small></div>
            {admin.status !== 'ACTIVE' && <em>{admin.status}</em>}
          </li>)}</ul> : <p>Nhóm này chưa được phân công quản trị viên.</p>}
        </div>}
      </article>)}</div>
      {data && !groups.length && <p className="admin-empty-state">Chưa tìm thấy bốn hội nhóm chính trong dữ liệu.</p>}
      {!data && !error && <p className="admin-loading">Đang tải dữ liệu nhóm...</p>}
    </section>
  </main>;
}
