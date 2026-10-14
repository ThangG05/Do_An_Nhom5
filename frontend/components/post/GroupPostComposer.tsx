"use client";

import type { ApiGroup, GroupPost } from '@/types/group-api';
import { useCreatePost } from '@/hooks/useCreatePost';
import { createProfilePost } from '@/lib/api';
import { categoryForGroup } from '@/lib/group-post';
import CreatePostModal from './CreatePostModal';
import { CategoryIcon } from './PostCategoryDetails';
import styles from './GroupPost.module.css';

export default function GroupPostComposer({ group, onSubmitted }: { group: ApiGroup; onSubmitted: (post: GroupPost) => void }) {
  const state = useCreatePost(async payload => {
    const post = await createProfilePost(payload, group.id);
    onSubmitted(post as GroupPost);
    return post;
  });
  const category = categoryForGroup(group.slug);
  return <><section className={styles.composer} data-category={category}><span className={styles.iconTile}><CategoryIcon category={category} size={26} /></span><div><strong>Bạn muốn chia sẻ gì với {group.name}?</strong><p>Thêm thông tin, xem trước và gửi bài để quản trị viên duyệt.</p></div><button type="button" className={styles.primary} onClick={() => state.openModal(category)}>＋ Tạo bài viết</button></section><CreatePostModal postState={state} group={group} /></>;
}
