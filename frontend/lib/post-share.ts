const POST_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

import type { Post } from '@/types/post';

export function originalPostPath(post: Pick<Post, 'id' | 'groupId' | 'author'>): string {
  const query = `post=${encodeURIComponent(post.id)}`;
  return post.groupId
    ? `/groups?group=${encodeURIComponent(post.groupId)}&${query}`
    : `/profile/${encodeURIComponent(post.author.id)}?${query}`;
}

export function postPath(postId: string): string {
  return `/posts/${encodeURIComponent(postId)}`;
}

export function sharedPostPath(url: string): string | null {
  try {
    const parsed = new URL(url);
    if (!['http:', 'https:'].includes(parsed.protocol)) return null;
    const match = /^\/posts\/([^/]+)\/?$/.exec(parsed.pathname);
    const id = match ? decodeURIComponent(match[1]) : '';
    return POST_ID.test(id) ? postPath(id) : null;
  } catch {
    return null;
  }
}

export function sharedPostIdFromText(content: string): string | null {
  for (const match of content.matchAll(/https?:\/\/[^\s<>]+/g)) {
    const path = sharedPostPath(match[0].replace(/[.,!?;)]+$/, ''));
    if (path) return path.slice('/posts/'.length);
  }
  return null;
}

export function shareCaption(content: string): string {
  return content.replace(/https?:\/\/[^\s<>]+/g, candidate => {
    const suffix = candidate.match(/[.,!?;)]+$/)?.[0] || '';
    return sharedPostPath(candidate.slice(0, candidate.length - suffix.length)) ? suffix : candidate;
  }).trim();
}
