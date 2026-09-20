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
import { createReport, setUserBlocked } from '@/lib/api';
import { useDialog } from '@/components/ui/DialogProvider';

export default function VisitorProfilePage() {
  const dialog = useDialog();
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
    unfriendById,
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
      {!isOwnProfile && (
        <div className="profile-report-row">
          <button type="button" className="btn btn-secondary btn-sm" onClick={async () => {
            const reason = await dialog.prompt({title:'Báo cáo tài khoản',message:`Mô tả hành vi vi phạm của ${profile.name}.`,placeholder:'Lý do báo cáo...',multiline:true,minLength:5,tone:'danger'});
            if (!reason) return;
            try { await createReport('USER', profile.id, reason); dialog.notify({title:'Đã gửi báo cáo',message:'Quản trị viên sẽ xem xét nội dung này.',tone:'success'}); }
            catch (error) { dialog.notify({title:'Không thể gửi báo cáo',message:error instanceof Error ? error.message : undefined,tone:'danger'}); }
          }}>Báo cáo tài khoản</button>
          <button type="button" className="btn btn-secondary btn-sm" onClick={async()=>{if(!await dialog.confirm({title:'Chặn người dùng?',message:'Hai bên sẽ không thể xem hồ sơ, kết bạn hoặc nhắn tin. Quan hệ bạn bè hiện tại sẽ bị hủy.',confirmLabel:'Chặn người dùng',tone:'danger'}))return;try{await setUserBlocked(profile.id,true);window.location.assign('/home');}catch(error){dialog.notify({title:'Không thể chặn người dùng',message:error instanceof Error?error.message:undefined,tone:'danger'});}}}>Chặn người dùng</button>
        </div>
      )}

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
              <ProfilePhotosWidget photos={photos} onSeeAllPhotos={setActiveTab} />
              <ProfileFriendsWidget friends={friends} friendsCount={profile.friendsCount} onSeeAllFriends={setActiveTab} />
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

        {activeTab === 'friends' && (
          <ProfileFriendsTab friends={friends} isOwnProfile={isOwnProfile} searchQuery={friendsSearch} filter={friendsFilter} onSearchChange={setFriendsSearch} onFilterChange={setFriendsFilter} onUnfriend={unfriendById} />
        )}

        {activeTab === 'photos' && (
          <ProfilePhotosTab photos={photos} subTab={photosSubTab} onSubTabChange={setPhotosSubTab} />
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
