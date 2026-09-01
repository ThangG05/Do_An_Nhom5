"use client";

import React from 'react';
import { ProfileTabType } from '@/types/user';

interface ProfileNavTabsProps {
  activeTab: ProfileTabType;
  onTabChange: (tab: ProfileTabType) => void;
  friendsCount?: number;
  photosCount?: number;
  listingsCount?: number;
}

export default function ProfileNavTabs({
  activeTab,
  onTabChange,
  friendsCount = 0,
  photosCount = 0,
  listingsCount = 0,
}: ProfileNavTabsProps) {
  const tabs: { id: ProfileTabType; label: string; count?: number }[] = [
    { id: 'posts', label: 'Bài viết' },
    { id: 'about', label: 'Giới thiệu' },
    { id: 'listings', label: 'Bài niêm yết', count: listingsCount },
  ];

  return (
    <nav className="profile-nav-tabs-container" aria-label="Điều hướng hồ sơ">
      <div className="profile-nav-tabs-inner">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              className={`profile-nav-tab-btn ${isActive ? 'active' : ''}`}
              onClick={() => onTabChange(tab.id)}
              aria-current={isActive ? 'page' : undefined}
            >
              <span>{tab.label}</span>
              {tab.count !== undefined && tab.count > 0 && (
                <span className="tab-count-badge">{tab.count}</span>
              )}
              {isActive && <div className="active-tab-indicator" />}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
