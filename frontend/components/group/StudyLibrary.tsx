"use client";

import { useEffect, useMemo, useState } from "react";
import {
  decideStudyDocument, listStudyDocuments, myStudyDocuments, pendingStudyDocuments,
  searchSubjects, shareStudyDocument, signedStudyFile,
  type StudyDocument, type StudyFile, type Subject,
} from "@/lib/study-library";
import styles from "./StudyLibrary.module.css";

type Tab = "browse" | "mine" | "pending";
const LIMIT = 50 * 1024 * 1024;
const ALLOWED = new Set(["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "jpg", "jpeg", "png", "webp"]);
const formatSize = (bytes: number) => bytes >= 1024 * 1024
  ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.ceil(bytes / 1024)} KB`;
const formatDate = (value: string) => new Intl.DateTimeFormat("vi-VN", {
  dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Ho_Chi_Minh",
}).format(new Date(value));

export default function StudyLibrary({ groupId, isAdmin, canRead }: {
  groupId: string; isAdmin: boolean; canRead: boolean;
}) {
  const [tab, setTab] = useState<Tab>("browse");
  const [documents, setDocuments] = useState<StudyDocument[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [subjectQuery, setSubjectQuery] = useState("");
  const [query, setQuery] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [rejecting, setRejecting] = useState("");
  const [reason, setReason] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const totalBytes = useMemo(() => files.reduce((sum, file) => sum + file.size, 0), [files]);

  useEffect(() => {
    if (!canRead) return;
    const timer = window.setTimeout(() => {
      void searchSubjects(subjectQuery).then(setSubjects, err => setError(err instanceof Error ? err.message : "Không tải được môn học."));
    }, 250);
    return () => window.clearTimeout(timer);
  }, [canRead, subjectQuery]);

  useEffect(() => {
    if (!canRead) return;
    let active = true;
    const timer = window.setTimeout(() => {
      setLoading(true);
      const request = tab === "mine" ? myStudyDocuments(groupId, offset)
        : tab === "pending" ? pendingStudyDocuments(groupId, offset)
        : listStudyDocuments(groupId, query, subjectId, offset);
      void request.then(rows => { if (active) { setDocuments(previous => offset ? [...previous, ...rows.filter(row => !previous.some(item => item.id === row.id))] : rows); setHasMore(rows.length === 30); setError(""); } },
        err => { if (active) setError(err instanceof Error ? err.message : "Không tải được kho tài liệu."); })
        .finally(() => { if (active) setLoading(false); });
    }, tab === "browse" ? 250 : 0);
    return () => { active = false; window.clearTimeout(timer); };
  }, [canRead, groupId, query, subjectId, tab, offset, refresh]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!subjectId || !title.trim() || !files.length || totalBytes > LIMIT || files.length > 10) return;
    setBusy(true); setError("");
    try {
      await shareStudyDocument(groupId, subjectId, title.trim(), description.trim(), files);
      setShowForm(false); setTitle(""); setDescription(""); setFiles([]); setTab("mine"); setOffset(0); setRefresh(value => value + 1);
    } catch (err) { setError(err instanceof Error ? err.message : "Không gửi được tài liệu."); }
    finally { setBusy(false); }
  };

  const decide = async (doc: StudyDocument, decision: "APPROVE" | "REJECT") => {
    if (decision === "REJECT" && reason.trim().length < 3) return;
    setBusy(true); setError("");
    try {
      await decideStudyDocument(groupId, doc.id, decision, decision === "REJECT" ? reason.trim() : undefined);
      setRejecting(""); setReason(""); setOffset(0); setRefresh(value => value + 1);
    } catch (err) { setError(err instanceof Error ? err.message : "Không thể xử lý tài liệu."); }
    finally { setBusy(false); }
  };

  const openFile = async (doc: StudyDocument, file: StudyFile, preview: boolean) => {
    const newTab = preview ? window.open("", "_blank") : null;
    try {
      const signed = await signedStudyFile(groupId, doc.id, file.id, preview);
      if (newTab) newTab.location.href = signed.url;
      else { const link = document.createElement("a"); link.href = signed.url; link.rel = "noopener"; link.click(); }
    } catch (err) {
      newTab?.close(); setError(err instanceof Error ? err.message : "Không mở được file.");
    }
  };

  if (!canRead) return <section className={styles.gate}><span>🔒</span><h2>Kho tài liệu dành cho thành viên</h2><p>Hãy tham gia nhóm Học tập để tìm kiếm và chia sẻ tài liệu đã được duyệt.</p></section>;

  return <section className={styles.library} aria-label="Kho tài liệu Học tập">
    <header className={styles.header}><div><span>KHO TÀI LIỆU · HỌC TẬP</span><h2>Tài liệu học tập</h2><p>Chia sẻ kiến thức theo môn học. Mọi tài liệu đều được quản trị viên duyệt trước khi xuất hiện.</p></div><button type="button" className={styles.primary} onClick={() => setShowForm(value => !value)}>{showForm ? "Đóng biểu mẫu" : "+ Chia sẻ tài liệu"}</button></header>
    {error && <div className={styles.error} role="alert">{error}</div>}
    {showForm && <form className={styles.form} onSubmit={event => void submit(event)}>
      <div className={styles.formHeading}><h3>Chia sẻ tài liệu mới</h3><span>Admin nhóm sẽ xem xét trước khi hiển thị</span></div>
      <div className={styles.formGrid}>
        <label>Môn học <b>*</b><input value={subjectQuery} onChange={event => { setSubjectQuery(event.target.value); setSubjectId(""); }} placeholder="Tìm theo tên hoặc mã môn…" autoComplete="off" />
          <select value={subjectId} onChange={event => setSubjectId(event.target.value)} required><option value="">Chọn môn học đã xác minh</option>{subjects.map(subject => <option key={subject.id} value={subject.id}>{subject.code} · {subject.name}</option>)}</select>
          {!subjects.length && <small>Chưa tìm thấy môn học. Hãy liên hệ quản trị viên để cập nhật danh mục.</small>}
        </label>
        <label>Tên tài liệu <b>*</b><input value={title} onChange={event => setTitle(event.target.value)} placeholder="Ví dụ: Slide chương 1" maxLength={255} required /></label>
      </div>
      <label>Mô tả ngắn <span>(tùy chọn)</span><textarea value={description} onChange={event => setDescription(event.target.value)} rows={3} maxLength={2000} placeholder="Tóm tắt nội dung giúp bạn học dễ tìm thấy…" /></label>
      <label className={styles.filePick}>+ Chọn file PDF, Office hoặc ảnh<input type="file" multiple accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png,.webp" onChange={event => setFiles(Array.from(event.target.files || []))} /></label>
      <div className={styles.fileSummary}><span>{files.length ? files.map(file => file.name).join(" · ") : "Chưa có file"}</span><strong className={totalBytes > LIMIT ? styles.over : ""}>{formatSize(totalBytes)} / 50 MB</strong></div>
      {files.some(file => !ALLOWED.has(file.name.split(".").pop()?.toLowerCase() || "")) && <p className={styles.error}>Có file không thuộc định dạng được hỗ trợ.</p>}
      <div className={styles.formFoot}><small>Tối đa 10 file, tổng 50 MB. File gốc được lưu riêng tư trên R2.</small><button className={styles.primary} disabled={busy || !subjectId || !title.trim() || !files.length || files.length > 10 || totalBytes > LIMIT || files.some(file => !ALLOWED.has(file.name.split(".").pop()?.toLowerCase() || ""))}>{busy ? "Đang gửi…" : "Gửi chờ duyệt"}</button></div>
    </form>}
    <nav className={styles.tabs} aria-label="Danh mục kho tài liệu"><button className={tab === "browse" ? styles.active : ""} onClick={() => { setTab("browse"); setOffset(0); }}>Tài liệu đã duyệt</button><button className={tab === "mine" ? styles.active : ""} onClick={() => { setTab("mine"); setOffset(0); }}>Tài liệu của tôi</button>{isAdmin && <button className={tab === "pending" ? styles.active : ""} onClick={() => { setTab("pending"); setOffset(0); }}>Chờ duyệt</button>}</nav>
    {tab === "browse" && <div className={styles.filters}><input value={query} onChange={event => { setQuery(event.target.value); setOffset(0); }} placeholder="Tìm tên tài liệu hoặc môn học…" aria-label="Tìm tài liệu"/><select value={subjectId} onChange={event => { setSubjectId(event.target.value); setOffset(0); }} aria-label="Lọc môn học"><option value="">Tất cả môn học</option>{subjects.map(subject => <option key={subject.id} value={subject.id}>{subject.code} · {subject.name}</option>)}</select></div>}
    {loading ? <div className={styles.empty}>Đang tải tài liệu…</div> : !documents.length ? <div className={styles.empty}><span>📚</span><h3>{tab === "pending" ? "Không có tài liệu chờ duyệt" : "Chưa có tài liệu phù hợp"}</h3><p>{tab === "browse" ? "Thử tìm môn học khác hoặc chia sẻ tài liệu đầu tiên." : "Danh sách sẽ cập nhật khi có tài liệu mới."}</p></div> : <div className={styles.list}>{documents.map(doc => <article key={doc.id} className={styles.card}>
      <div className={styles.cardTop}><span className={styles.subject}>{doc.subject_code} · {doc.subject_name}</span>{tab !== "browse" && <span className={`${styles.status} ${styles[doc.status.toLowerCase()]}`}>{doc.status === "PENDING" ? "Chờ duyệt" : doc.status === "APPROVED" ? "Đã duyệt" : "Từ chối"}</span>}</div>
      <h3>{doc.title}</h3>{doc.description && <p>{doc.description}</p>}<div className={styles.meta}>Chia sẻ bởi <strong>{doc.uploader_name}</strong><span>·</span>{formatDate(doc.created_at)}<span>·</span>{formatSize(doc.total_bytes)}</div>
      {doc.rejection_reason && <p className={styles.rejection}>Lý do từ chối: {doc.rejection_reason}</p>}
      {!!doc.files.length && <div className={styles.files}>{doc.files.map(file => <div key={file.id} className={styles.file}><div><span aria-hidden="true">{["jpg", "jpeg", "png", "webp"].includes(file.extension) ? "▧" : "▤"}</span><div><strong>{file.original_name}</strong><small>{file.extension.toUpperCase()} · {formatSize(file.size_bytes)}</small></div></div><div className={styles.fileActions}>{(["pdf", "jpg", "jpeg", "png", "webp"].includes(file.extension)) && <button type="button" onClick={() => void openFile(doc, file, true)}>Xem</button>}<button type="button" onClick={() => void openFile(doc, file, false)}>Tải</button></div></div>)}</div>}
      {tab === "pending" && isAdmin && <div className={styles.moderation}>{rejecting === doc.id ? <><input value={reason} onChange={event => setReason(event.target.value)} placeholder="Lý do từ chối (ít nhất 3 ký tự)" maxLength={2000} /><button disabled={busy || reason.trim().length < 3} onClick={() => void decide(doc, "REJECT")}>Xác nhận từ chối</button><button onClick={() => { setRejecting(""); setReason(""); }}>Hủy</button></> : <><button className={styles.primary} disabled={busy} onClick={() => void decide(doc, "APPROVE")}>Phê duyệt</button><button disabled={busy} onClick={() => setRejecting(doc.id)}>Từ chối</button></>}</div>}
    </article>)}</div>}
    {hasMore && !loading && <button type="button" className={styles.loadMore} onClick={() => setOffset(value => value + 30)}>Xem thêm tài liệu</button>}
  </section>;
}
