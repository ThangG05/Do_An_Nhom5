export type GroupTab = 'market' | 'room' | 'event';

export type ItemStatus = 'available' | 'sold' | 'rented';

export type EventUserStatus = 'going' | 'interested' | null;

export interface MarketItem {
  id: string;
  title: string;
  price: string;
  originalPrice?: string;
  condition: 'Brand New' | 'Like New' | 'Used';
  location: string;
  sellerName: string;
  sellerAvatar: string;
  sellerPhone?: string;
  image: string;
  category: string;
  status: ItemStatus;
  createdAt: string;
}

export interface RoomItem {
  id: string;
  title: string;
  rentPerMonth: string;
  area: string;
  address: string;
  distanceToSchool: string;
  amenities: string[];
  status: ItemStatus;
  landlordName: string;
  landlordPhone: string;
  image: string;
  createdAt: string;
}

export interface EventItem {
  id: string;
  title: string;
  day: string;
  month: string;
  time: string;
  location: string;
  organizer: string;
  coverImage: string;
  goingCount: number;
  interestedCount: number;
  userStatus: EventUserStatus;
  createdAt: string;
}

export interface GroupHeaderData {
  id: string;
  title: string;
  description: string;
  bannerImage: string;
  avatarImage: string;
  memberCount: number;
  postCount: number;
  isJoined: boolean;
}
