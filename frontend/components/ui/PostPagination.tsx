"use client";

import styles from './PostPagination.module.css';

export interface PostPaginationProps {
  page: number; loading: boolean; error: string; hasNext: boolean;
  previous: () => void; next: () => void; reload: () => void;
}

export default function PostPagination({ page, loading, error, hasNext, previous, next, reload }: PostPaginationProps) {
  return <div className={styles.wrapper}>
    {error && <p role="alert">{error} <button type="button" onClick={reload} disabled={loading}>Thử lại</button></p>}
    <nav className={styles.controls} aria-label="Phân trang bài viết" aria-busy={loading}>
      <button type="button" disabled={page === 0 || loading} onClick={previous}>Trang trước</button>
      <span aria-live="polite">{loading ? 'Đang tải…' : `Trang ${page + 1}`}</span>
      <button type="button" disabled={!hasNext || loading} onClick={next}>Trang sau</button>
    </nav>
  </div>;
}
