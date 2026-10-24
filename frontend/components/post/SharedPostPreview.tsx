"use client";

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchPost } from '@/lib/api';
import { originalPostPath, shareCaption } from '@/lib/post-share';
import { safeImageSrc } from '@/lib/media';
import type { Post } from '@/types/post';
import styles from './SharedPostPreview.module.css';

export default function SharedPostPreview({ postId }: { postId: string }) {
  const [post, setPost] = useState<Post | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  useEffect(() => {
    let active = true;
    setPost(null); setUnavailable(false);
    const resolve = async () => {
      let id = postId;
      const seen = new Set<string>();
      for (let depth = 0; depth < 8; depth += 1) {
        if (seen.has(id)) throw new Error('Vòng lặp bài chia sẻ.');
        seen.add(id);
        const result = await fetchPost(id);
        const next = result.sharedPostId;
        if (!next) return result;
        id = next;
      }
      throw new Error('Bài chia sẻ lồng nhau quá sâu.');
    };
    void resolve().then(result => { if (active) setPost(result); })
      .catch(() => { if (active) setUnavailable(true); });
    return () => { active = false; };
  }, [postId]);
  if (unavailable) return <div className={styles.unavailable}>Bài viết gốc không khả dụng hoặc bạn không có quyền xem.</div>;
  if (!post) return <div className={styles.unavailable}>Đang tải bài viết được chia sẻ…</div>;
  const thumbnail = post.media?.find(item => item.type === 'image');
  return <Link href={originalPostPath(post)} className={styles.card} aria-label={`Xem bài viết gốc của ${post.author.name}`}>
    <div className={styles.author}><img src={safeImageSrc(post.author.avatar)} alt="" /><span><strong>{post.author.name}</strong><small>{post.groupName ? `Trong nhóm ${post.groupName}` : 'Bài viết cá nhân'}</small></span><b aria-hidden="true">↗</b></div>
    {(post.sharedPostId ? shareCaption(post.content) : post.content) && <p>{post.sharedPostId ? shareCaption(post.content) : post.content}</p>}
    {thumbnail && <img className={styles.thumbnail} src={safeImageSrc(thumbnail.url)} alt="Ảnh trong bài viết được chia sẻ" loading="lazy" />}
  </Link>;
}
