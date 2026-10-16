"use client";

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchReportDetail, fetchReportQueue, resolveReport } from '@/lib/api';
import { useAuthUser } from '@/components/auth/AuthProvider';
import { safeImageSrc } from '@/lib/media';
import { useDialog } from '@/components/ui/DialogProvider';
import UserAvatar from '@/components/ui/UserAvatar';
import RelativeTime from '@/components/ui/RelativeTime';
import PostCategoryDetails from '@/components/post/PostCategoryDetails';
import type { ApiReport, ReportDetail } from '@/types/report';

const reportTypeLabel = { POST: 'Bài viết', COMMENT: 'Bình luận', USER: 'Tài khoản' } as const;

export default function ReportQueue({ groupId }: { groupId?: string }) {
  const [items, setItems] = useState<ApiReport[]>([]);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<ApiReport | null>(null);
  const [detail, setDetail] = useState<ReportDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState('');
  const dialog = useDialog();
  const superAdmin = useAuthUser()?.system_role === 'SUPER_ADMIN';

  const load = useCallback(async () => {
    try {
      const rows = await fetchReportQueue('OPEN');
      setItems(groupId ? rows.filter(report => report.group_id === groupId) : rows);
      setError('');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không tải được báo cáo.');
    }
  }, [groupId]);
  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    if (!selected) return;
    const onEscape = (event: KeyboardEvent) => { if (event.key === 'Escape') setSelected(null); };
    window.addEventListener('keydown', onEscape);
    return () => window.removeEventListener('keydown', onEscape);
  }, [selected]);

  const openDetail = async (item: ApiReport) => {
    setSelected(item);
    setDetail(null);
    setDetailError('');
    setDetailLoading(true);
    try {
      setDetail(await fetchReportDetail(item.id));
    } catch (cause) {
      setDetailError(cause instanceof Error ? cause.message : 'Không tải được nội dung bị báo cáo.');
    } finally {
      setDetailLoading(false);
    }
  };

  const decide = async (item: ApiReport, decision: 'RESOLVE' | 'REJECT', action: 'NONE' | 'HIDE_CONTENT' | 'LOCK_USER' | 'DISABLE_USER') => {
    const note = await dialog.prompt({
      title: decision === 'REJECT' ? 'Bác bỏ báo cáo' : 'Xác nhận xử lý',
      message: 'Ghi rõ kết quả và căn cứ để người báo cáo có thể theo dõi.',
      placeholder: 'Ghi chú kết quả xử lý...', multiline: true, minLength: 3,
      tone: action === 'DISABLE_USER' ? 'danger' : 'default',
    });
    if (!note) return;
    try {
      const message = await resolveReport(item.id, decision, action, note);
      setSelected(null);
      await load();
      dialog.notify({ title: message, tone: 'success' });
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : 'Không xử lý được báo cáo.';
      setError(message);
      if (selected?.id === item.id) setDetailError(message);
    }
  };

  const actions = (item: ApiReport) => <div className="report-actions">
    <button type="button" onClick={() => void decide(item, 'REJECT', 'NONE')}>Bác bỏ</button>
    {item.target_type !== 'USER' && (selected?.id === item.id && detail && (item.target_type === 'POST' ? !detail.post : !detail.comment)
      ? <button type="button" className="warning" onClick={() => void decide(item, 'RESOLVE', 'NONE')}>Kết thúc · nội dung đã gỡ</button>
      : <button type="button" className="warning" onClick={() => void decide(item, 'RESOLVE', 'HIDE_CONTENT')}>Xác nhận & gỡ nội dung</button>)}
    {superAdmin && item.target_type === 'USER' && <>
      <button type="button" className="warning" onClick={() => void decide(item, 'RESOLVE', 'LOCK_USER')}>Xác nhận & khóa</button>
      <button type="button" className="danger" onClick={() => void decide(item, 'RESOLVE', 'DISABLE_USER')}>Vô hiệu hóa</button>
    </>}
  </div>;

  return <section className="report-queue">
    <header><div><span>REPORT MANAGEMENT</span><h2>Báo cáo vi phạm</h2></div><b>{items.length} đang chờ</b></header>
    <p className="report-scope-note">{groupId ? 'Báo cáo nội dung trong nhóm này do quản trị nhóm xử lý.' : 'Báo cáo tài khoản, nội dung ngoài nhóm và nhóm chưa có quản trị viên.'}</p>
    {error && <div className="admin-error" role="alert">{error}</div>}
    <div className="report-list">{items.map(item => <article key={item.id}>
      <div className="report-copy">
        <div><span className="report-type">{reportTypeLabel[item.target_type]}</span>{item.group_name && <span className="report-group">{item.group_name}</span>}</div>
        <strong>{item.reporter_name} đã báo cáo</strong>
        <small><RelativeTime value={item.created_at} /></small>
        <p className="report-reason"><b>Nội dung báo cáo:</b> {item.reason}</p>
        <button type="button" className="report-target-link" onClick={() => void openDetail(item)} aria-label={`Xem ${reportTypeLabel[item.target_type].toLocaleLowerCase()} bị báo cáo`}>
          <span>{item.target_summary || 'Đối tượng không còn hiển thị'}</span><b>Xem nội dung <span aria-hidden="true">↗</span></b>
        </button>
        {item.evidence_url && <a href={item.evidence_url} target="_blank" rel="noreferrer">Xem minh chứng</a>}
      </div>
      {actions(item)}
    </article>)}{!items.length && !error && <p className="live-empty">Không có báo cáo đang chờ xử lý.</p>}</div>

    {selected && <div className="report-detail-backdrop" onClick={() => setSelected(null)}>
      <section className="report-detail-dialog" role="dialog" aria-modal="true" aria-labelledby="report-detail-title" onClick={event => event.stopPropagation()}>
        <header><div><span>CHI TIẾT BÁO CÁO</span><h2 id="report-detail-title">{reportTypeLabel[selected.target_type]} bị báo cáo</h2></div><button type="button" className="report-detail-close" onClick={() => setSelected(null)} aria-label="Đóng chi tiết">×</button></header>
        <div className="report-detail-body">
          <p className="report-detail-reason"><b>Lý do báo cáo</b><span>{selected.reason}</span></p>
          {detailLoading && <p className="report-detail-status">Đang tải nội dung...</p>}
          {detailError && <p className="admin-error" role="alert">{detailError}</p>}
          {detail && !detail.post && !detail.user && <p className="report-detail-status">{selected.target_type === 'USER' ? 'Tài khoản không còn khả dụng.' : `${selected.target_type === 'COMMENT' ? 'Bình luận' : 'Bài viết'} đã được gỡ trước khi xử lý báo cáo. Bạn có thể kết thúc báo cáo mà không xóa lần nữa.`}</p>}
          {detail?.post && <div className="report-preview-post">
            <div className="report-preview-author"><UserAvatar src={detail.post.author.avatar} name={detail.post.author.name} /><div><strong>{detail.post.author.name}</strong><small><RelativeTime value={detail.post.createdAt} />{detail.post.groupName ? ` · ${detail.post.groupName}` : ' · Bài viết cộng đồng'}</small></div></div>
            <PostCategoryDetails post={detail.post} />
            {detail.post.content && <p className="report-preview-content">{detail.post.content}</p>}
            {!!detail.post.media?.length && <div className="report-preview-media">{detail.post.media.map(media => media.type === 'image' ? <img key={media.id} src={safeImageSrc(media.url)} alt={media.name || 'Ảnh trong bài viết bị báo cáo'} /> : media.type === 'video' ? <video key={media.id} src={media.url} controls preload="metadata" /> : <a key={media.id} href={media.url} target="_blank" rel="noreferrer">{media.name || 'Tệp đính kèm'}</a>)}</div>}
            {selected.target_type === 'COMMENT' && <div className="report-preview-comment"><b>Bình luận bị báo cáo</b>{detail.comment ? <div><UserAvatar src={detail.comment.author.avatar} name={detail.comment.author.name} /><section><strong>{detail.comment.author.name}</strong><small><RelativeTime value={detail.comment.createdAt} /></small><p>{detail.comment.content}</p>{detail.comment.imageUrl && <img src={safeImageSrc(detail.comment.imageUrl)} alt="Ảnh trong bình luận bị báo cáo" />}</section></div> : <p>Bình luận đã được gỡ trước khi xử lý báo cáo. Bạn có thể kết thúc báo cáo mà không xóa lần nữa.</p>}</div>}
          </div>}
          {detail?.user && <div className="report-preview-user"><UserAvatar src={detail.user.avatar} name={detail.user.name} /><h3>{detail.user.name}</h3>{detail.user.student_code && <p>Mã sinh viên: {detail.user.student_code}</p>}<p>Tham gia: {new Date(detail.user.joined_at).toLocaleDateString('vi-VN')}</p><p>Trạng thái: {detail.user.status}</p><Link href={`/profile/${detail.user.id}`}>Xem trang cá nhân</Link></div>}
        </div>
        <footer>{actions(selected)}</footer>
      </section>
    </div>}
  </section>;
}
