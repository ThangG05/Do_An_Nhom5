"use client";

import { useCallback, useEffect, useRef, useState } from 'react';

export const POST_PAGE_SIZE = 10;

/** Fetch one page plus a lookahead row. Never display data from an old scope. */
export function usePostPage<T>(key: string, fetchPage: (limit: number, offset: number) => Promise<T[]>, enabled = true) {
  const [position, setPosition] = useState({ key, page: 0 });
  const [result, setResult] = useState<{ key: string; page: number; items: T[]; hasNext: boolean }>({ key: '', page: 0, items: [], hasNext: false });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  const request = useRef(0);
  const page = position.key === key ? position.page : 0;
  const current = enabled && result.key === key && result.page === page;
  useEffect(() => {
    const id = ++request.current;
    setPosition(previous => previous.key === key ? previous : { key, page: 0 });
    setError('');
    if (!enabled) { setLoading(false); return; }
    setLoading(true);
    fetchPage(POST_PAGE_SIZE + 1, page * POST_PAGE_SIZE).then(rows => {
      if (request.current !== id) return;
      // Deleting the final row on the last page returns to the previous page.
      if (!rows.length && page > 0) { setPosition({ key, page: page - 1 }); return; }
      setResult({ key, page, items: rows.slice(0, POST_PAGE_SIZE), hasNext: rows.length > POST_PAGE_SIZE });
    }).catch(reason => {
      if (request.current === id) setError(reason instanceof Error ? reason.message : 'Không thể tải bài viết.');
    }).finally(() => { if (request.current === id) setLoading(false); });
    return () => { request.current++; };
  }, [key, page, fetchPage, enabled, revision]);
  const reload = useCallback(() => setRevision(value => value + 1), []);
  return {
    items: current ? result.items : [], page, loading, error,
    hasNext: current && result.hasNext, reload,
    previous: () => setPosition({ key, page: Math.max(0, page - 1) }),
    next: () => { if (current && result.hasNext && !loading) setPosition({ key, page: page + 1 }); },
  };
}
