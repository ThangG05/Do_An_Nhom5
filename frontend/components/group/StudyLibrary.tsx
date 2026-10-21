"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  decideStudyDocument, decideStudyDocumentReport, deleteStudyDocument, downloadStudyBundle, listStudyDocuments,
  myStudyDocuments, openStudyDocumentReports, pendingStudyDocuments, pendingStudyAIAssessments, previewStudyOfficeFile,
  reportStudyDocument, shareStudyDocument, signedStudyFile,
  documentTypeLabel, assessmentTypeLabel,
  type StudyDocument, type StudyDocumentReport, type StudyFile, type CatalogScope, type OfficePreview,
  type DocumentType, type AssessmentType, type StudyAIAssessment,
} from "@/lib/study-library";
import styles from "./StudyLibrary.module.css";
import SubjectPicker from "./SubjectPicker";
import { useAuthUser } from "@/components/auth/AuthProvider";

type Tab = "browse" | "mine" | "pending" | "reports";
const LIMIT = 50 * 1024 * 1024;
const PAGE_SIZE = 5;
const APPROVED_PAGE_SIZE = 6;
const ALLOWED = new Set(["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "jpg", "jpeg", "png", "webp"]);
const formatSize = (bytes: number) => bytes >= 1024 * 1024
  ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.ceil(bytes / 1024)} KB`;
const formatDate = (value: string) => new Intl.DateTimeFormat("vi-VN", {
  dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Ho_Chi_Minh",
}).format(new Date(value));

export default function StudyLibrary({ groupId, isAdmin, canRead, pendingCount = 0, reportCount = 0 }: {
  groupId: string; isAdmin: boolean; canRead: boolean; pendingCount?: number; reportCount?: number;
}) {
  const currentUser = useAuthUser();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [tab, setTab] = useState<Tab>("browse");
  const [documents, setDocuments] = useState<StudyDocument[]>([]);
  const [aiAssessments, setAiAssessments] = useState<Record<string, StudyAIAssessment>>({});
  const [reports, setReports] = useState<StudyDocumentReport[]>([]);
  const [uploadSubjectId, setUploadSubjectId] = useState("");
  const [uploadSubjectName, setUploadSubjectName] = useState("");
  const [uploadMajorId, setUploadMajorId] = useState("");
  const [documentType, setDocumentType] = useState<DocumentType | "">("");
  const [assessmentType, setAssessmentType] = useState<AssessmentType | null>(null);
  const [scope, setScope] = useState<CatalogScope>({});
  const [typeFilter, setTypeFilter] = useState("");
  const [assessmentFilter, setAssessmentFilter] = useState("");
  const pageSize = tab === "browse" ? APPROVED_PAGE_SIZE : PAGE_SIZE;
  const [filterReset, setFilterReset] = useState(0);
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
  const [notice, setNotice] = useState("");
  const [officePreview, setOfficePreview] = useState<OfficePreview | null>(null);
  const [reportingDocument, setReportingDocument] = useState<StudyDocument | null>(null);
  const [reportReason, setReportReason] = useState("");
  const [resolvingReport, setResolvingReport] = useState<StudyDocumentReport | null>(null);
  const [resolution, setResolution] = useState<{ decision: "REMOVE_DOCUMENT" | "DISMISS"; note: string } | null>(null);
  const totalBytes = useMemo(() => files.reduce((sum, file) => sum + file.size, 0), [files]);

  const resetUploadForm = () => {
    setUploadSubjectId("");
    setUploadSubjectName("");
    setUploadMajorId("");
    setDocumentType("");
    setAssessmentType(null);
    setTitle("");
    setDescription("");
    setFiles([]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const toggleUploadForm = () => {
    if (busy) return;
    resetUploadForm();
    setError("");
    setShowForm(value => !value);
  };

  const addFiles = (selected: FileList | null) => {
    // FileList is live: clearing the input below can empty it before React runs the state updater.
    const pickedFiles = Array.from(selected ?? []);
    if (!pickedFiles.length) return;
    setFiles(current => [...current, ...pickedFiles]);
    if (!title.trim() && !files.length) {
      const suggestion = pickedFiles[0].name.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " ").replace(/\s+/g, " ").trim();
      if (suggestion.length >= 5) setTitle(suggestion.slice(0, 120));
    }
  };

  const removeFile = (index: number) => {
    setFiles(current => current.filter((_, fileIndex) => fileIndex !== index));
  };

  useEffect(() => {
    if (!canRead) return;
    let active = true;
    const timer = window.setTimeout(() => {
      setLoading(true);
      if (tab === "reports") {
        void openStudyDocumentReports(groupId, offset, PAGE_SIZE + 1).then(rows => {
          if (active) { setReports(rows.slice(0, PAGE_SIZE)); setHasMore(rows.length > PAGE_SIZE); setError(""); }
        }, err => { if (active) setError(err instanceof Error ? err.message : "Không tải được tố cáo tài liệu."); })
          .finally(() => { if (active) setLoading(false); });
        return;
      }
      const request = tab === "mine" ? myStudyDocuments(groupId, offset, PAGE_SIZE + 1)
        : tab === "pending" ? pendingStudyDocuments(groupId, offset, PAGE_SIZE + 1)
        : listStudyDocuments(groupId, query, subjectId, offset, scope, pageSize + 1, typeFilter, assessmentFilter);
      void request.then(rows => { if (active) { setDocuments(rows.slice(0, pageSize)); setHasMore(rows.length > pageSize); setError(""); } },
        err => { if (active) setError(err instanceof Error ? err.message : "Không tải được kho tài liệu."); })
        .finally(() => { if (active) setLoading(false); });
    }, tab === "browse" ? 250 : 0);
    return () => { active = false; window.clearTimeout(timer); };
  }, [canRead, groupId, query, subjectId, tab, offset, refresh, scope, typeFilter, assessmentFilter, pageSize]);

  useEffect(() => {
    if (!isAdmin || !["pending", "reports"].includes(tab)) return;
    const timer = window.setInterval(() => setRefresh(value => value + 1), 30_000);
    return () => window.clearInterval(timer);
  }, [isAdmin, tab]);

  useEffect(() => { setReports([]); }, [groupId, refresh]);

  useEffect(() => {
    if (tab !== "pending" || !isAdmin || !documents.length) return;
    let active = true;
    void pendingStudyAIAssessments(groupId, documents.map(doc => doc.id)).then(rows => {
      if (active) setAiAssessments(Object.fromEntries(rows.map(row => [row.document_id, row])));
    }, () => { if (active) setAiAssessments({}); });
    return () => { active = false; };
  }, [tab, isAdmin, groupId, documents]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!uploadMajorId || !uploadSubjectId || !documentType || title.trim().length < 5 || !files.length || totalBytes > LIMIT || files.length > 10) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const created = await shareStudyDocument(groupId, uploadMajorId, uploadSubjectId, documentType,
        ["EXAM", "EXERCISE", "REVIEW"].includes(documentType) ? assessmentType : null,
        title.trim(), description.trim(), files);
      setShowForm(false); resetUploadForm(); setTab("mine"); setOffset(0); setRefresh(value => value + 1);
      setNotice(created.status === "APPROVED" ? "Tài liệu đã được chia sẻ và hiển thị ngay trong kho." : "Tài liệu đã được gửi, đang chờ admin nhóm duyệt.");
    } catch (err) { setError(err instanceof Error ? err.message : "Không gửi được tài liệu."); }
    finally { setBusy(false); }
  };

  const decide = async (doc: StudyDocument, decision: "APPROVE" | "REJECT") => {
    if (decision === "REJECT" && reason.trim().length < 3) return;
    setBusy(true); setError(""); setNotice("");
    try {
      await decideStudyDocument(groupId, doc.id, decision, decision === "REJECT" ? reason.trim() : undefined);
      setRejecting(""); setReason(""); setOffset(0); setRefresh(value => value + 1);
    } catch (err) { setError(err instanceof Error ? err.message : "Không thể xử lý tài liệu."); }
    finally { setBusy(false); }
  };

  const openFile = async (doc: StudyDocument, file: StudyFile, preview: boolean) => {
    setError("");
    if (preview && ["docx", "xlsx"].includes(file.extension.toLowerCase())) {
      try { setOfficePreview(await previewStudyOfficeFile(groupId, doc.id, file.id)); }
      catch (err) { setError(err instanceof Error ? err.message : "Không mở được bản xem trước."); }
      return;
    }
    const newTab = preview ? window.open("", "_blank") : null;
    try {
      const signed = await signedStudyFile(groupId, doc.id, file.id, preview);
      if (newTab) newTab.location.href = signed.url;
      else { const link = document.createElement("a"); link.href = signed.url; link.rel = "noopener"; link.click(); }
    } catch (err) {
      newTab?.close(); setError(err instanceof Error ? err.message : "Không mở được file.");
    }
  };

  const downloadBundle = async (doc: StudyDocument) => {
    setBusy(true); setError("");
    try {
      const blob = await downloadStudyBundle(groupId, doc.id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a"); link.href = url; link.download = `bo-tai-lieu-${doc.id}.zip`;
      document.body.appendChild(link); link.click(); link.remove(); window.setTimeout(() => URL.revokeObjectURL(url), 30_000);
    } catch (err) { setError(err instanceof Error ? err.message : "Không tải được trọn bộ tài liệu."); }
    finally { setBusy(false); }
  };

  const removeDocument = async (doc: StudyDocument) => {
    if (!window.confirm(`Xóa bộ tài liệu “${doc.title}”? Các file trong bộ này cũng sẽ bị xóa.`)) return;
    setBusy(true); setError("");
    try {
      await deleteStudyDocument(groupId, doc.id);
      if (documents.length === 1 && offset > 0) setOffset(value => Math.max(0, value - pageSize));
      setRefresh(value => value + 1);
    } catch (err) { setError(err instanceof Error ? err.message : "Không xóa được tài liệu."); }
    finally { setBusy(false); }
  };

  const submitReport = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!reportingDocument || reportReason.trim().length < 5) return;
    setBusy(true); setError(""); setNotice("");
    try {
      await reportStudyDocument(groupId, reportingDocument.id, reportReason.trim());
      setReportingDocument(null); setReportReason("");
      setNotice("Tố cáo đã được gửi đến admin nhóm Học tập.");
    } catch (err) { setError(err instanceof Error ? err.message : "Không gửi được tố cáo."); }
    finally { setBusy(false); }
  };

  const submitReportDecision = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!resolvingReport || !resolution || resolution.note.trim().length < 3) return;
    setBusy(true); setError(""); setNotice("");
    try {
      await decideStudyDocumentReport(groupId, resolvingReport.id, resolution.decision, resolution.note.trim());
      setResolvingReport(null); setResolution(null); setOffset(0); setRefresh(value => value + 1);
    } catch (err) { setError(err instanceof Error ? err.message : "Không xử lý được tố cáo."); }
    finally { setBusy(false); }
  };

  if (!canRead) return <section className={styles.gate}><span>🔒</span><h2>Kho tài liệu dành cho thành viên</h2><p>Hãy tham gia nhóm Học tập để tìm kiếm và chia sẻ tài liệu đã được duyệt.</p></section>;

  return <section className={styles.library} aria-label="Kho tài liệu Học tập">
    <header className={styles.header}><div><span>KHO TÀI LIỆU · HỌC TẬP</span><h2>Tài liệu học tập</h2><p>Chia sẻ kiến thức theo môn học. Tài liệu của thành viên được duyệt trước khi hiển thị; tài liệu của admin nhóm hiển thị ngay.</p></div><button type="button" className={styles.primary} disabled={busy} onClick={toggleUploadForm}>{showForm ? "Đóng biểu mẫu" : "+ Chia sẻ tài liệu"}</button></header>
    {error && <div className={styles.error} role="alert">{error}</div>}{notice && <div className={styles.notice} role="status">{notice}</div>}
    {showForm && <form className={styles.form} onSubmit={event => void submit(event)}>
      <div className={styles.formHeading}><h3>Chia sẻ tài liệu mới</h3><span>{isAdmin ? "Tài liệu của admin sẽ hiển thị ngay" : "Admin nhóm sẽ xem xét trước khi hiển thị"}</span></div>
      <div className={styles.formGrid}>
        <SubjectPicker value={uploadSubjectId} onChange={setUploadSubjectId}
          onSubjectChange={subject => setUploadSubjectName(subject?.name || "")}
          onScopeChange={next => setUploadMajorId(next.majorId || "")} required requireMajor />
      </div>
      <fieldset className={styles.typePicker}><legend>Loại tài liệu <b>*</b></legend><div>
        {(Object.entries(documentTypeLabel) as [DocumentType, string][]).map(([value, label]) =>
          <button key={value} type="button" aria-pressed={documentType === value}
            className={documentType === value ? styles.typeSelected : ""}
            onClick={() => { setDocumentType(value); if (!["EXAM", "EXERCISE", "REVIEW"].includes(value)) setAssessmentType(null); }}>
            {label}</button>)}
      </div></fieldset>
      {["EXAM", "EXERCISE", "REVIEW"].includes(documentType) &&
        <fieldset className={styles.assessmentPicker}><legend>Kỳ đánh giá <span>(tùy chọn)</span></legend><div>
          {([null, "MIDTERM", "FINAL"] as const).map(value => <label key={value || "none"}>
            <input type="radio" name="assessment-type" checked={assessmentType === value} onChange={() => setAssessmentType(value)} />
            {value ? assessmentTypeLabel[value] : "Không áp dụng / Không rõ"}
          </label>)}
        </div></fieldset>}
      <input ref={fileInputRef} className={styles.fileInput} type="file" multiple accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png,.webp" aria-label="Chọn tài liệu để chia sẻ" onChange={event => { addFiles(event.currentTarget.files); event.currentTarget.value = ""; }} />
      <button type="button" className={styles.filePick} disabled={busy} onClick={() => fileInputRef.current?.click()}>+ Chọn file PDF, Office hoặc ảnh</button>
      <div className={styles.fileSummary}><span>{files.length ? `${files.length} tệp đã chọn` : "Chưa có file"}</span><strong className={totalBytes > LIMIT ? styles.over : ""}>{formatSize(totalBytes)} / 50 MB</strong></div>
      {files.length > 0 && <ul className={styles.selectedFiles} aria-label="Tệp đã chọn để chia sẻ">{files.map((file, index) => <li key={`${file.name}-${file.lastModified}-${index}`}><span className={styles.selectedFileIcon} aria-hidden="true">▤</span><span className={styles.selectedFileInfo}><strong title={file.name}>{file.name}</strong><small>{formatSize(file.size)}</small></span><button type="button" disabled={busy} onClick={() => removeFile(index)} aria-label={`Gỡ tệp ${file.name}`} title="Gỡ tệp khỏi danh sách">Gỡ</button></li>)}</ul>}
      <label>Tiêu đề tài liệu <b>*</b><input value={title} onChange={event => setTitle(event.target.value)} placeholder="Ví dụ: Bài tập SQL chương 1–3" minLength={5} maxLength={120} required /></label>
      <label>Mô tả <span>(tùy chọn)</span><textarea value={description} onChange={event => setDescription(event.target.value)} rows={3} maxLength={500} placeholder="Ví dụ: Tài liệu gồm bài tập SQL chương 1–3, dùng để ôn giữa kỳ." /></label>
      <p className={styles.metadataPreview}>Xem trước: {uploadSubjectName || "Chưa chọn môn"} · {documentType ? documentTypeLabel[documentType] : "Chưa chọn loại"}{assessmentType ? ` · ${assessmentTypeLabel[assessmentType]}` : ""}</p>
      {totalBytes > LIMIT && <p className={styles.fileLimitWarning} role="alert">Tổng dung lượng vượt 50 MB. Hãy gỡ bớt tệp trước khi gửi.</p>}
      {files.length > 10 && <p className={styles.fileLimitWarning} role="alert">Chỉ được chia sẻ tối đa 10 tệp. Hãy gỡ bớt tệp trước khi gửi.</p>}
      {files.some(file => !ALLOWED.has(file.name.split(".").pop()?.toLowerCase() || "")) && <p className={styles.error}>Có file không thuộc định dạng được hỗ trợ.</p>}
      <div className={styles.formFoot}><small>Tối đa 10 file, tổng 50 MB. File gốc được lưu riêng tư trên R2.</small><button className={styles.primary} disabled={busy || !uploadMajorId || !uploadSubjectId || !documentType || title.trim().length < 5 || !files.length || files.length > 10 || totalBytes > LIMIT || files.some(file => !ALLOWED.has(file.name.split(".").pop()?.toLowerCase() || ""))}>{busy ? "Đang gửi…" : isAdmin ? "Chia sẻ ngay" : "Gửi tài liệu để duyệt"}</button></div>
    </form>}
    <nav className={styles.tabs} aria-label="Danh mục kho tài liệu"><button className={tab === "browse" ? styles.active : ""} onClick={() => { setTab("browse"); setOffset(0); }}>Tài liệu đã duyệt</button><button className={tab === "mine" ? styles.active : ""} onClick={() => { setTab("mine"); setOffset(0); }}>Tài liệu của tôi</button>{isAdmin && <><button className={tab === "pending" ? styles.active : ""} onClick={() => { setTab("pending"); setOffset(0); }}>Chờ duyệt{pendingCount > 0 && <span className={styles.pendingBadge}>{pendingCount}</span>}</button><button className={tab === "reports" ? styles.active : ""} onClick={() => { setTab("reports"); setOffset(0); }}>Tố cáo{reportCount > 0 && <span className={styles.pendingBadge}>{reportCount}</span>}</button></>}</nav>
    <div hidden={tab !== "browse"}><div className={styles.filters}><input value={query} onChange={event => { setQuery(event.target.value); setOffset(0); }} placeholder="Tìm tên tài liệu hoặc môn học…" aria-label="Tìm tài liệu"/>
      <select aria-label="Lọc loại tài liệu" value={typeFilter} onChange={event => { setTypeFilter(event.target.value); setOffset(0); }}><option value="">Mọi loại tài liệu</option>{(Object.entries(documentTypeLabel) as [DocumentType, string][]).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
      <select aria-label="Lọc kỳ đánh giá" value={assessmentFilter} onChange={event => { setAssessmentFilter(event.target.value); setOffset(0); }}><option value="">Mọi kỳ đánh giá</option>{(Object.entries(assessmentTypeLabel) as [AssessmentType, string][]).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
      <button type="button" onClick={() => { setQuery(""); setSubjectId(""); setTypeFilter(""); setAssessmentFilter(""); setScope({}); setFilterReset(value => value + 1); setOffset(0); }}>Đặt lại</button>
    </div><SubjectPicker key={filterReset} value={subjectId} onChange={id => { setSubjectId(id); setOffset(0); }} onScopeChange={next => { setScope(next); setOffset(0); }} /></div>
    {tab === "reports" ? loading ? <div className={styles.empty}>Đang tải tố cáo…</div> : !reports.length ? <div className={styles.empty}><span>✓</span><h3>Không có tố cáo cần xử lý</h3><p>Tố cáo tài liệu mới sẽ xuất hiện tại đây.</p></div> : <div className={styles.reportList}>{reports.map(report => <article key={report.id} className={styles.reportCard}><div className={styles.reportHeading}><div><span className={styles.subject}>{report.subject_code ? `${report.subject_code} · ` : ""}{report.subject_name}</span><h3>{report.title}</h3></div><time>{formatDate(report.created_at)}</time></div><p className={styles.reportMeta}><strong>{report.reporter_name}</strong> đã tố cáo · Người chia sẻ: <strong>{report.uploader_name}</strong></p><div className={styles.reportReason}><strong>Nguyên nhân tố cáo</strong><p>{report.reason}</p></div>{report.document_deleted && <p className={styles.reportWarning}>Tác giả đã xóa tài liệu khỏi kho trước khi tố cáo được xử lý.</p>}<div className={styles.reportActions}><button type="button" disabled={busy || report.document_deleted} className={styles.deleteButton} onClick={() => { setResolvingReport(report); setResolution({ decision: "REMOVE_DOCUMENT", note: "" }); }}>Gỡ tài liệu khỏi nhóm</button><button type="button" disabled={busy} onClick={() => { setResolvingReport(report); setResolution({ decision: "DISMISS", note: "" }); }}>Bác tố cáo</button></div></article>)}</div> : loading ? <div className={styles.empty}>Đang tải tài liệu…</div> : !documents.length ? <div className={styles.empty}><span>📚</span><h3>{tab === "pending" ? "Không có tài liệu chờ duyệt" : "Chưa có tài liệu phù hợp"}</h3><p>{tab === "browse" ? "Thử tìm môn học khác hoặc chia sẻ tài liệu đầu tiên." : "Danh sách sẽ cập nhật khi có tài liệu mới."}</p></div> : <div className={styles.list}>{documents.map(doc => <article key={doc.id} className={styles.card}>
      <div className={styles.cardTop}><span className={styles.subject}>{doc.subject_code ? `${doc.subject_code} · ` : ""}{doc.subject_name}</span>{tab !== "browse" && <span className={`${styles.status} ${styles[doc.status.toLowerCase()]}`}>{doc.status === "PENDING" ? "Chờ duyệt" : doc.status === "APPROVED" ? "Đã duyệt" : "Từ chối"}</span>}</div>
      <div className={styles.documentTags}><span>{doc.document_type ? documentTypeLabel[doc.document_type] : "Chưa phân loại"}</span>{doc.assessment_type && <span>{assessmentTypeLabel[doc.assessment_type]}</span>}</div>
      <h3>{doc.title}</h3>{doc.description && <p>{doc.description}</p>}<div className={styles.meta}>Chia sẻ bởi <strong>{doc.uploader_name}</strong><span>·</span>{formatDate(doc.created_at)}<span>·</span>{formatSize(doc.total_bytes)}</div>
      {doc.rejection_reason && <p className={styles.rejection}>Lý do từ chối: {doc.rejection_reason}</p>}
      {tab === "pending" && isAdmin && <section className={styles.aiAdvice} aria-label="Đề xuất AI, chỉ để tham khảo">
        <div className={styles.aiAdviceHead}><strong>AI đọc trước · chỉ hỗ trợ quyết định</strong><span>{aiAssessments[doc.id]?.status === "COMPLETED"
          ? aiAssessments[doc.id].recommendation === "APPROVE" ? "Gợi ý duyệt" : aiAssessments[doc.id].recommendation === "REJECT" ? "Gợi ý từ chối" : "Cần xem kỹ"
          : aiAssessments[doc.id]?.status === "FAILED" || !aiAssessments[doc.id] ? "Cần xem thủ công" : "Đang phân tích"}</span></div>
        {aiAssessments[doc.id]?.reason && <p>{aiAssessments[doc.id].reason}</p>}
        {aiAssessments[doc.id]?.file_results?.map(file => <div className={styles.aiFile} key={file.file_id}>
          <strong>{file.file_name} · {file.recommendation === "APPROVE" ? "Phù hợp" : file.recommendation === "REJECT" ? "Có dấu hiệu cần từ chối" : "Cần xem kỹ"}</strong>
          <p>{file.reason}{file.sampling_limited && " · Chỉ đọc được một phần, cần kiểm tra file gốc."}</p>{file.evidence_quote && <blockquote>{file.evidence_location && <b>{file.evidence_location}: </b>}“{file.evidence_quote}”</blockquote>}
        </div>)}
        <small>Admin vẫn cần kiểm tra tài liệu trước khi phê duyệt hoặc từ chối.</small>
      </section>}
      {!!doc.files.length && <div className={styles.files}>{doc.files.map(file => <div key={file.id} className={styles.file}><div><span aria-hidden="true">{["jpg", "jpeg", "png", "webp"].includes(file.extension) ? "▧" : "▤"}</span><div><strong title={file.original_name}>{file.original_name}</strong><small>{file.extension.toUpperCase()} · {formatSize(file.size_bytes)}</small></div></div><div className={styles.fileActions}>{(["pdf", "docx", "xlsx", "jpg", "jpeg", "png", "webp"].includes(file.extension.toLowerCase())) && <button type="button" onClick={() => void openFile(doc, file, true)}>Xem</button>}<button type="button" onClick={() => void openFile(doc, file, false)}>Tải</button></div></div>)}</div>}
      <div className={styles.documentActions}><button type="button" disabled={busy} onClick={() => void downloadBundle(doc)}>Tải cả bộ (.zip)</button>{tab === "mine" && <button type="button" className={styles.deleteButton} disabled={busy} onClick={() => void removeDocument(doc)}>Xóa tài liệu</button>}{tab === "browse" && currentUser?.id !== doc.uploaded_by && <button type="button" disabled={busy} onClick={() => { setReportingDocument(doc); setReportReason(""); }}>Tố cáo</button>}</div>
      {tab === "pending" && isAdmin && <div className={styles.moderation}>{rejecting === doc.id ? <><input value={reason} onChange={event => setReason(event.target.value)} placeholder="Lý do từ chối (ít nhất 3 ký tự)" maxLength={2000} /><button disabled={busy || reason.trim().length < 3} onClick={() => void decide(doc, "REJECT")}>Xác nhận từ chối</button><button onClick={() => { setRejecting(""); setReason(""); }}>Hủy</button></> : <><button className={styles.primary} disabled={busy} onClick={() => void decide(doc, "APPROVE")}>Phê duyệt</button><button disabled={busy} onClick={() => setRejecting(doc.id)}>Từ chối</button></>}</div>}
    </article>)}</div>}
    {(offset > 0 || hasMore) && <nav className={styles.pagination} aria-label="Phân trang tài liệu"><button type="button" disabled={loading || offset === 0} onClick={() => setOffset(value => Math.max(0, value - pageSize))}>‹ Trang trước</button><span>Trang {Math.floor(offset / pageSize) + 1}</span><button type="button" disabled={loading || !hasMore} onClick={() => setOffset(value => value + pageSize)}>Trang sau ›</button></nav>}
    {officePreview && <div className={styles.previewBackdrop} role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setOfficePreview(null); }}><section className={styles.previewModal} role="dialog" aria-modal="true" aria-label={`Xem trước ${officePreview.name}`}><header><div><strong>{officePreview.name}</strong><small>{officePreview.kind === "word" ? "Bản xem trước Word" : "Bản xem trước Excel"}</small></div><button type="button" onClick={() => setOfficePreview(null)} aria-label="Đóng bản xem trước">×</button></header><div className={styles.previewContent}>{officePreview.kind === "word" ? <>{officePreview.paragraphs.map((paragraph, index) => <p key={`p-${index}`}>{paragraph}</p>)}{officePreview.tables.map((table, tableIndex) => <div className={styles.previewTableWrap} key={`t-${tableIndex}`}><table><tbody>{table.map((row, rowIndex) => <tr key={rowIndex}>{row.map((cell, cellIndex) => <td key={cellIndex}>{cell}</td>)}</tr>)}</tbody></table></div>)}</> : officePreview.sheets.map(sheet => <section key={sheet.name}><h3>{sheet.name}</h3><div className={styles.previewTableWrap}><table><tbody>{sheet.rows.map((row, rowIndex) => <tr key={rowIndex}>{row.map((cell, cellIndex) => <td key={cellIndex}>{cell ?? ""}</td>)}</tr>)}</tbody></table></div>{sheet.truncated && <small>Đang hiển thị tối đa 200 dòng và 30 cột của trang tính này.</small>}</section>)}</div></section></div>}
    {reportingDocument && <div className={styles.previewBackdrop}><form className={`${styles.previewModal} ${styles.reasonModal}`} role="dialog" aria-modal="true" onSubmit={event => void submitReport(event)}><header><div><strong>Tố cáo tài liệu</strong><small>{reportingDocument.title}</small></div><button type="button" onClick={() => setReportingDocument(null)} aria-label="Đóng">×</button></header><div className={styles.reasonBody}><p>Hãy ghi rõ nội dung vi phạm để admin nhóm Học tập xem xét.</p><textarea autoFocus value={reportReason} onChange={event => setReportReason(event.target.value)} minLength={5} maxLength={3000} rows={5} placeholder="Mô tả nguyên nhân tố cáo…" required /><small>{reportReason.trim().length}/3000 ký tự</small></div><footer><button type="button" onClick={() => setReportingDocument(null)}>Hủy</button><button type="submit" className={styles.primary} disabled={busy || reportReason.trim().length < 5}>{busy ? "Đang gửi…" : "Gửi tố cáo"}</button></footer></form></div>}
    {resolvingReport && resolution && <div className={styles.previewBackdrop}><form className={`${styles.previewModal} ${styles.reasonModal}`} role="dialog" aria-modal="true" onSubmit={event => void submitReportDecision(event)}><header><div><strong>{resolution.decision === "REMOVE_DOCUMENT" ? "Gỡ tài liệu khỏi nhóm" : "Bác tố cáo"}</strong><small>{resolvingReport.title}</small></div><button type="button" onClick={() => { setResolvingReport(null); setResolution(null); }} aria-label="Đóng">×</button></header><div className={styles.reasonBody}><p>{resolution.decision === "REMOVE_DOCUMENT" ? "Tài liệu và các file sẽ bị gỡ khỏi kho Học tập. Hãy ghi rõ lý do để người chia sẻ hiểu quyết định." : "Tố cáo sẽ được đóng mà không gỡ tài liệu. Hãy ghi lại căn cứ xử lý."}</p><textarea autoFocus value={resolution.note} onChange={event => setResolution(value => value ? { ...value, note: event.target.value } : value)} minLength={3} maxLength={3000} rows={5} placeholder="Lý do xử lý…" required /><small>{resolution.note.trim().length}/3000 ký tự</small></div><footer><button type="button" onClick={() => { setResolvingReport(null); setResolution(null); }}>Hủy</button><button type="submit" className={resolution.decision === "REMOVE_DOCUMENT" ? styles.deleteButton : styles.primary} disabled={busy || resolution.note.trim().length < 3}>{busy ? "Đang xử lý…" : resolution.decision === "REMOVE_DOCUMENT" ? "Xác nhận gỡ" : "Xác nhận bác tố cáo"}</button></footer></form></div>}
  </section>;
}
