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
  updateFriendshipStatus,
  createProfilePost,
  CURRENT_USER_MOCK,
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
  handleFriendAction: (action: 'add' | 'accept' | 'reject' | 'unfriend' | 'cancel') => Promise<void>;
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

  const resolvedUserId = targetUserId || CURRENT_USER_MOCK.id;
  const isOwnProfile = !targetUserId || targetUserId === CURRENT_USER_MOCK.id || targetUserId === 'me';

  const loadProfileData = useCallback(async () => {
    setIsLoading(true);
    setIsError(false);
    setErrorMessage('');
    try {
      const profileData = await fetchUserProfile(resolvedUserId);
      setProfile(profileData);

      const [userPosts, userFriends, userPhotos, userListings] = await Promise.all([
        fetchUserPosts(resolvedUserId),
        fetchUserFriends(resolvedUserId),
        fetchUserPhotos(resolvedUserId),
        fetchUserListings(resolvedUserId),
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
      setProfile(updated);
      setIsEditModalOpen(false);
    } catch (err: unknown) {
      console.error('Lỗi cập nhật hồ sơ:', err);
    }
  };

  const handleFriendAction = async (action: 'add' | 'accept' | 'reject' | 'unfriend' | 'cancel') => {
    if (!profile) return;
    try {
      const res = await updateFriendshipStatus(profile.id, action);
      setProfile((prev) => (prev ? { ...prev, friendshipStatus: res.status as FriendshipStatus } : null));
    } catch (err: unknown) {
      console.error('Lỗi tương tác bạn bè:', err);
    }
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
    handleFriendAction,
    handleCreatePost,
    refetchData: loadProfileData,
  };
}
