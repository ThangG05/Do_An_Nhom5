export type FriendshipStatus =
  | 'self'
  | 'none'
  | 'friends'
  | 'pending_sent'
  | 'pending_received';

export type ProfileTabType =
  | 'posts'
  | 'about'
  | 'friends'
  | 'photos'
  | 'listings';

export interface UserSocialLinks {
  facebook?: string;
  instagram?: string;
  linkedin?: string;
  github?: string;
  website?: string;
}

export interface UserProfile {
  id: string;
  name: string;
  username: string;
  avatar: string;
  coverBanner: string;
  bio: string;
  pronouns: string;
  role?: string;
  studentCode?: string;
  faculty?: string;
  courseYear?: string;
  workplace?: string;
  education?: string;
  currentCity?: string;
  hometown?: string;
  joinedDate: string;
  email?: string;
  phone?: string;
  gender?: string;
  birthDate?: string;
  relationshipStatus?: string;
  isVerified?: boolean;
  isOnline?: boolean;
  friendsCount: number;
  followersCount: number;
  mutualFriendsCount: number;
  mutualFriendsAvatars: string[];
  friendshipStatus: FriendshipStatus;
  socialLinks?: UserSocialLinks;
}

export interface UserFriend {
  id: string;
  name: string;
  username: string;
  avatar: string;
  mutualCount: number;
  isOnline?: boolean;
  role?: string;
  faculty?: string;
  friendshipStatus: FriendshipStatus;
}

export interface UserPhoto {
  id: string;
  url: string;
  caption?: string;
  createdAt: string;
  likesCount?: number;
  albumName?: string;
}

export interface UserListing {
  id: string;
  title: string;
  category: 'market' | 'roommate' | 'event';
  price: string;
  location: string;
  status: 'active' | 'sold' | 'rented' | 'expired';
  imageUrl: string;
  createdAt: string;
  description?: string;
}

export interface User extends UserProfile {}
