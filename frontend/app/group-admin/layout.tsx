"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import UserAvatar from "@/components/ui/UserAvatar";
import { getAuthUser, logoutSession, type AuthUser } from "@/lib/auth";
import "../admin/admin-shell.css";
import "./group-admin-shell.css";
import "./group-admin-fixes.css";
import "./member-ui.css";
import "./member-alignment.css";

export default function GroupAdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const accountRef = useRef<HTMLDivElement | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
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

  if (!ready) return <div className="admin-shell-loading">Đang kiểm tra quyền quản trị nhóm...</div>;

  const allowed = !!user && (user.system_role === "SUPER_ADMIN" || user.admin_group_slugs.length > 0);
  if (!allowed) {
    return (
      <main className="admin-access-denied">
        <section>
          <h1>Không có quyền truy cập</h1>
          <p>Khu vực này chỉ dành cho Group Admin.</p>
          <Link href="/login">Đăng nhập tài khoản quản trị nhóm</Link>
        </section>
      </main>
    );
  }

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

  return (
    <div className="admin-shell group-admin-shell">
      <div className="admin-workspace">
        <header className="admin-topbar">
          <Link href="/group-admin" className="group-admin-top-brand">
            <img src="/assets/logo.png" alt="HVNH Hub" />
            <strong>HVNH Hub</strong>
          </Link>
          <div className="group-admin-top-title">
            <span>TRUNG TÂM ĐIỀU HÀNH NHÓM</span>
            <strong>Quản trị nhóm</strong>
          </div>
          <div className="group-admin-account-wrap" ref={accountRef}>
            <button
              type="button"
              className="admin-identity"
              onClick={() => setAccountOpen((value) => !value)}
              aria-expanded={accountOpen}
              aria-haspopup="menu"
              aria-label="Mở menu tài khoản quản trị nhóm"
            >
              <div>
                <strong>{user.full_name || "Group Admin"}</strong>
                <small>{user.email}</small>
              </div>
              <UserAvatar src={user.avatar_url} name={user.full_name} fallbackClassName="admin-identity-initial" />
            </button>
            {accountOpen && (
              <div className="group-admin-account-menu" role="menu">
                <strong>{user.full_name || "Group Admin"}</strong>
                <span>{user.email}</span>
                <button type="button" onClick={() => void signOut()} disabled={signingOut}>
                  {signingOut ? "Đang đăng xuất..." : "Đăng xuất"}
                </button>
              </div>
            )}
          </div>
        </header>
        <div className="admin-workspace-content">{children}</div>
      </div>
    </div>
  );
}
