"use client";

import React from 'react';
import { useParams } from 'next/navigation';
import { useProfile } from '@/hooks/useProfile';
import ProfileHeader from '@/components/profile/ProfileHeader';
import ProfileIntroWidget from '@/components/profile/ProfileIntroWidget';
import ProfilePhotosWidget from '@/components/profile/ProfilePhotosWidget';
import ProfileFriendsWidget from '@/components/profile/ProfileFriendsWidget';
import ProfileListingsWidget from '@/components/profile/ProfileListingsWidget';
import ProfilePostsTab from '@/components/profile/ProfilePostsTab';
import ProfileAboutTab from '@/components/profile/ProfileAboutTab';
import ProfileFriendsTab from '@/components/profile/ProfileFriendsTab';
import ProfilePhotosTab from '@/components/profile/ProfilePhotosTab';
import ProfileListingsTab from '@/components/profile/ProfileListingsTab';
import EditProfileModal from '@/components/profile/EditProfileModal';

export default function VisitorProfilePage() {
  const params = useParams();
  const userId = (params?.id as string) || '102';

  const {
    profile,
    posts,
    friends,
    photos,
    listings,
    activeTab,
    isLoading,
    isError,
    errorMessage,
    isOwnProfile,
    isEditModalOpen,
    postFilter,
    postViewMode,
    friendsSearch,
    friendsFilter,
    photosSubTab,
    listingsCategory,
    setActiveTab,
    setIsEditModalOpen,
    setPostFilter,
    setPostViewMode,
    setFriendsSearch,
    setFriendsFilter,
    setPhotosSubTab,
    setListingsCategory,
    updateBio,
    updateProfile,
    handleFriendAction,
    handleCreatePost,
    refetchData,
  } = useProfile(userId);

  if (isLoading) {
    return (
      <div className="profile-page-loading-skeleton">
        <div className="skeleton-cover-banner" />
        <div className="skeleton-header-info">
          <div className="skeleton-avatar" />
          <div className="skeleton-lines">
            <div className="skeleton-line title" />
            <div className="skeleton-line sub" />
          </div>
        </div>
      </div>
    );
  }

  if (isError || !profile) {
    return (
      <div className="profile-page-error-container">
        <div className="error-card">
          <div className="error-icon">⚠️</div>
          <h2>Không tìm thấy trang cá nhân</h2>
          <p>{errorMessage || 'Người dùng không tồn tại hoặc đã bị khóa.'}</p>
          <button type="button" className="btn btn-primary" onClick={refetchData}>
            Thử lại
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-workspace-wrapper">
      {/* Profile Header Section */}
      <ProfileHeader
        profile={profile}
        isOwnProfile={isOwnProfile}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onOpenEditModal={() => setIsEditModalOpen(true)}
        onFriendAction={handleFriendAction}
      />

      {/* Main Profile Body Content Area */}
      <main className="profile-body-container">
        {/* 1. Posts Tab View */}
        {activeTab === 'posts' && (
          <div className="profile-2col-layout">
            <aside className="profile-left-sidebar">
              <ProfileIntroWidget
                profile={profile}
                isOwnProfile={isOwnProfile}
                onUpdateBio={updateBio}
                onOpenEditModal={() => setIsEditModalOpen(true)}
              />

              <ProfileListingsWidget
                listings={listings}
                onSeeAllListings={setActiveTab}
              />
            </aside>

            <section className="profile-right-timeline">
              <ProfilePostsTab
                profile={profile}
                posts={posts}
                isOwnProfile={isOwnProfile}
                postFilter={postFilter}
                postViewMode={postViewMode}
                onFilterChange={setPostFilter}
                onViewModeChange={setPostViewMode}
                onCreatePost={handleCreatePost}
              />
            </section>
          </div>
        )}

        {/* 2. About Tab View */}
        {activeTab === 'about' && (
          <ProfileAboutTab
            profile={profile}
            isOwnProfile={isOwnProfile}
            onOpenEditModal={() => setIsEditModalOpen(true)}
          />
        )}

        {/* 3. My Listings Tab View */}
        {activeTab === 'listings' && (
          <ProfileListingsTab
            listings={listings}
            isOwnProfile={isOwnProfile}
            categoryFilter={listingsCategory}
            onCategoryChange={setListingsCategory}
          />
        )}
      </main>

      {/* Edit Profile Modal */}
      <EditProfileModal
        profile={profile}
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onSave={updateProfile}
      />
    </div>
  );
}
