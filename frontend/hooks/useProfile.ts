"use client";

import { useState, useEffect, useCallback } from 'react';
import {
  UserProfile,
  UserFriend,
  UserPhoto,
  UserListing,
  ProfileTabType,
  FriendshipStatus,
} from '@/types/user';
import { Post, CreatePostPayload } from '@/types/post';
import {
  fetchUserProfile,
  fetchUserPosts,
  fetchUserFriends,
  fetchUserPhotos,
  fetchUserListings,
  updateUserProfile,
  uploadProfileAvatar,
  uploadProfileCover,
  updateFriendshipStatus,
  createProfilePost,
} from '@/lib/api';

export interface UseProfileReturn {
  profile: UserProfile | null;
  posts: Post[];
  friends: UserFriend[];
  photos: UserPhoto[];
  listings: UserListing[];
  activeTab: ProfileTabType;
  isLoading: boolean;
  isError: boolean;
  errorMessage: string;
  isOwnProfile: boolean;
  isEditModalOpen: boolean;
  postFilter: string;
  postViewMode: 'list' | 'grid';
  friendsSearch: string;
  friendsFilter: string;
  photosSubTab: 'of_you' | 'your_photos' | 'albums';
  listingsCategory: string;
  // State setters & Actions
  setActiveTab: (tab: ProfileTabType) => void;
  setIsEditModalOpen: (isOpen: boolean) => void;
  setPostFilter: (filter: string) => void;
  setPostViewMode: (mode: 'list' | 'grid') => void;
  setFriendsSearch: (query: string) => void;
  setFriendsFilter: (filter: string) => void;
  setPhotosSubTab: (subTab: 'of_you' | 'your_photos' | 'albums') => void;
  setListingsCategory: (category: string) => void;
  updateBio: (newBio: string) => Promise<void>;
  updateProfile: (data: Partial<UserProfile>) => Promise<void>;
  updateAvatar: (file: File, caption: string, visibility: 'PUBLIC' | 'FRIENDS' | 'PRIVATE') => Promise<void>;
  updateCover: (file: File) => Promise<void>;
  handleFriendAction: (action: 'add' | 'accept' | 'reject' | 'unfriend' | 'cancel') => Promise<void>;
  unfriendById: (friendId: string) => Promise<void>;
  handleCreatePost: (payload: CreatePostPayload) => Promise<Post | null>;
  refetchData: () => Promise<void>;
}

export function useProfile(targetUserId?: string): UseProfileReturn {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [friends, setFriends] = useState<UserFriend[]>([]);
  const [photos, setPhotos] = useState<UserPhoto[]>([]);
  const [listings, setListings] = useState<UserListing[]>([]);

  const [activeTab, setActiveTab] = useState<ProfileTabType>('posts');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isError, setIsError] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [isEditModalOpen, setIsEditModalOpen] = useState<boolean>(false);

  const [postFilter, setPostFilter] = useState<string>('all');
  const [postViewMode, setPostViewMode] = useState<'list' | 'grid'>('list');
  const [friendsSearch, setFriendsSearch] = useState<string>('');
  const [friendsFilter, setFriendsFilter] = useState<string>('all');
  const [photosSubTab, setPhotosSubTab] = useState<'of_you' | 'your_photos' | 'albums'>('your_photos');
  const [listingsCategory, setListingsCategory] = useState<string>('all');

  const resolvedUserId = targetUserId || 'me';
  const isOwnProfile = !targetUserId || targetUserId === 'me' || profile?.friendshipStatus === 'self';

  const loadProfileData = useCallback(async () => {
    setIsLoading(true);
    setIsError(false);
    setErrorMessage('');
    try {
      const profileData = await fetchUserProfile(resolvedUserId);
      setProfile(profileData);

      const [userPosts, userFriends, userPhotos, userListings] = await Promise.all([
        fetchUserPosts(profileData.id),
        fetchUserFriends(profileData.id),
        fetchUserPhotos(profileData.id),
        fetchUserListings(profileData.id),
      ]);

      setPosts(userPosts);
      setFriends(userFriends);
      setPhotos(userPhotos);
      setListings(userListings);
    } catch (err: unknown) {
      setIsError(true);
      setErrorMessage(err instanceof Error ? err.message : 'Không thể tải thông tin hồ sơ.');
    } finally {
      setIsLoading(false);
    }
  }, [resolvedUserId]);

  useEffect(() => {
    loadProfileData();
  }, [loadProfileData]);

  const updateBio = async (newBio: string) => {
    if (!profile) return;
    try {
      const updated = await updateUserProfile({ bio: newBio });
      setProfile(updated);
    } catch (err: unknown) {
      console.error('Lỗi cập nhật bio:', err);
    }
  };

  const updateProfile = async (data: Partial<UserProfile>) => {
    if (!profile) return;
    try {
      const updated = await updateUserProfile(data);
      setProfile((previous) => ({ ...updated, avatar: data.avatar ?? previous?.avatar ?? updated.avatar }));
      setIsEditModalOpen(false);
    } catch (err: unknown) {
      console.error('Lỗi cập nhật hồ sơ:', err);
    }
  };

  const updateAvatar = async (file: File, caption: string, visibility: 'PUBLIC' | 'FRIENDS' | 'PRIVATE') => {
    const avatar = await uploadProfileAvatar(file, caption, visibility);
    setProfile((previous) => previous ? { ...previous, avatar } : previous);
  };

  const updateCover = async (file: File) => {
    const coverBanner = await uploadProfileCover(file);
    setProfile((previous) => previous ? { ...previous, coverBanner } : previous);
  };

  const handleFriendAction = async (action: 'add' | 'accept' | 'reject' | 'unfriend' | 'cancel') => {
    if (!profile) return;
    try {
      const res = await updateFriendshipStatus(profile.id, action);
      setProfile((prev) => (prev ? { ...prev, friendshipStatus: res.status as FriendshipStatus } : null));
      if (action === 'accept' || action === 'unfriend') await loadProfileData();
    } catch (err: unknown) {
      console.error('Lỗi tương tác bạn bè:', err);
    }
  };

  const unfriendById = async (friendId: string) => {
    await updateFriendshipStatus(friendId, 'unfriend');
    setFriends((previous) => previous.filter((friend) => friend.id !== friendId));
    setProfile((previous) => previous ? { ...previous, friendsCount: Math.max(0, previous.friendsCount - 1) } : previous);
  };

  const handleCreatePost = async (payload: CreatePostPayload): Promise<Post | null> => {
    try {
      const newPost = await createProfilePost(payload);
      setPosts((prev) => [newPost, ...prev]);
      return newPost;
    } catch (err: unknown) {
      console.error('Lỗi tạo bài viết:', err);
      return null;
    }
  };

  return {
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
    updateAvatar,
    updateCover,
    handleFriendAction,
    unfriendById,
    handleCreatePost,
    refetchData: loadProfileData,
  };
}
