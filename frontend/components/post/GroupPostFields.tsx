"use client";

import type { ReactNode } from 'react';
import type { UseCreatePostReturn } from '@/hooks/useCreatePost';
import type { PostFieldErrors } from '@/lib/group-post';
import styles from './GroupPost.module.css';

export type GroupFieldState = Pick<UseCreatePostReturn, 'category' | 'content' | 'setContent' | 'marketListing' | 'setMarketListing' | 'roomListing' | 'setRoomListing' | 'eventListing' | 'setEventListing' | 'studyListing' | 'setStudyListing' | 'location' | 'setLocation'>;

function Field({ name, label, required, errors, children, hint }: { name: string; label: string; required?: boolean; errors: PostFieldErrors; children: ReactNode; hint?: string }) {
  return <div className={styles.field}>
    <label htmlFor={`gp-${name}`}>{label} {required ? <span className={styles.required}>*</span> : <small>(Tùy chọn)</small>}</label>
    {children}
    {errors[name] ? <small id={`gp-${name}-error`} className={styles.error}>{errors[name]}</small> : hint && <small className={styles.hint}>{hint}</small>}
  </div>;
}

export default function GroupPostFields({ state: s, errors = {}, onPickLocation }: { state: GroupFieldState; errors?: PostFieldErrors; onPickLocation: () => void }) {
  const attrs = (key: string) => ({ id: `gp-${key}`, 'aria-invalid': !!errors[key], 'aria-describedby': errors[key] ? `gp-${key}-error` : undefined });
  const place = s.category === 'market' ? s.marketListing.location : s.category === 'event' ? s.eventListing.location : s.roomListing.location;
  const setPlace = (value: string) => {
    s.setLocation(value.trim() ? { name: value } : null); // Manual edits invalidate old coordinates.
    if (s.category === 'market') s.setMarketListing(previous => ({ ...previous, location: value }));
    if (s.category === 'event') s.setEventListing(previous => ({ ...previous, location: value }));
    if (s.category === 'roommate') s.setRoomListing(previous => ({ ...previous, location: value }));
  };
  return <div className={styles.fields}>
    {s.category === 'market' && <Field name="productName" label="Tên vật phẩm" required errors={errors}><input {...attrs('productName')} maxLength={200} placeholder="VD: Bàn phím Keychron K6" value={s.marketListing.productName || ''} onChange={e => s.setMarketListing(p => ({ ...p, productName: e.target.value }))} /></Field>}
    {s.category === 'event' && <Field name="eventName" label="Tên sự kiện" required errors={errors}><input {...attrs('eventName')} maxLength={200} placeholder="VD: Movie Night — Xem phim & giao lưu" value={s.eventListing.eventName || ''} onChange={e => s.setEventListing(p => ({ ...p, eventName: e.target.value }))} /></Field>}
    {s.category === 'study' && <Field name="subjectName" label="Tên môn học" required errors={errors}><input {...attrs('subjectName')} maxLength={200} placeholder="VD: Giải tích 1" value={s.studyListing.subjectName} onChange={e => s.setStudyListing({ subjectName: e.target.value })} /></Field>}
    <Field name="content" label={s.category === 'market' ? 'Thông tin chi tiết' : s.category === 'event' ? 'Mô tả sự kiện' : s.category === 'study' ? 'Nội dung tài liệu' : s.category === 'roommate' ? 'Thông tin phòng / nhu cầu ở ghép' : 'Nội dung bài viết'} required={['event', 'study', 'roommate'].includes(s.category)} errors={errors}>
      <textarea {...attrs('content')} maxLength={10000} rows={4} value={s.content} onChange={e => s.setContent(e.target.value)} placeholder={s.category === 'market' ? 'Tình trạng, lý do pass, cách liên hệ…' : s.category === 'study' ? 'Giới thiệu tài liệu, nội dung chính và nguồn tham khảo…' : s.category === 'roommate' ? 'Mô tả phòng, số người, tiện ích, yêu cầu ở ghép…' : s.category === 'event' ? 'Hoạt động gì đang chờ đón mọi người?' : 'Bạn muốn chia sẻ điều gì hôm nay?'} />
    </Field>
    {s.category === 'market' && <Field name="price" label="Giá bán (VNĐ)" required errors={errors} hint="Nhập 0 nếu bạn muốn tặng miễn phí."><input {...attrs('price')} inputMode="numeric" maxLength={15} placeholder="VD: 1500000" value={s.marketListing.price} onChange={e => s.setMarketListing(p => ({ ...p, price: e.target.value }))} /></Field>}
    {s.category === 'roommate' && <Field name="rentPerMonth" label="Giá thuê mỗi tháng (VNĐ)" errors={errors} hint="Có thể bỏ qua nếu chưa xác định giá."><input {...attrs('rentPerMonth')} inputMode="numeric" maxLength={15} placeholder="VD: 2500000" value={s.roomListing.rentPerMonth} onChange={e => s.setRoomListing(p => ({ ...p, rentPerMonth: e.target.value }))} /></Field>}
    {s.category === 'event' && <div className={styles.twoFields}>
      <Field name="eventDate" label="Ngày diễn ra" required errors={errors}><input {...attrs('eventDate')} type="date" value={s.eventListing.eventDate} onChange={e => s.setEventListing(p => ({ ...p, eventDate: e.target.value }))} /></Field>
      <Field name="eventTime" label="Giờ bắt đầu" required errors={errors} hint="Giờ Việt Nam (UTC+7)."><input {...attrs('eventTime')} type="time" value={s.eventListing.eventTime} onChange={e => s.setEventListing(p => ({ ...p, eventTime: e.target.value }))} /></Field>
    </div>}
    {['market', 'event', 'roommate'].includes(s.category) && <Field name="location" label="Vị trí" required errors={errors} hint="Nhập tên khu vực hoặc tìm địa điểm / dùng GPS."><div className={styles.locationInput}><input {...attrs('location')} maxLength={255} placeholder="VD: Chùa Bộc, Đống Đa, Hà Nội" value={place} onChange={e => setPlace(e.target.value)} /><button type="button" onClick={onPickLocation} aria-label="Tìm địa điểm hoặc dùng vị trí hiện tại" title="Tìm địa điểm / GPS">⌖</button></div></Field>}
  </div>;
}
