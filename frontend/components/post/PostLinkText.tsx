import Link from 'next/link';
import { sharedPostPath } from '@/lib/post-share';

const URL_PATTERN = /https?:\/\/[^\s<>]+/g;

export default function PostLinkText({ content }: { content: string }) {
  const pieces: React.ReactNode[] = [];
  let cursor = 0;
  for (const match of content.matchAll(URL_PATTERN)) {
    const start = match.index ?? 0;
    if (start > cursor) pieces.push(content.slice(cursor, start));
    const candidate = match[0].replace(/[.,!?;)]+$/, '');
    const path = sharedPostPath(candidate);
    if (path) {
      pieces.push(<Link key={`${start}-${path}`} href={path} className="shared-post-inline-link">Xem bài viết gốc ↗</Link>);
      if (candidate.length < match[0].length) pieces.push(match[0].slice(candidate.length));
    } else {
      pieces.push(match[0]);
    }
    cursor = start + match[0].length;
  }
  if (cursor < content.length) pieces.push(content.slice(cursor));
  return <>{pieces.length ? pieces : content}</>;
}
