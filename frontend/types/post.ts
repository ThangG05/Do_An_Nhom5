export type PostCategory = 'general' | 'market' | 'roommate' | 'event' | 'study';

export type PostPrivacy = 'public' | 'friends';

export interface PostMedia {
  id: string;
  url: string;
  type: 'image' | 'video';
  name?: string;
  size?: number;
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
