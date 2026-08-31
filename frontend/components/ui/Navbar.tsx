"use client";

import React, { useState } from 'react';
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
} from './Icons';

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();

  const [searchQuery, setSearchQuery] = useState('');
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);

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
  ];
  
  const isAuthRoute =
    pathname === '/' ||
    authRoutes.some((route) => route !== '/' && pathname.startsWith(route));

  if (isAuthRoute) {
    return null;
  }

  const handleLogout = () => {
    if (typeof window !== 'undefined') {
      window.sessionStorage.removeItem('hvnh-hub-mock-authenticated');
    }
    router.push('/login');
  };

  const navItems = [
    { label: 'Trang chủ', href: '/home', icon: IconHome },
    { label: 'Hội nhóm', href: '/groups', icon: IconGroups },
    { label: 'Tin nhắn', href: '/messages', icon: IconMessage },
    { label: 'Thông báo', href: '/notifications', icon: IconBell, badge: 3 },
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
          <div className="global-search-pill">
            <IconSearch size={16} className="search-pill-icon" />
            <input
              type="text"
              className="search-pill-input"
              placeholder="Tìm kiếm sinh viên, bài viết..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* User Profile Avatar Dropdown Menu */}
          <div className="utility-dropdown-container">
            <button
              type="button"
              className="profile-avatar-trigger"
              onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
              aria-label="Menu tài khoản"
            >
              <img
                src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&q=80"
                alt="Avatar"
                className="user-nav-avatar"
              />
              <span className="online-green-dot" />
            </button>

            {isProfileMenuOpen && (
              <div className="utility-popup-card profile-menu-popup">
                <div className="profile-pop-user-info">
                  <strong>Trần Nguyễn Phương Thảo</strong>
                  <small>@phuongthao_hvnh • Sinh viên K25</small>
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
                <button
                  type="button"
                  className="pop-menu-row"
                  onClick={() => setIsProfileMenuOpen(false)}
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


