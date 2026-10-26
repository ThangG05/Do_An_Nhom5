"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import DisciplineActions from "@/components/admin/DisciplineActions";
import RagTokenSummary from "@/components/admin/RagTokenSummary";
import { fetchAdminUsers } from "@/lib/api";
import type { AdminUser, RagPeriod } from "@/types/admin";

type AccountGroup = "ADMIN" | "USER";
const PAGE_SIZE = 10;

export default function AdminUsersPage() {
  const [group, setGroup] = useState<AccountGroup>("ADMIN");
  const [pages, setPages] = useState<Record<AccountGroup, number>>({ ADMIN: 0, USER: 0 });
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [period, setPeriod] = useState<RagPeriod>("30d");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const requestId = useRef(0);
  const page = pages[group];
  const validPeriod = period !== "custom" || Boolean(startDate && endDate && startDate <= endDate);

  const resetPages = () => setPages({ ADMIN: 0, USER: 0 });
  const load = useCallback(async () => {
    const current = ++requestId.current;
    if (!validPeriod) { setLoading(false); return; }
    setLoading(true);
    try {
      const result = await fetchAdminUsers(q, status, period, startDate, endDate, group, page * PAGE_SIZE, PAGE_SIZE);
      if (current !== requestId.current) return;
      if (page > 0 && result.total <= page * PAGE_SIZE) {
        setPages(previous => ({ ...previous, [group]: Math.max(0, Math.ceil(result.total / PAGE_SIZE) - 1) }));
        return;
      }
      setUsers(result.items);
      setTotal(result.total);
      setError("");
    } catch (cause) {
      if (current === requestId.current) setError(cause instanceof Error ? cause.message : "Không tải được tài khoản.");
    } finally {
      if (current === requestId.current) setLoading(false);
    }
  }, [q, status, period, startDate, endDate, group, page, validPeriod]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 250);
    return () => { window.clearTimeout(timer); requestId.current += 1; };
  }, [load]);

  const setPage = (next: number) => setPages(current => ({ ...current, [group]: Math.max(0, next) }));
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return <main className="admin-console">
    <header className="admin-page-heading"><div><span>ACCOUNT MANAGEMENT</span><h1>Quản lý tài khoản</h1><p>Tra cứu vai trò hiện tại và xử lý kỷ luật người dùng.</p></div></header>
    {error && <div className="admin-error" role="alert"><span>{error === 'Failed to fetch' ? 'Không kết nối được backend. Kiểm tra dịch vụ API rồi thử lại.' : error}</span> <button type="button" onClick={() => void load()}>Thử lại</button></div>}
    <section className="admin-users">
      <header><div><h2>Danh sách tài khoản</h2><p>Vai trò được hiển thị để tra cứu, không chỉnh sửa tại đây.</p></div><div><input value={q} onChange={event => { setQ(event.target.value); resetPages(); }} placeholder="Tên, mã SV, email, khoa..." aria-label="Tìm tài khoản"/><select value={status} onChange={event => { setStatus(event.target.value); resetPages(); }} aria-label="Trạng thái tài khoản"><option value="">Mọi trạng thái</option><option value="ACTIVE">Hoạt động</option><option value="LOCKED">Tạm khóa</option><option value="DISABLED">Khóa vĩnh viễn</option></select></div></header>
      <div className="admin-account-tabs" role="tablist" aria-label="Loại tài khoản">
        <button type="button" role="tab" aria-selected={group === "ADMIN"} className={group === "ADMIN" ? "active" : ""} onClick={() => setGroup("ADMIN")}>Tài khoản Admin</button>
        <button type="button" role="tab" aria-selected={group === "USER"} className={group === "USER" ? "active" : ""} onClick={() => setGroup("USER")}>Tài khoản người dùng</button>
      </div>
      <div className="admin-rag-period"><strong>Token RAG</strong><select value={period} onChange={event => { setPeriod(event.target.value as RagPeriod); resetPages(); }} aria-label="Khoảng thời gian token"><option value="today">Hôm nay</option><option value="7d">7 ngày</option><option value="30d">30 ngày</option><option value="custom">Tùy chọn</option><option value="all">Toàn thời gian</option></select>{period === "custom" && <><input type="date" value={startDate} onChange={event => { setStartDate(event.target.value); resetPages(); }} aria-label="Từ ngày"/><span>đến</span><input type="date" value={endDate} onChange={event => { setEndDate(event.target.value); resetPages(); }} aria-label="Đến ngày"/></>}{!validPeriod && <small>Chọn khoảng ngày hợp lệ.</small>}</div>
      {loading ? <p className="admin-loading" role="status">Đang tải dữ liệu...</p> : <div className="admin-user-list">
        {users.map(user => <article key={user.id}>
          <div className="admin-user-main"><div className="admin-avatar">{user.full_name.slice(0, 1).toUpperCase()}</div><div><strong>{user.full_name}</strong><p>{user.email} · @{user.username}</p><small>{user.student_code || "Chưa có mã SV"}{user.faculty ? ` · ${user.faculty}` : ""}</small></div><span className={`admin-status ${user.status.toLowerCase()}`}>{user.status}</span></div>
          <RagTokenSummary user={user} period={period} startDate={startDate} endDate={endDate}/>
          <div className="admin-role-row"><b>Vai trò hiện tại:</b><span className="admin-role-label">{user.system_role === "SUPER_ADMIN" ? "Super Admin" : user.admin_groups.length ? "Group Admin" : "Người dùng"}</span>{user.system_role !== "SUPER_ADMIN" && user.admin_groups.map(adminGroup => <span className="admin-role-label group" key={adminGroup.id}>{adminGroup.name}</span>)}</div>
          <div className="admin-account-actions">{user.system_role === "SUPER_ADMIN" ? <span>SUPER ADMIN</span> : <DisciplineActions user={user} onDone={load}/>}</div>
        </article>)}
        {!users.length && !error && <p className="admin-loading">Không tìm thấy tài khoản {group === "ADMIN" ? "Admin" : "người dùng"}.</p>}
      </div>}
      {!loading && total > 0 && <nav className="admin-account-pagination" aria-label={`Phân trang tài khoản ${group === "ADMIN" ? "Admin" : "người dùng"}`}><span>{total} tài khoản · Trang {page + 1}/{pageCount}</span><div><button type="button" disabled={page === 0} onClick={() => setPage(page - 1)}>‹ Trước</button><button type="button" disabled={page + 1 >= pageCount} onClick={() => setPage(page + 1)}>Tiếp ›</button></div></nav>}
    </section>
  </main>;
}
