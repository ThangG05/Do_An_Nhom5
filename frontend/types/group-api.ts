import type { Post } from '@/types/post';

export type GroupMembership = 'NONE' | 'PENDING' | 'MEMBER' | 'ADMIN';

export interface ApiGroup {
  id: string;
  name: string;
  slug: string;
  description: string;
  member_count: number;
  membership: GroupMembership;
}

export interface GroupJoinRequest {
  id: string;
  user_id: string;
  name: string;
  username: string;
  created_at: string;
}

export interface GroupMember {
  id: string;
  name: string;
  username: string;
  role: 'MEMBER' | 'ADMIN';
  student_code?: string | null;
}

export type GroupPost = Post & {
  groupId: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  rejectionReason: string | null;
  isPinned: boolean;
};
