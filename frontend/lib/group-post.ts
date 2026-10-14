import type { CreatePostPayload, PostCategory } from '@/types/post';

export const GROUP_POST_KINDS = [
  { category: 'market', slug: 'pass-do', label: 'Pass đồ', description: 'Trao lại món đồ, gửi thêm giá trị.', icon: 'bag' },
  { category: 'event', slug: 'su-kien', label: 'Sự kiện', description: 'Hẹn nhau ở những trải nghiệm mới.', icon: 'calendar' },
  { category: 'roommate', slug: 'ghep-phong-tim-tro', label: 'Ghép phòng', description: 'Tìm nơi ở, kết nối bạn cùng phòng.', icon: 'home' },
  { category: 'study', slug: 'hoc-tap', label: 'Học tập', description: 'Chia sẻ kiến thức, cùng tiến bộ.', icon: 'book' },
] as const;

export type PostFieldErrors = Record<string, string>;
export type PostDraft = Pick<CreatePostPayload, 'category' | 'content' | 'marketListing' | 'roomListing' | 'eventListing' | 'studyListing'>;

export function validatePostDraft(draft: PostDraft, mediaCount: number): PostFieldErrors {
  const errors: PostFieldErrors = {};
  const required = (key: string, value: string | undefined, label: string) => {
    if (!value?.trim()) errors[key] = `Vui lòng nhập ${label}.`;
  };
  const price = (key: string, value: string | undefined, optional = false) => {
    if (optional && !value?.trim()) return;
    if (!/^[0-9]{1,15}$/.test(value?.trim() || '')) errors[key] = 'Nhập số tiền VNĐ không âm, tối đa 15 chữ số.';
  };
  if (draft.category === 'market') {
    required('productName', draft.marketListing?.productName, 'tên vật phẩm');
    price('price', draft.marketListing?.price);
    required('location', draft.marketListing?.location, 'vị trí giao dịch');
  }
  if (draft.category === 'event') {
    required('eventName', draft.eventListing?.eventName, 'tên sự kiện');
    required('eventDate', draft.eventListing?.eventDate, 'ngày diễn ra');
    required('eventTime', draft.eventListing?.eventTime, 'giờ bắt đầu');
    if (draft.eventListing?.eventDate) {
      const value = draft.eventListing.eventDate;
      const parsed = new Date(`${value}T00:00:00Z`);
      if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== value) errors.eventDate = 'Ngày diễn ra không hợp lệ.';
    }
    if (draft.eventListing?.eventTime && !/^([01]\d|2[0-3]):[0-5]\d$/.test(draft.eventListing.eventTime)) errors.eventTime = 'Giờ bắt đầu không hợp lệ.';
    required('location', draft.eventListing?.location, 'địa điểm sự kiện');
  }
  if (draft.category === 'roommate') {
    price('rentPerMonth', draft.roomListing?.rentPerMonth, true);
    required('location', draft.roomListing?.location, 'vị trí phòng');
  }
  if (draft.category === 'study') required('subjectName', draft.studyListing?.subjectName, 'tên môn học');
  if (['event', 'roommate', 'study'].includes(draft.category)) required('content', draft.content, 'nội dung mô tả');
  if (draft.category === 'general' && !draft.content.trim() && !mediaCount) errors.content = 'Nhập nội dung hoặc thêm tệp đính kèm.';
  if (mediaCount > 10) errors.media = 'Mỗi bài được đính kèm tối đa 10 tệp.';
  return errors;
}

export function formatPostPrice(value?: string, monthly = false) {
  if (!value?.trim()) return '';
  if (!/^\d+$/.test(value.trim())) return value; // Existing free-text prices stay readable.
  if (value.trim() === '0') return monthly ? 'Miễn phí' : 'Tặng miễn phí';
  return `${new Intl.NumberFormat('vi-VN').format(Number(value))} đ${monthly ? '/tháng' : ''}`;
}

export function categoryForGroup(slug: string): PostCategory {
  return GROUP_POST_KINDS.find(kind => kind.slug === slug)?.category || 'general';
}
