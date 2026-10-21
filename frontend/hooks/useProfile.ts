"use client";

import { useState, useEffect, useCallback, useRef } from 'react';
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
  fetchUserGroupPosts,
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
  friendsLoading: boolean;
  friendsError: string;
  photos: UserPhoto[];
  listings: UserListing[];
  groupPosts: Post[];
  activeTab: ProfileTabType;
  isLoading: boolean;
  isError: boolean;
  errorMessage: string;
  isOwnProfile: boolean;
  isEditModalOpen: boolean;
  postFilter: string;
  friendsSearch: string;
  friendsFilter: string;
  photosSubTab: 'your_photos' | 'albums';
  listingsCategory: string;
  // State setters & Actions
  setActiveTab: (tab: ProfileTabType) => void;
  setIsEditModalOpen: (isOpen: boolean) => void;
  setPostFilter: (filter: string) => void;
  setFriendsSearch: (query: string) => void;
  setFriendsFilter: (filter: string) => void;
  setPhotosSubTab: (subTab: 'your_photos' | 'albums') => void;
  setListingsCategory: (category: string) => void;
  updateBio: (newBio: string) => Promise<void>;
  updateProfile: (data: Partial<UserProfile>) => Promise<void>;
  updateAvatar: (file: File, caption: string, visibility: 'PUBLIC' | 'FRIENDS' | 'PRIVATE') => Promise<void>;
  updateCover: (file: File) => Promise<void>;
  handleFriendAction: (action: 'add' | 'accept' | 'reject' | 'unfriend' | 'cancel') => Promise<void>;
  unfriendById: (friendId: string) => Promise<void>;
  handleCreatePost: (payload: CreatePostPayload) => Promise<Post | null>;
  refetchData: () => Promise<void>;
  refetchFriends: () => Promise<void>;
}

export function useProfile(targetUserId?: string): UseProfileReturn {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [friends, setFriends] = useState<UserFriend[]>([]);
  const [friendsLoading, setFriendsLoading] = useState(true);
  const [friendsError, setFriendsError] = useState('');
  const friendsRequestId = useRef(0);
  const [photos, setPhotos] = useState<UserPhoto[]>([]);
  const [listings, setListings] = useState<UserListing[]>([]);
  const [groupPosts, setGroupPosts] = useState<Post[]>([]);

  const [activeTab, setActiveTab] = useState<ProfileTabType>('posts');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isError, setIsError] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [isEditModalOpen, setIsEditModalOpen] = useState<boolean>(false);

  const [postFilter, setPostFilter] = useState<string>('all');
  const [friendsSearch, setFriendsSearch] = useState<string>('');
  const [friendsFilter, setFriendsFilter] = useState<string>('all');
  const [photosSubTab, setPhotosSubTab] = useState<'your_photos' | 'albums'>('your_photos');
  const [listingsCategory, setListingsCategory] = useState<string>('all');

  const resolvedUserId = targetUserId || 'me';
  const isOwnProfile = !targetUserId || targetUserId === 'me' || profile?.friendshipStatus === 'self';

  const loadFriends = useCallback(async (userId: string) => {
    const requestId = ++friendsRequestId.current;
    setFriendsLoading(true);
    setFriendsError('');
    try {
      const result = await fetchUserFriends(userId);
      if (requestId === friendsRequestId.current) setFriends(result);
    } catch (error) {
      if (requestId === friendsRequestId.current) {
        setFriendsError(error instanceof Error ? error.message : 'Không thể tải danh sách bạn bè.');
      }
    } finally {
      if (requestId === friendsRequestId.current) setFriendsLoading(false);
    }
  }, []);

  const loadProfileData = useCallback(async () => {
    friendsRequestId.current += 1;
    setFriends([]);
    setFriendsLoading(true);
    setFriendsError('');
    setIsLoading(true);
    setIsError(false);
    setErrorMessage('');
    try {
      const profileData = await fetchUserProfile(resolvedUserId);
      setProfile(profileData);
      void loadFriends(profileData.id);
      void Promise.allSettled([
        fetchUserPhotos(profileData.id).then(setPhotos),
        fetchUserListings(profileData.id).then(setListings),
        fetchUserGroupPosts(profileData.id).then(setGroupPosts),
      ]);
      setPosts(await fetchUserPosts(profileData.id));
    } catch (err: unknown) {
      setIsError(true);
      setErrorMessage(err instanceof Error ? err.message : 'Không thể tải thông tin hồ sơ.');
      setIsLoading(false);
      return;
    }

    // Show the default posts view once its data is ready. The other tabs and
    // sidebar panels should not keep the entire profile behind a skeleton.
    setIsLoading(false);
  }, [resolvedUserId, loadFriends]);

  useEffect(() => {
    loadProfileData();
  }, [loadProfileData]);

  const updateBio = async (newBio: string) => {
    if (!profile) return;
    const updated = await updateUserProfile({ bio: newBio });
    setProfile(updated);
  };

  const updateProfile = async (data: Partial<UserProfile>) => {
    if (!profile) return;
    const updated = await updateUserProfile(data);
    setProfile((previous) => ({
      ...updated,
      avatar: data.avatar ?? previous?.avatar ?? updated.avatar,
      coverBanner: data.coverBanner ?? previous?.coverBanner ?? updated.coverBanner,
    }));
    setIsEditModalOpen(false);
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
    const res = await updateFriendshipStatus(profile.id, action);
    setProfile((prev) => (prev ? { ...prev, friendshipStatus: res.status as FriendshipStatus } : null));
    if (action === 'accept' || action === 'unfriend') await loadProfileData();
  };

  const unfriendById = async (friendId: string) => {
    await updateFriendshipStatus(friendId, 'unfriend');
    setFriends((previous) => previous.filter((friend) => friend.id !== friendId));
    setProfile((previous) => previous ? { ...previous, friendsCount: Math.max(0, previous.friendsCount - 1) } : previous);
  };

  const refetchFriends = async () => {
    if (profile) await loadFriends(profile.id);
  };

  const handleCreatePost = async (payload: CreatePostPayload): Promise<Post | null> => {
    const newPost = await createProfilePost(payload);
    if (newPost.status === 'APPROVED') setPosts((prev) => [newPost, ...prev]);
    return newPost;
  };

  return {
    profile,
    posts,
    friends,
    friendsLoading,
    friendsError,
    photos,
    listings,
    groupPosts,
    activeTab,
    isLoading,
    isError,
    errorMessage,
    isOwnProfile,
    isEditModalOpen,
    postFilter,
    friendsSearch,
    friendsFilter,
    photosSubTab,
    listingsCategory,
    setActiveTab,
    setIsEditModalOpen,
    setPostFilter,
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
    refetchFriends,
  };
}
