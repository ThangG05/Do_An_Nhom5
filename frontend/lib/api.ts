import { UserProfile, UserFriend, UserPhoto, UserListing, FriendshipStatus } from '@/types/user';
import { Post, CreatePostPayload } from '@/types/post';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function api<T>(endpoint: string, options?: RequestInit): Promise<T> {
  try {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });
    if (!res.ok) {
      throw new Error(`API error: ${res.statusText}`);
    }
    return await res.json();
  } catch (error) {
    console.warn(`[API] Fallback for ${endpoint}:`, error);
    throw error;
  }
}

// Mock Data Generators for rich offline & demo capability
export const CURRENT_USER_MOCK: UserProfile = {
  id: 'user-me',
  name: 'Trần Nguyễn Phương Thảo',
  username: 'phuongthao_hvnh',
  avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80',
  coverBanner: 'https://images.unsplash.com/photo-1541339907198-e08756dedf3f?auto=format&fit=crop&w=1200&q=80',
  bio: 'Sinh viên năm 3 K25 - Khoa Tài Chính - HVNH 🎓 | Đam mê nghiên cứu fintech & nhiếp ảnh 📸',
  pronouns: 'she/her',
  role: 'Sinh viên',
  studentCode: '25A4010188',
  faculty: 'Khoa Tài Chính',
  courseYear: 'K25 (2023 - 2027)',
  workplace: 'Đại sứ truyền thông HVNH Hub',
  education: 'Học viện Ngân hàng (BAV)',
  currentCity: 'Hà Nội',
  hometown: 'Thái Bình',
  joinedDate: 'Tháng 9 năm 2023',
  email: 'thaotnp.k25@hvnh.edu.vn',
  phone: '0987 *** 321',
  gender: 'Nữ',
  birthDate: '15/10/2004',
  relationshipStatus: 'Độc thân',
  isVerified: true,
  isOnline: true,
  friendsCount: 482,
  followersCount: 1250,
  mutualFriendsCount: 0,
  mutualFriendsAvatars: [],
  friendshipStatus: 'self',
  socialLinks: {
    facebook: 'https://facebook.com/phuongthao.hvnh',
    instagram: 'https://instagram.com/thao.fintech',
    linkedin: 'https://linkedin.com/in/phuongthao-hvnh',
    github: 'https://github.com/phuongthao-dev',
  },
};

export const VISITOR_USER_MOCK: UserProfile = {
  id: 'user-102',
  name: 'Nguyễn Văn Hải',
  username: 'hai_finance',
  avatar: 'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=400&q=80',
  coverBanner: 'https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&w=1200&q=80',
  bio: 'Sinh viên K24 - Khoa Ngân Hàng | Chủ tịch CLB Chứng Khoán HVNH 📈',
  pronouns: 'he/him',
  role: 'Sinh viên',
  studentCode: '24A4020099',
  faculty: 'Khoa Ngân Hàng',
  courseYear: 'K24 (2022 - 2026)',
  workplace: 'Chủ tịch CLB Chứng Khoán BAV',
  education: 'Học viện Ngân hàng (BAV)',
  currentCity: 'Hà Nội',
  hometown: 'Nam Định',
  joinedDate: 'Tháng 10 năm 2022',
  email: 'hainv.k24@hvnh.edu.vn',
  isVerified: true,
  isOnline: true,
  friendsCount: 610,
  followersCount: 2340,
  mutualFriendsCount: 34,
  mutualFriendsAvatars: [
    'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=100&q=80',
    'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=100&q=80',
    'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=crop&w=100&q=80',
  ],
  friendshipStatus: 'none',
  socialLinks: {
    facebook: 'https://facebook.com/hai.bav',
    linkedin: 'https://linkedin.com/in/hai-finance',
  },
};

export const MOCK_FRIENDS: UserFriend[] = [
  {
    id: 'friend-1',
    name: 'Lê Minh Anh',
    username: 'minhanh_k25',
    avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=200&q=80',
    mutualCount: 42,
    isOnline: true,
    role: 'Sinh viên',
    faculty: 'Khoa Kế Toán',
    friendshipStatus: 'friends',
  },
  {
    id: 'friend-2',
    name: 'Phạm Đức Hoàng',
    username: 'hoang_bav',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80',
    mutualCount: 28,
    isOnline: false,
    role: 'Sinh viên',
    faculty: 'Khoa Hệ thống thông tin',
    friendshipStatus: 'friends',
  },
  {
    id: 'friend-3',
    name: 'Đỗ Thị Khánh Linh',
    username: 'linh_khanh',
    avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=crop&w=200&q=80',
    mutualCount: 56,
    isOnline: true,
    role: 'Sinh viên',
    faculty: 'Khoa Kinh Tế',
    friendshipStatus: 'friends',
  },
  {
    id: 'friend-4',
    name: 'Vũ Hoàng Nam',
    username: 'nam_vu',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=200&q=80',
    mutualCount: 19,
    isOnline: false,
    role: 'Sinh viên',
    faculty: 'Khoa Tài Chính',
    friendshipStatus: 'friends',
  },
  {
    id: 'friend-5',
    name: 'Hoàng Ngọc Hà',
    username: 'ngocha_bav',
    avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=200&q=80',
    mutualCount: 31,
    isOnline: true,
    role: 'Sinh viên',
    faculty: 'Khoa Ngôn Ngữ Anh',
    friendshipStatus: 'friends',
  },
  {
    id: 'friend-6',
    name: 'Bùi Quang Huy',
    username: 'huy_bui',
    avatar: 'https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?auto=format&fit=crop&w=200&q=80',
    mutualCount: 15,
    isOnline: false,
    role: 'Sinh viên',
    faculty: 'Khoa Ngân Hàng',
    friendshipStatus: 'friends',
  },
  {
    id: 'friend-7',
    name: 'Nguyễn Thảo Nhi',
    username: 'thaonhi_25',
    avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=200&q=80',
    mutualCount: 22,
    isOnline: true,
    role: 'Sinh viên',
    faculty: 'Khoa Quản Trị Kinh Doanh',
    friendshipStatus: 'friends',
  },
  {
    id: 'friend-8',
    name: 'Trần Gia Bảo',
    username: 'giabao_bav',
    avatar: 'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&w=200&q=80',
    mutualCount: 37,
    isOnline: false,
    role: 'Sinh viên',
    faculty: 'Khoa Tài Chính',
    friendshipStatus: 'friends',
  },
  {
    id: 'friend-9',
    name: 'Đặng Mai Phương',
    username: 'maiphuong_phuong',
    avatar: 'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=200&q=80',
    mutualCount: 12,
    isOnline: true,
    role: 'Sinh viên',
    faculty: 'Khoa Kinh Doanh Quốc Tế',
    friendshipStatus: 'friends',
  },
];

export const MOCK_PHOTOS: UserPhoto[] = [
  {
    id: 'photo-1',
    url: 'https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=600&q=80',
    caption: 'Kỷ niệm khai giảng năm học mới HVNH 🎓✨',
    createdAt: '2 ngày trước',
    likesCount: 124,
    albumName: 'Hoạt động trường',
  },
  {
    id: 'photo-2',
    url: 'https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=600&q=80',
    caption: 'Thư viện Học viện Ngân hàng chiều thu 📚🍂',
    createdAt: '1 tuần trước',
    likesCount: 89,
    albumName: 'Góc BAV',
  },
  {
    id: 'photo-3',
    url: 'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=600&q=80',
    caption: 'Buổi thảo luận nhóm bài tập lớn Fintech 💻🚀',
    createdAt: '2 tuần trước',
    likesCount: 65,
    albumName: 'Học tập',
  },
  {
    id: 'photo-4',
    url: 'https://images.unsplash.com/photo-1529156069898-49953e39b3ac?auto=format&fit=crop&w=600&q=80',
    caption: 'Hội thao sinh viên HVNH 2026 🎉🏅',
    createdAt: '3 tuần trước',
    likesCount: 142,
    albumName: 'Hoạt động trường',
  },
  {
    id: 'photo-5',
    url: 'https://images.unsplash.com/photo-1543269865-cbf427effbad?auto=format&fit=crop&w=600&q=80',
    caption: 'Coffee workshop cùng CLB Nghiên cứu khoa học ☕📈',
    createdAt: '1 tháng trước',
    likesCount: 98,
    albumName: 'CLB & Sự kiện',
  },
  {
    id: 'photo-6',
    url: 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?auto=format&fit=crop&w=600&q=80',
    caption: 'Gala Chào tân sinh viên BAV 🌟🎶',
    createdAt: '1 tháng trước',
    likesCount: 210,
    albumName: 'CLB & Sự kiện',
  },
  {
    id: 'photo-7',
    url: 'https://images.unsplash.com/photo-1511632765486-a01980e01a18?auto=format&fit=crop&w=600&q=80',
    caption: 'Dã ngoại cùng đội Đại sứ truyền thông 🌳🌸',
    createdAt: '2 tháng trước',
    likesCount: 176,
    albumName: 'Kỷ niệm',
  },
  {
    id: 'photo-8',
    url: 'https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?auto=format&fit=crop&w=600&q=80',
    caption: 'Góc tự học tầng 4 Nhà D BAV 📖💡',
    createdAt: '2 tháng trước',
    likesCount: 84,
    albumName: 'Góc BAV',
  },
  {
    id: 'photo-9',
    url: 'https://images.unsplash.com/photo-1524178232363-1fb2b075b655?auto=format&fit=crop&w=600&q=80',
    caption: 'Seminar Xu hướng Ngân hàng Số 2026 🏢🌐',
    createdAt: '3 tháng trước',
    likesCount: 115,
    albumName: 'Học tập',
  },
];

export const MOCK_LISTINGS: UserListing[] = [
  {
    id: 'list-1',
    title: 'Pass lại Giáo trình Tài chính Doanh nghiệp (Tái bản mới nhất)',
    category: 'market',
    price: '45.000đ',
    location: 'Cổng chính Học viện Ngân hàng',
    status: 'active',
    imageUrl: 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=500&q=80',
    createdAt: 'Hôm qua',
    description: 'Sách còn mới 95%, đã highlight các phần quan trọng cho kỳ thi.',
  },
  {
    id: 'list-2',
    title: 'Tìm bạn nữ ở ghép phòng chung cư mini 35m² ngõ 12 Chùa Bộc',
    category: 'roommate',
    price: '2.200.000đ/tháng',
    location: 'Ngõ 12 Chùa Bộc (cách BAV 300m)',
    status: 'active',
    imageUrl: 'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=500&q=80',
    createdAt: '3 ngày trước',
    description: 'Phòng đầy đủ điều hòa, nóng lạnh, ban công thoáng mát, tự do giờ giấc.',
  },
  {
    id: 'list-3',
    title: 'Pass Máy tính Casio FX-580VN X chính hãng tem BITEX',
    category: 'market',
    price: '380.000đ',
    location: 'Ký túc xá HVNH',
    status: 'sold',
    imageUrl: 'https://images.unsplash.com/photo-1587145820266-a5951ee6f620?auto=format&fit=crop&w=500&q=80',
    createdAt: '1 tuần trước',
    description: 'Dùng tốt cho môn Lý thuyết xác suất & Kinh tế lượng.',
  },
  {
    id: 'list-4',
    title: 'Workshop: Định hướng nghề nghiệp & Skill set cho Sinh viên Fintech',
    category: 'event',
    price: 'Miễn phí',
    location: 'Hội trường D2 - Học viện Ngân hàng',
    status: 'active',
    imageUrl: 'https://images.unsplash.com/photo-1475721027785-f74eccf877e2?auto=format&fit=crop&w=500&q=80',
    createdAt: '2 tuần trước',
    description: 'Sự kiện do CLB phối hợp cùng Khoa Tài chính tổ chức.',
  },
];

export const MOCK_POSTS: Post[] = [
  {
    id: 'post-p1',
    author: {
      id: CURRENT_USER_MOCK.id,
      name: CURRENT_USER_MOCK.name,
      avatar: CURRENT_USER_MOCK.avatar,
      role: CURRENT_USER_MOCK.role,
      isVerified: CURRENT_USER_MOCK.isVerified,
    },
    createdAt: '3 giờ trước',
    content: 'Vừa hoàn thành xong slide báo cáo Nghiên cứu khoa học cấp Học viện! Cảm ơn cả team Khoa Tài Chính đã nỗ lực cùng nhau suốt 2 tháng qua. Hẹn gặp mọi người tại vòng Chung kết tuần sau nha 🎉🎓🚀',
    category: 'general',
    privacy: 'public',
    media: [
      {
        id: 'pm-1',
        url: 'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=800&q=80',
        type: 'image',
      },
    ],
    likesCount: 84,
    commentsCount: 19,
    isLiked: true,
  },
  {
    id: 'post-p2',
    author: {
      id: CURRENT_USER_MOCK.id,
      name: CURRENT_USER_MOCK.name,
      avatar: CURRENT_USER_MOCK.avatar,
      role: CURRENT_USER_MOCK.role,
      isVerified: CURRENT_USER_MOCK.isVerified,
    },
    createdAt: '2 ngày trước',
    content: 'Mình cần pass gấp bộ giáo trình Kinh tế vĩ mô & Vi mô còn mới 98%. Bạn nào cần ôn thi học kỳ này ib mình ngay nhé, giá hạt dẻ cho sinh viên K26-K27 ạ! 📚✨',
    category: 'market',
    privacy: 'public',
    marketListing: {
      price: '45.000đ',
      condition: 'Mới 95%',
      location: 'Cổng trường Chùa Bộc',
    },
    media: [
      {
        id: 'pm-2',
        url: 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=800&q=80',
        type: 'image',
      },
    ],
    likesCount: 42,
    commentsCount: 7,
    isLiked: false,
  },
  {
    id: 'post-p3',
    author: {
      id: CURRENT_USER_MOCK.id,
      name: CURRENT_USER_MOCK.name,
      avatar: CURRENT_USER_MOCK.avatar,
      role: CURRENT_USER_MOCK.role,
      isVerified: CURRENT_USER_MOCK.isVerified,
    },
    createdAt: '1 tuần trước',
    content: 'Góc tự học tầng 4 Thư viện BAV hôm nay yên tĩnh quá. Tiết trời Hà Nội mùa thu thật thích hợp để cày deadline! ☕🍁📖',
    category: 'study',
    privacy: 'friends',
    media: [
      {
        id: 'pm-3',
        url: 'https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=800&q=80',
        type: 'image',
      },
    ],
    likesCount: 112,
    commentsCount: 24,
    isLiked: true,
  },
];

// API Functions Implementation
export async function fetchUserProfile(userId?: string): Promise<UserProfile> {
  if (!userId || userId === 'user-me' || userId === 'me') {
    return CURRENT_USER_MOCK;
  }
  try {
    return await api<UserProfile>(`/users/${userId}`);
  } catch {
    return {
      ...VISITOR_USER_MOCK,
      id: userId,
      name: userId === '102' ? 'Nguyễn Văn Hải' : `Sinh viên ${userId}`,
    };
  }
}

export async function updateUserProfile(data: Partial<UserProfile>): Promise<UserProfile> {
  try {
    return await api<UserProfile>('/users/me', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  } catch {
    Object.assign(CURRENT_USER_MOCK, data);
    return { ...CURRENT_USER_MOCK };
  }
}

export async function fetchUserPosts(userId: string, filter?: string): Promise<Post[]> {
  try {
    return await api<Post[]>(`/users/${userId}/posts?filter=${filter || 'all'}`);
  } catch {
    if (filter === 'market') {
      return MOCK_POSTS.filter((p) => p.category === 'market');
    }
    return MOCK_POSTS;
  }
}

export async function fetchUserFriends(userId: string, query?: string): Promise<UserFriend[]> {
  try {
    return await api<UserFriend[]>(`/users/${userId}/friends?q=${encodeURIComponent(query || '')}`);
  } catch {
    let friends = MOCK_FRIENDS;
    if (query) {
      const q = query.toLowerCase();
      friends = friends.filter(
        (f) => f.name.toLowerCase().includes(q) || f.username.toLowerCase().includes(q)
      );
    }
    return friends;
  }
}

export async function fetchUserPhotos(userId: string): Promise<UserPhoto[]> {
  try {
    return await api<UserPhoto[]>(`/users/${userId}/photos`);
  } catch {
    return MOCK_PHOTOS;
  }
}

export async function fetchUserListings(userId: string, category?: string): Promise<UserListing[]> {
  try {
    return await api<UserListing[]>(`/users/${userId}/listings?category=${category || 'all'}`);
  } catch {
    if (category && category !== 'all') {
      return MOCK_LISTINGS.filter((l) => l.category === category);
    }
    return MOCK_LISTINGS;
  }
}

export async function updateFriendshipStatus(
  targetUserId: string,
  action: 'add' | 'accept' | 'reject' | 'unfriend' | 'cancel'
): Promise<{ status: FriendshipStatus }> {
  try {
    return await api<{ status: FriendshipStatus }>(`/users/${targetUserId}/friendship`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    });
  } catch {
    const statusMap: Record<string, FriendshipStatus> = {
      add: 'pending_sent',
      accept: 'friends',
      reject: 'none',
      unfriend: 'none',
      cancel: 'none',
    };
    return { status: statusMap[action] || 'none' };
  }
}

export async function createProfilePost(payload: CreatePostPayload): Promise<Post> {
  try {
    return await api<Post>('/posts', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  } catch {
    const newPost: Post = {
      id: `post-new-${Date.now()}`,
      author: {
        id: CURRENT_USER_MOCK.id,
        name: CURRENT_USER_MOCK.name,
        avatar: CURRENT_USER_MOCK.avatar,
        role: CURRENT_USER_MOCK.role,
        isVerified: CURRENT_USER_MOCK.isVerified,
      },
      createdAt: 'Vừa xong',
      content: payload.content,
      category: payload.category,
      privacy: payload.privacy,
      media: payload.media,
      likesCount: 0,
      commentsCount: 0,
      isLiked: false,
    };
    MOCK_POSTS.unshift(newPost);
    return newPost;
  }
}
