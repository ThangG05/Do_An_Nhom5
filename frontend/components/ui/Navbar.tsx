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
  IconSearch,
  IconInfo,
  IconSettings,
  IconLogout,
  IconAI,
} from './Icons';
import { AuthUser, getAccessToken, getAuthUser, logoutSession } from '@/lib/auth';
import { createWebSocketTicket, fetchUnreadMessageCount, fetchUnreadNotificationCount } from '@/lib/api';

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();

  const [searchQuery, setSearchQuery] = useState('');
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [notificationCount, setNotificationCount] = useState(0);
  const [messageCount, setMessageCount] = useState(0);
  const profileMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setAuthUser(getAuthUser());
    setIsProfileMenuOpen(false);
  }, [pathname]);

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
    if(!getAccessToken())return;
    let socket:WebSocket|undefined,timer:number|undefined,cancelled=false;
    void createWebSocketTicket().then(ticket=>{if(cancelled)return;const base=(process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000/api/v1').replace(/^http/,'ws');socket=new WebSocket(`${base}/chat/ws?ticket=${encodeURIComponent(ticket)}`);socket.onmessage=event=>{try{const data=JSON.parse(event.data);if(data.event==='notification.created'){void fetchUnreadNotificationCount().then(setNotificationCount);if(data.type==='MESSAGE')void fetchUnreadMessageCount().then(setMessageCount);}else if(data.event==='call.offer'&&pathname!=='/messages'){window.sessionStorage.setItem('hvnh-pending-call',JSON.stringify(data));router.push(`/messages?conversationId=${encodeURIComponent(data.conversation_id)}`);}}catch{/* ignore malformed frames */}};timer=window.setInterval(()=>{if(socket?.readyState===WebSocket.OPEN)socket.send('ping');},25000);}).catch(()=>undefined);
    return()=>{cancelled=true;if(timer!==undefined)window.clearInterval(timer);socket?.close();};
  },[pathname]);

  useEffect(() => {
    if (!getAccessToken()) {
      setMessageCount(0);
      return;
    }
    const refreshCount = () => { void fetchUnreadMessageCount().then(setMessageCount).catch(() => undefined); };
    refreshCount(); window.addEventListener('messages-changed', refreshCount);
    const timer = window.setInterval(refreshCount, 30000);
    return () => { window.removeEventListener('messages-changed', refreshCount); window.clearInterval(timer); };
  }, [pathname]);

  useEffect(() => {
    if (!getAccessToken()) {
      setNotificationCount(0);
      return;
    }
    const refreshCount = () => { void fetchUnreadNotificationCount().then(setNotificationCount).catch(() => undefined); };
    refreshCount();
    window.addEventListener('notifications-changed', refreshCount);
    const timer = window.setInterval(refreshCount, 30000);
    return () => { window.removeEventListener('notifications-changed', refreshCount); window.clearInterval(timer); };
  }, [pathname]);

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
    { label: 'Tin nhắn', href: '/messages', icon: IconMessage, badge: messageCount },
    { label: 'Thông báo', href: '/notifications', icon: IconBell, badge: notificationCount },
  ];

  return (
    <header className="global-navbar-header">
      <div className="navbar-container">
        {/* 1. Left Brand Logo Asset */}
        <div className="navbar-brand-col">
          <Link href="/home" className="navbar-brand-link" aria-label="Về trang chủ HVNH Hub">
            <img
              src="/assets/logo.png"
              alt="HVNH Hub Logo"
              className="navbar-brand-logo-img"
            />
            <span className="brand-title-text">HVNH Hub</span>
          </Link>
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
                  {item.badge && item.badge > 0 && (
                    <span className="nav-badge-pill">{item.badge}</span>
                  )}
                  {isActive && <div className="active-navy-indicator" />}
                </Link>
              </div>
            );
          })}
        </nav>

        {/* 3. Right Utility Area (Global Search Bar & Profile Dropdown Menu) */}
        <div className="navbar-right-col">
          {/* Global Search Pill Input */}
          <form className="global-search-pill" onSubmit={(event) => { event.preventDefault(); const query=searchQuery.trim(); if(query) router.push(`/search?q=${encodeURIComponent(query)}`); }}>
            <IconSearch size={16} className="search-pill-icon" />
            <input
              type="text"
              className="search-pill-input"
              placeholder="Tìm kiếm sinh viên, bài viết..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Tìm kiếm sinh viên"
            />
          </form>

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
                  href="/settings/blocked"
                  className="pop-menu-row"
                  onClick={() => setIsProfileMenuOpen(false)}
                >
                  <IconSettings size={18} />
                  <span>Danh sách đã chặn</span>
                </Link>
                <button
                  type="button"
                  className="pop-menu-row"
                  onClick={() => { setIsProfileMenuOpen(false); router.push('/settings/password'); }}
                >
                  <IconSettings size={18} />
                  <span>Cài đặt & Quyền riêng tư</span>
                </button>
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
    </header>
  );
}


