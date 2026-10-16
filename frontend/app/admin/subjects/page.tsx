"use client";

import { useEffect, useState } from "react";
import { adminSubjects, saveSubject, listMajors, type Major, type Subject } from "@/lib/study-library";
import styles from "./subjects.module.css";

export default function SubjectsPage() {
  const [editingId, setEditingId] = useState<string | undefined>();
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
      void adminSubjects(query, offset).then(rows => { if (current) { setSubjects(previous => offset ? [...previous, ...rows] : rows); setHasMore(rows.length === 50); setError(""); } },
        err => { if (current) setError(err instanceof Error ? err.message : "Không tải được môn học."); })
        .finally(() => { if (current) setLoading(false); });
    }, 250);
    return () => { current = false; window.clearTimeout(timer); };
  }, [query, refresh, offset]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy(true); setError("");
    try {
      await saveSubject({ id: editingId, category, needs_review: needsReview, major_ids: majorIds, code: code.trim().toUpperCase() || null, name: name.trim(), source_note: source.trim(), is_active: active });
      setEditingId(undefined); setCode(""); setName(""); setSource(""); setActive(true); setNeedsReview(false); setMajorIds([]); setOffset(0); setRefresh(value => value + 1);
    } catch (err) { setError(err instanceof Error ? err.message : "Không lưu được môn học."); }
    finally { setBusy(false); }
  };

  const toggle = async (subject: Subject) => {
    setBusy(true); setError("");
    try { await saveSubject({ ...subject, is_active: !subject.is_active }); setOffset(0); setRefresh(value => value + 1); }
    catch (err) { setError(err instanceof Error ? err.message : "Không đổi được trạng thái môn học."); }
    finally { setBusy(false); }
  };

  return <main className="admin-console"><header className="admin-page-heading"><div><span>STUDY CATALOG</span><h1>Danh mục môn học</h1><p>Quản lý học phần đại cương và theo ngành. Giữ nguyên dữ liệu nguồn, rà soát các mã trùng hoặc còn thiếu.</p></div></header>
    {error && <div className="admin-error" role="alert">{error}</div>}
    <div className={styles.layout}><section className={styles.panel}><h2>{editingId ? "Chỉnh sửa môn học" : "Thêm môn học"}</h2><p>Mỗi môn được quản lý riêng, kể cả khi trùng mã. Mã còn thiếu có thể để trống.</p><form onSubmit={event => void submit(event)}><label>Mã môn học (nếu có)<input value={code} onChange={event => setCode(event.target.value)} placeholder="Mã theo nguồn đã xác minh" maxLength={40} minLength={2} /></label><label>Tên môn học <b>*</b><input value={name} onChange={event => setName(event.target.value)} placeholder="Tên môn học chính thức" maxLength={255} minLength={2} required /></label><label>Nguồn xác minh <b>*</b><textarea value={source} onChange={event => setSource(event.target.value)} placeholder="Ví dụ: tên tài liệu nội bộ, đơn vị cung cấp, thời điểm kiểm tra" maxLength={500} minLength={5} rows={3} required /></label><label>Phân loại<select value={category} onChange={event => { setCategory(event.target.value as Subject["category"]); setMajorIds([]); }}><option value="GENERAL">Đại cương</option><option value="SPECIALIZED">Theo ngành</option></select></label>
      {category === "SPECIALIZED" && <fieldset className={styles.majorChoices}><legend>Ngành sử dụng môn học</legend>{majors.map(major => <label key={major.id} className={styles.checkbox}><input type="checkbox" checked={majorIds.includes(major.id)} onChange={event => setMajorIds(previous => event.target.checked ? [...previous, major.id] : previous.filter(id => id !== major.id))} />{major.name}</label>)}</fieldset>}
      <label className={styles.checkbox}><input type="checkbox" checked={needsReview} onChange={event => setNeedsReview(event.target.checked)} /> Cần đối chiếu mã / tên với nguồn chính thức</label>
      <label className={styles.checkbox}><input type="checkbox" checked={active} onChange={event => setActive(event.target.checked)} /> Cho phép chọn khi chia sẻ tài liệu</label><button type="submit" disabled={busy}>{busy ? "Đang lưu…" : "Lưu môn học"}</button>{editingId && <button type="button" onClick={() => { setEditingId(undefined); setCode(""); setName(""); setSource(""); setMajorIds([]); setNeedsReview(false); setActive(true); }}>Hủy chỉnh sửa</button>}</form></section>
    <section className={styles.panel}><div className={styles.listHeader}><div><h2>Môn học trong hệ thống</h2><p>{subjects.length} kết quả</p></div><input value={query} onChange={event => { setQuery(event.target.value); setOffset(0); }} placeholder="Tìm mã hoặc tên môn…" aria-label="Tìm môn học" /></div>{loading ? <div className={styles.empty}>Đang tải…</div> : subjects.length ? <div className={styles.list}>{subjects.map(subject => <article key={subject.id}><div><strong>{subject.name}</strong><span>{subject.code || "Chưa có mã"} · {subject.category === "GENERAL" ? "Đại cương" : "Theo ngành"}{subject.needs_review ? " · Cần rà soát" : ""}</span><small>Nguồn: {subject.source_note}</small></div><div><em className={subject.is_active ? styles.enabled : styles.disabled}>{subject.is_active ? "Đang dùng" : "Đã tắt"}</em><button onClick={() => { setEditingId(subject.id); setCategory(subject.category); setNeedsReview(subject.needs_review); setMajorIds(subject.major_ids); setCode(subject.code || ""); setName(subject.name); setSource(subject.source_note); setActive(subject.is_active); window.scrollTo({ top: 0, behavior: "smooth" }); }}>Chỉnh sửa</button><button disabled={busy} onClick={() => void toggle(subject)}>{subject.is_active ? "Tắt" : "Bật"}</button></div></article>)}</div> : <div className={styles.empty}><strong>Không tìm thấy môn học</strong><p>Thêm môn từ nguồn đáng tin cậy trước khi sinh viên chia sẻ tài liệu.</p></div>}{hasMore && !loading && <button type="button" onClick={() => setOffset(value => value + 50)}>Xem thêm môn học</button>}</section></div>
  </main>;
}
