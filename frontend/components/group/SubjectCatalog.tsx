"use client";

import { useEffect, useState } from "react";
import { adminSubjects, saveSubject, listMajors, type Major, type Subject } from "@/lib/study-library";
import styles from "./SubjectCatalog.module.css";

export default function SubjectCatalog({ groupId }: { groupId: string }) {
  const pageSize = 10;
  const [editingSubject, setEditingSubject] = useState<Subject | null>(null);
  const [editCode, setEditCode] = useState("");
  const [editName, setEditName] = useState("");
  const [editError, setEditError] = useState("");
  const [category, setCategory] = useState<Subject["category"]>("SPECIALIZED");
  const [needsReview, setNeedsReview] = useState(false);
  const [majors, setMajors] = useState<Major[]>([]);
  const [majorIds, setMajorIds] = useState<string[]>([]);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  useEffect(() => { void listMajors().then(setMajors).catch(() => setError("Không tải được danh mục ngành.")); }, []);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [query, setQuery] = useState("");
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [source, setSource] = useState("");
  const [active, setActive] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    let current = true;
    const timer = window.setTimeout(() => {
      setLoading(true);
      void adminSubjects(groupId, query, offset, pageSize + 1).then(rows => { if (current) { if (offset > 0 && rows.length === 0) { setOffset(value => Math.max(0, value - pageSize)); return; } setSubjects(rows.slice(0, pageSize)); setHasMore(rows.length > pageSize); setError(""); } },
        err => { if (current) setError(err instanceof Error ? err.message : "Không tải được môn học."); })
        .finally(() => { if (current) setLoading(false); });
    }, 250);
    return () => { current = false; window.clearTimeout(timer); };
  }, [groupId, query, refresh, offset]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy(true); setError("");
    try {
      await saveSubject(groupId, { category, needs_review: needsReview, major_ids: majorIds, code: code.trim().toUpperCase() || null, name: name.trim(), source_note: source.trim(), is_active: active });
      setCode(""); setName(""); setSource(""); setActive(true); setNeedsReview(false); setMajorIds([]); setCategory("SPECIALIZED"); setOffset(0); setRefresh(value => value + 1);
    } catch (err) { setError(err instanceof Error ? err.message : "Không lưu được môn học."); }
    finally { setBusy(false); }
  };

  const toggle = async (subject: Subject) => {
    setBusy(true); setError("");
    try { await saveSubject(groupId, { ...subject, is_active: !subject.is_active }); setOffset(0); setRefresh(value => value + 1); }
    catch (err) { setError(err instanceof Error ? err.message : "Không đổi được trạng thái môn học."); }
    finally { setBusy(false); }
  };

  const startEditing = (subject: Subject) => {
    setEditingSubject(subject);
    setEditCode(subject.code || "");
    setEditName(subject.name);
    setEditError("");
  };

  const submitEdit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!editingSubject) return;
    setBusy(true); setEditError("");
    try {
      await saveSubject(groupId, {
        id: editingSubject.id,
        code: editCode.trim().toUpperCase() || null,
        name: editName.trim(),
        source_note: editingSubject.source_note,
        is_active: editingSubject.is_active,
        category: editingSubject.category,
        needs_review: editingSubject.needs_review,
        major_ids: editingSubject.major_ids,
      });
      setEditingSubject(null); setOffset(0); setRefresh(value => value + 1);
    } catch (err) {
      setEditError(err instanceof Error ? err.message : "Không lưu được tên hoặc mã môn học.");
    } finally { setBusy(false); }
  };

  return <section className={styles.catalog}><header className={styles.catalogHeading}><div><span>STUDY CATALOG</span><h2>Danh mục môn học</h2><p>Quản lý học phần đại cương và theo ngành. Giữ nguyên dữ liệu nguồn, rà soát các mã trùng hoặc còn thiếu.</p></div></header>
    {error && <div className="admin-error" role="alert">{error}</div>}
    <div className={styles.layout}><section className={styles.panel}><h2>Thêm môn học</h2><p>Mỗi môn được quản lý riêng, kể cả khi trùng mã. Mã còn thiếu có thể để trống.</p><form onSubmit={event => void submit(event)}><label>Mã môn học (nếu có)<input value={code} onChange={event => setCode(event.target.value)} placeholder="Mã theo nguồn đã xác minh" maxLength={40} minLength={2} /></label><label>Tên môn học <b>*</b><input value={name} onChange={event => setName(event.target.value)} placeholder="Tên môn học chính thức" maxLength={255} minLength={2} required /></label><label>Nguồn xác minh <b>*</b><textarea value={source} onChange={event => setSource(event.target.value)} placeholder="Ví dụ: tên tài liệu nội bộ, đơn vị cung cấp, thời điểm kiểm tra" maxLength={500} minLength={5} rows={3} required /></label><label>Phân loại<select value={category} onChange={event => { setCategory(event.target.value as Subject["category"]); setMajorIds([]); }}><option value="GENERAL">Đại cương</option><option value="SPECIALIZED">Theo ngành</option></select></label>
      {category === "SPECIALIZED" && <fieldset className={styles.majorChoices}><legend>Ngành sử dụng môn học</legend>{majors.map(major => <label key={major.id} className={styles.checkbox}><input type="checkbox" checked={majorIds.includes(major.id)} onChange={event => setMajorIds(previous => event.target.checked ? [...previous, major.id] : previous.filter(id => id !== major.id))} />{major.name}</label>)}</fieldset>}
      <label className={styles.checkbox}><input type="checkbox" checked={needsReview} onChange={event => setNeedsReview(event.target.checked)} /> Cần đối chiếu mã / tên với nguồn chính thức</label>
      <label className={styles.checkbox}><input type="checkbox" checked={active} onChange={event => setActive(event.target.checked)} /> Cho phép chọn khi chia sẻ tài liệu</label><button type="submit" disabled={busy}>{busy ? "Đang lưu…" : "Thêm môn học"}</button></form></section>
    <section className={styles.panel}><div className={styles.listHeader}><div><h2>Môn học trong hệ thống</h2><p>Trang {Math.floor(offset / pageSize) + 1} · {subjects.length} môn</p></div><input value={query} onChange={event => { setQuery(event.target.value); setOffset(0); }} placeholder="Tìm mã hoặc tên môn…" aria-label="Tìm môn học" /></div>{loading ? <div className={styles.empty}>Đang tải…</div> : subjects.length ? <div className={styles.list}>{subjects.map(subject => <article key={subject.id}><div><strong>{subject.name}</strong><span>{subject.code || "Chưa có mã"} · {subject.category === "GENERAL" ? "Đại cương" : "Theo ngành"}{subject.needs_review ? " · Cần rà soát" : ""}</span><small>Nguồn: {subject.source_note}</small></div><div><em className={subject.is_active ? styles.enabled : styles.disabled}>{subject.is_active ? "Đang dùng" : "Đã tắt"}</em><button type="button" onClick={() => startEditing(subject)}>Chỉnh sửa</button><button type="button" disabled={busy} onClick={() => void toggle(subject)}>{subject.is_active ? "Tắt" : "Bật"}</button></div></article>)}</div> : <div className={styles.empty}><strong>Không tìm thấy môn học</strong><p>Thêm môn từ nguồn đáng tin cậy trước khi sinh viên chia sẻ tài liệu.</p></div>}{(offset > 0 || hasMore) && <nav className={styles.pagination} aria-label="Phân trang môn học"><button type="button" disabled={loading || offset === 0} onClick={() => setOffset(value => Math.max(0, value - pageSize))}>‹ Trang trước</button><span>Trang {Math.floor(offset / pageSize) + 1}</span><button type="button" disabled={loading || !hasMore} onClick={() => setOffset(value => value + pageSize)}>Trang sau ›</button></nav>}</section></div>
    {editingSubject && <div className={styles.modalBackdrop} role="presentation" onMouseDown={event => { if (event.target === event.currentTarget && !busy) setEditingSubject(null); }}><section className={styles.editModal} role="dialog" aria-modal="true" aria-labelledby="edit-subject-title"><header><div><span>CHỈNH SỬA DANH MỤC</span><h2 id="edit-subject-title">Sửa môn học</h2><p>{editingSubject.code || "Chưa có mã"} · {editingSubject.category === "GENERAL" ? "Đại cương" : "Theo ngành"}</p></div><button type="button" aria-label="Đóng" disabled={busy} onClick={() => setEditingSubject(null)}>×</button></header><form onSubmit={event => void submitEdit(event)}><label>Mã môn học<input autoFocus value={editCode} onChange={event => setEditCode(event.target.value)} placeholder="Nhập mã môn (có thể để trống)" maxLength={40} minLength={2} /></label><label>Tên môn học<input value={editName} onChange={event => setEditName(event.target.value)} placeholder="Nhập tên môn học" maxLength={255} minLength={2} required /></label>{editError && <div className={styles.modalError} role="alert">{editError}</div>}<footer><button type="button" disabled={busy} onClick={() => setEditingSubject(null)}>Hủy</button><button type="submit" disabled={busy || editName.trim().length < 2}>{busy ? "Đang lưu…" : "Lưu thay đổi"}</button></footer></form></section></div>}
  </section>;
}
