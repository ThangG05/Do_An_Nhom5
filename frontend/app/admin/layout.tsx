"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import UserAvatar from "@/components/ui/UserAvatar";
import { getAuthUser, logoutSession, type AuthUser } from "@/lib/auth";
import "./admin-shell.css";

const sections = [
  { href: "/admin", label: "Tổng quan", icon: "▦" },
  { href: "/admin/analytics", label: "Thống kê", icon: "⌁" },
  { href: "/admin/groups", label: "Quản lý nhóm", icon: "◉" },
  { href: "/admin/users", label: "Tài khoản", icon: "♙" },
  { href: "/admin/reports", label: "Báo cáo vi phạm", icon: "!" },
  { href: "/admin/audit", label: "Nhật ký quản trị", icon: "≡" },
  { href: "/admin/settings", label: "Cấu hình hệ thống", icon: "⚙" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const accountRef = useRef<HTMLDivElement | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [open, setOpen] = useState(false);
  const [ready, setReady] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [signingOut, setSigningOut] = useState(false);

  useEffect(() => {
    setUser(getAuthUser());
    setReady(true);
    setAccountOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!accountOpen) return;
    const closeOnPointerDown = (event: PointerEvent) => {
      if (!accountRef.current?.contains(event.target as Node)) setAccountOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setAccountOpen(false);
    };
    document.addEventListener("pointerdown", closeOnPointerDown);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOnPointerDown);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [accountOpen]);

  const signOut = async () => {
    if (signingOut) return;
    setSigningOut(true);
    try {
      await logoutSession();
      router.replace("/login");
    } finally {
      setSigningOut(false);
    }
  };

  if (!ready) return <div className="admin-shell-loading">Đang kiểm tra quyền quản trị...</div>;
  if (!user || user.system_role !== "SUPER_ADMIN") {
    return (
      <main className="admin-access-denied">
        <section>
          <h1>Không có quyền truy cập</h1>
          <p>Khu vực này chỉ dành cho Super Admin.</p>
          <Link href="/login">Đăng nhập tài khoản quản trị</Link>
        </section>
      </main>
    );
  }

  const currentSection = sections.find((item) => item.href === "/admin" ? pathname === "/admin" : pathname.startsWith(item.href));

  return (
    <div className="admin-shell">
      <aside className={open ? "admin-sidebar open" : "admin-sidebar"}>
        <Link href="/admin" className="admin-brand" onClick={() => setOpen(false)}>
          <img src="/assets/logo.png" alt="HVNH Hub" />
          <div><strong>HVNH HUB</strong><small>SUPER ADMIN</small></div>
        </Link>
        <div className="admin-side-label">QUẢN TRỊ HỆ THỐNG</div>
        <nav>
          {sections.map((item) => {
            const active = item.href === "/admin" ? pathname === "/admin" : pathname.startsWith(item.href);
            return (
              <Link className={active ? "active" : ""} aria-current={active ? "page" : undefined} key={item.href} href={item.href} onClick={() => setOpen(false)}>
                <i>{item.icon}</i><span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="admin-side-footer">
          <button type="button" onClick={() => void signOut()} disabled={signingOut}>{signingOut ? "Đang đăng xuất..." : "Đăng xuất"}</button>
        </div>
      </aside>
      {open && <button type="button" className="admin-sidebar-backdrop" aria-label="Đóng menu" onClick={() => setOpen(false)} />}
      <div className="admin-workspace">
        <header className="admin-topbar">
          <button type="button" className="admin-menu-toggle" onClick={() => setOpen(true)} aria-label="Mở menu quản trị">☰</button>
          <div><span>TRUNG TÂM ĐIỀU HÀNH</span><strong>{currentSection?.label || "Quản trị hệ thống"}</strong></div>
          <div className="admin-account-wrap" ref={accountRef}>
            <button type="button" className="admin-identity" onClick={() => setAccountOpen((value) => !value)} aria-expanded={accountOpen} aria-haspopup="menu" aria-label="Mở menu tài khoản quản trị">
              <div><strong>{user.full_name || "Super Admin"}</strong><small>{user.email}</small></div>
              <UserAvatar src={user.avatar_url} name={user.full_name} fallbackClassName="admin-identity-initial" />
            </button>
            {accountOpen && (
              <div className="admin-account-menu" role="menu">
                <div className="admin-account-summary">
                  <UserAvatar src={user.avatar_url} name={user.full_name} fallbackClassName="admin-identity-initial" />
                  <div><strong>{user.full_name || "Super Admin"}</strong><span>{user.email}</span><small>SUPER ADMIN</small></div>
                </div>
                <nav>
                  <Link href="/admin" onClick={() => setAccountOpen(false)}><i>▦</i><span><b>Trung tâm quản trị</b><small>Về trang tổng quan</small></span></Link>
                  <Link href="/admin/audit" onClick={() => setAccountOpen(false)}><i>≡</i><span><b>Nhật ký hoạt động</b><small>Xem lịch sử quản trị</small></span></Link>
                  <Link href="/admin/settings" onClick={() => setAccountOpen(false)}><i>⚙</i><span><b>Cài đặt hệ thống</b><small>Bảo trì và kiểm duyệt</small></span></Link>
                </nav>
                <button type="button" className="admin-menu-logout" onClick={() => void signOut()} disabled={signingOut}><i>↪</i> {signingOut ? "Đang đăng xuất..." : "Đăng xuất"}</button>
              </div>
            )}
          </div>
        </header>
        <div className="admin-workspace-content">{children}</div>
      </div>
    </div>
  );
}
