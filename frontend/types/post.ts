export type PostCategory = 'general' | 'market' | 'roommate' | 'event' | 'study';

export type PostPrivacy = 'public' | 'friends' | 'private';

export interface PostMedia {
  id: string;
  url: string;
  type: 'image' | 'video' | 'audio' | 'file';
  file?: File;
  name?: string;
  size?: number;
  uploadProgress?: number;
  uploadStatus?: 'pending' | 'uploading' | 'complete' | 'error';
  uploadError?: string;
  uploadedMediaId?: string;
}

export interface MarketListingData {
  price: string;
  condition: string;
  location: string;
}

export interface RoomListingData {
  rentPerMonth: string;
  area: string;
  amenities: string[];
  location: string;
}

export interface EventListingData {
  eventDate: string;
  eventTime: string;
  location: string;
  organizer: string;
}

export interface CreatePostPayload {
  content: string;
  category: PostCategory;
  privacy: PostPrivacy;
  media: PostMedia[];
  taggedFriends: string[];
  location?: string;
  marketListing?: MarketListingData;
  roomListing?: RoomListingData;
  eventListing?: EventListingData;
  onUploadProgress?: (mediaId: string, progress: number, status: 'uploading' | 'complete' | 'error', error?: string, uploadedMediaId?: string) => void;
}

export interface Author {
  id: string;
  name: string;
  avatar: string;
  role?: string;
  isVerified?: boolean;
}

export interface CommentAuthor {
  id: string;
  name: string;
  avatar: string;
}

export interface Comment {
  id: string;
  author: CommentAuthor;
  content: string;
  createdAt: string;
  parentId?: string | null;
  imageUrl?: string | null;
}

export interface Post {
  id: string;
  author: Author;
  createdAt: string;
  content: string;
  category: PostCategory;
  privacy: PostPrivacy;
  media?: PostMedia[];
  likesCount: number;
  commentsCount: number;
  isLiked?: boolean;
  comments?: Comment[];
  marketListing?: MarketListingData;
  roomListing?: RoomListingData;
  eventListing?: EventListingData;
}
