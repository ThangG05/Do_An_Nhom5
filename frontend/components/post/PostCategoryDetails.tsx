import type { Post } from '@/types/post';
import { GROUP_POST_KINDS, formatPostPrice } from '@/lib/group-post';
import { IconMarket, IconEvent, IconHousing } from '@/components/ui/Icons';
import styles from './GroupPost.module.css';

export function CategoryIcon({ category, size = 22 }: { category: string; size?: number }) {
  if (category === 'market') return <IconMarket size={size} />;
  if (category === 'event') return <IconEvent size={size} />;
  if (category === 'roommate') return <IconHousing size={size} />;
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M12 5c-3-2-7-2-9-1v15c3-1 6-1 9 1 3-2 6-2 9-1V4c-2-1-6-1-9 1Zm0 0v15" /></svg>;
}

export default function PostCategoryDetails({ post }: { post: Pick<Post, 'category' | 'marketListing' | 'roomListing' | 'eventListing' | 'studyListing' | 'media' | 'location'> }) {
  const kind = GROUP_POST_KINDS.find(item => item.category === post.category);
  if (!kind) return null;
  const title = post.marketListing?.productName || post.eventListing?.eventName || post.studyListing?.subjectName;
  const place = post.marketListing?.location || post.roomListing?.location || post.eventListing?.location;
  const event = post.eventListing;
  const date = event?.eventDate && /^\d{4}-\d{2}-\d{2}$/.test(event.eventDate) ? event.eventDate.split('-').reverse().join('/') : event?.eventDate;
  const fileCount = post.media?.filter(item => item.type === 'file').length || 0;
  return <div className={styles.postDetails} data-category={post.category}>
    <span className={styles.categoryBadge}><CategoryIcon category={post.category} size={16} />{kind.label}</span>
    {title && <h3>{title}</h3>}
    {post.marketListing?.price && <strong className={styles.price}>{formatPostPrice(post.marketListing.price)}</strong>}
    {post.roomListing?.rentPerMonth && <strong className={styles.price}>{formatPostPrice(post.roomListing.rentPerMonth, true)}</strong>}
    {event && (date || event.eventTime) && <div className={styles.detailLine}><CategoryIcon category="event" size={16} /><span>{date}{date && event.eventTime && ' · '}{event.eventTime}{event.eventTime && ' (giờ Việt Nam)'}</span></div>}
    {place && !post.location && <div className={styles.detailLine}><span aria-hidden="true">⌖</span>{place}</div>}
    {post.category === 'study' && fileCount > 0 && <span className={styles.fileCount}>{fileCount} tài liệu đính kèm</span>}
  </div>;
}
