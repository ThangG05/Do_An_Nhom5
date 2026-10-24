"use client";

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  IconHome,
  IconGroups,
  IconMessage,
  IconBell,
  IconProfile,
  IconInfo,
  IconSettings,
  IconLogout,
  IconAI,
} from './Icons';
import { AuthUser, getAccessToken, getAuthUser, logoutSession } from '@/lib/auth';
import { fetchHeaderUnreadCounts } from '@/lib/api';
import { useAuthUser } from '@/components/auth/AuthProvider';
import NavbarQuickPanel from './NavbarQuickPanel';
import ProfileChatDock from '@/components/chat/ProfileChatDock';
import GlobalUserSearch from './GlobalUserSearch';

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();

  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [notificationCount, setNotificationCount] = useState(0);
  const [messageCount, setMessageCount] = useState(0);
  const profileMenuRef = useRef<HTMLDivElement>(null);
  const quickPanelRef = useRef<HTMLDivElement>(null);
  const [quickPanel, setQuickPanel] = useState<'messages' | 'notifications' | null>(null);
  const [dockUser, setDockUser] = useState<{ id: string; name: string; avatar: string } | null>(null);
  const contextUser = useAuthUser();

  useEffect(() => {
    setAuthUser(contextUser || getAuthUser());
    setIsProfileMenuOpen(false);
    setQuickPanel(null);
  }, [pathname, contextUser]);

  useEffect(() => { setDockUser(null); }, [pathname]);

  useEffect(() => {
    if (!isProfileMenuOpen) return;
    const closeOnOutsideClick = (event: MouseEvent) => {
      if (!profileMenuRef.current?.contains(event.target as Node)) setIsProfileMenuOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setIsProfileMenuOpen(false);
    };
    document.addEventListener('mousedown', closeOnOutsideClick);
    document.addEventListener('keydown', closeOnEscape);
    return () => {
      document.removeEventListener('mousedown', closeOnOutsideClick);
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [isProfileMenuOpen]);

  useEffect(() => {
    if (!quickPanel) return;
    const close = (event: MouseEvent) => { if (!quickPanelRef.current?.contains(event.target as Node)) setQuickPanel(null); };
    const escape = (event: KeyboardEvent) => { if (event.key === 'Escape') setQuickPanel(null); };
    document.addEventListener('mousedown', close);
    document.addEventListener('keydown', escape);
    return () => { document.removeEventListener('mousedown', close); document.removeEventListener('keydown', escape); };
  }, [quickPanel]);

  useEffect(() => {
    const handleRealtime = (event: Event) => {
      const data = (event as CustomEvent<Record<string, unknown>>).detail;
      if (data?.event === 'call.offer' && pathname !== '/messages') {
        window.sessionStorage.setItem('hvnh-pending-call', JSON.stringify(data));
        router.push(`/messages?conversationId=${encodeURIComponent(String(data.conversation_id || ''))}`);
      }
    };
    window.addEventListener('hvnh-realtime', handleRealtime);
    return () => window.removeEventListener('hvnh-realtime', handleRealtime);
  }, [pathname, router]);

  useEffect(() => {
    if (!contextUser || !getAccessToken()) {
      setMessageCount(0);
      setNotificationCount(0);
      return;
    }
    let active = true;
    const refreshCount = () => {
      void fetchHeaderUnreadCounts().then(counts => {
        if (active) {
          setMessageCount(counts.messages);
          setNotificationCount(counts.notifications);
        }
      }).catch(() => undefined);
    };
    refreshCount();
    window.addEventListener('messages-changed', refreshCount);
    window.addEventListener('notifications-changed', refreshCount);
    const timer = window.setInterval(refreshCount, 30000);
    return () => {
      active = false;
      window.removeEventListener('messages-changed', refreshCount);
      window.removeEventListener('notifications-changed', refreshCount);
      window.clearInterval(timer);
    };
  }, [contextUser?.id]);

  // Completely hide top navbar on unauthenticated and onboarding flows
  const authRoutes = [
    '/',
    '/login',
    '/signin',
    '/register',
    '/signup',
    '/onboarding',
    '/welcome',
    '/forgot-password',
    '/reset-password',
    '/verification',
    '/password',
    '/maintenance',
  ];
  
  const isAuthRoute =
    pathname === '/' ||
    pathname.startsWith('/admin') ||
    authRoutes.some((route) => route !== '/' && pathname.startsWith(route));

  if (isAuthRoute) {
    return null;
  }

  const handleLogout = async () => {
    await logoutSession();
    router.replace('/login');
  };

  const navItems = [
    { label: 'Trang chủ', href: '/home', icon: IconHome },
    { label: 'Trợ lý AI', href: '/assistant', icon: IconAI },
    { label: 'Hội nhóm', href: '/groups', icon: IconGroups },
  ];

  if (pathname.startsWith('/admin') || pathname.startsWith('/group-admin')) return null;
  return (
    <header className="global-navbar-header">
      <div className="navbar-container">
        {/* Brand and search */}
        <div className="navbar-brand-col">
          <Link href="/home" className="navbar-brand-link" aria-label="Về trang chủ HVNH Hub">
            <img
              src="/assets/logo.png"
              alt="HVNH Hub Logo"
              className="navbar-brand-logo-img"
            />
            <span className="brand-title-text">HVNH Hub</span>
          </Link>
          <GlobalUserSearch />
        </div>

        {/* 2. Center Core Navigation Links */}
        <nav className="navbar-center-nav" aria-label="Điều hướng hệ thống">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              pathname === item.href ||
              (item.href === '/groups' &&
                (pathname.startsWith('/groups') ||
                  pathname.startsWith('/market') ||
                  pathname.startsWith('/roommate') ||
                  pathname.startsWith('/events'))) ||
              (item.href === '/notifications' && pathname.startsWith('/notifications'));

            return (
              <div key={item.href} className="nav-link-wrapper">
                <Link
                  href={item.href}
                  className={`global-nav-link ${isActive ? 'active' : ''}`}
                >
                  <Icon size={20} className="nav-icon-stroke" />
                  <span className="nav-label">{item.label}</span>
                  {isActive && <div className="active-navy-indicator" />}
                </Link>
              </div>
            );
          })}
          <Link href="/messages" className={`global-nav-link navbar-mobile-only ${pathname === '/messages' ? 'active' : ''}`}><IconMessage size={20}/><span className="nav-label">Tin nhắn</span>{messageCount > 0 && <span className="nav-badge-pill">{messageCount}</span>}</Link>
          <Link href="/notifications" className={`global-nav-link navbar-mobile-only ${pathname === '/notifications' ? 'active' : ''}`}><IconBell size={20}/><span className="nav-label">Thông báo</span>{notificationCount > 0 && <span className="nav-badge-pill">{notificationCount}</span>}</Link>
        </nav>

        {/* Notifications, messages and account */}
        <div className="navbar-right-col">
          <div className="navbar-quick-wrap" ref={quickPanelRef}>
            <button type="button" className={`navbar-quick-trigger ${quickPanel === 'messages' ? 'active' : ''}`} aria-label="Mở tin nhắn gần đây" aria-expanded={quickPanel === 'messages'} onClick={() => { setIsProfileMenuOpen(false); setDockUser(null); setQuickPanel(current => current === 'messages' ? null : 'messages'); }}><IconMessage size={21}/>{messageCount > 0 && <span>{messageCount}</span>}</button>
            <button type="button" className={`navbar-quick-trigger ${quickPanel === 'notifications' ? 'active' : ''}`} aria-label="Mở thông báo gần đây" aria-expanded={quickPanel === 'notifications'} onClick={() => { setIsProfileMenuOpen(false); setDockUser(null); setQuickPanel(current => current === 'notifications' ? null : 'notifications'); }}><IconBell size={21}/>{notificationCount > 0 && <span>{notificationCount}</span>}</button>
            {quickPanel && <NavbarQuickPanel kind={quickPanel} onClose={() => setQuickPanel(null)} onChat={setDockUser} />}
          </div>

          {/* User Profile Avatar Dropdown Menu */}
          <div className="utility-dropdown-container" ref={profileMenuRef}>
            <button
              type="button"
              className="profile-avatar-trigger"
              onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
              aria-expanded={isProfileMenuOpen}
              aria-haspopup="menu"
              aria-label="Menu tài khoản"
            >
              <img
                src={authUser?.avatar_url || '/assets/logo.png'}
                alt={authUser?.full_name || 'Avatar'}
                className="user-nav-avatar"
              />
              <span className="online-green-dot" />
            </button>

            {isProfileMenuOpen && (
              <div className="utility-popup-card profile-menu-popup">
                <div className="profile-pop-user-info">
                  <strong>{authUser?.full_name || 'Sinh viên HVNH'}</strong>
                  <small>@{authUser?.username || 'hvnh'} • Sinh viên</small>
                </div>
                <div className="pop-menu-divider" />
                <Link
                  href="/profile"
                  className="pop-menu-row"
                  onClick={() => setIsProfileMenuOpen(false)}
                >
                  <IconProfile size={18} />
                  <span>Trang cá nhân của tôi</span>
                </Link>
                <Link
                  href="/about"
                  className="pop-menu-row"
                  onClick={() => setIsProfileMenuOpen(false)}
                >
                  <IconInfo size={18} />
                  <span>Giới thiệu về HVNH Hub</span>
                </Link>
                {authUser?.system_role === 'SUPER_ADMIN' && (
                  <Link
                    href="/admin"
                    className="pop-menu-row"
                    onClick={() => setIsProfileMenuOpen(false)}
                  >
                    <IconSettings size={18} />
                    <span>Quản trị hệ thống</span>
                  </Link>
                )}
                {!!authUser?.admin_group_slugs?.length && <Link href="/group-admin" className="pop-menu-row" onClick={() => setIsProfileMenuOpen(false)}><IconSettings size={18}/><span>Quản trị nhóm</span></Link>}
                <Link
                  href="/settings"
                  className="pop-menu-row"
                  onClick={() => setIsProfileMenuOpen(false)}
                >
                  <IconSettings size={18} />
                  <span>Cài đặt & Quyền riêng tư</span>
                </Link>
                <div className="pop-menu-divider" />
                <button
                  type="button"
                  className="pop-menu-row danger"
                  onClick={handleLogout}
                >
                  <IconLogout size={18} />
                  <span>Đăng xuất</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
      {dockUser && <ProfileChatDock key={dockUser.id} userId={dockUser.id} name={dockUser.name} avatar={dockUser.avatar} onClose={() => setDockUser(null)} />}
    </header>
  );
}


