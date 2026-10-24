"use client";

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { fetchPost } from '@/lib/api';
import { originalPostPath } from '@/lib/post-share';
import styles from './post-permalink.module.css';

export default function PostPermalink({ id }: { id: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    const resolveOriginal = async () => {
      let currentId = id;
      const seen = new Set<string>();
      for (let depth = 0; depth < 8; depth += 1) {
        if (seen.has(currentId)) throw new Error('Liên kết bài viết không hợp lệ.');
        seen.add(currentId);
        const result = await fetchPost(currentId);
        if (!result.sharedPostId) return result;
        currentId = result.sharedPostId;
      }
      throw new Error('Liên kết bài viết không hợp lệ.');
    };
    void resolveOriginal().then(result => {
      if (active) router.replace(originalPostPath(result));
    })
      .catch(cause => {
        if (active) {
          setError(cause instanceof Error ? cause.message : 'Không thể mở bài viết.');
          setLoading(false);
        }
      });
    return () => { active = false; };
  }, [id, router]);
  return <main className={styles.page}>
    <Link href="/home" className={styles.back}>‹ Về bảng tin</Link>
    <header><span>HVNH HUB</span><h1>Đang mở bài viết gốc</h1></header>
    {loading && <p className={styles.state}>Đang chuyển tới nơi đăng bài viết…</p>}
    {!loading && error && <div className={styles.state} role="alert"><strong>Không thể xem bài viết</strong><p>{error}</p><small>Bài có thể đã bị xóa, chưa được duyệt hoặc bạn chưa có quyền xem.</small></div>}
  </main>;
}
