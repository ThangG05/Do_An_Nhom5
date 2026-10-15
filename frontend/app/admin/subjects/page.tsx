"use client";

import { useEffect, useState } from "react";
import { adminSubjects, saveSubject, type Subject } from "@/lib/study-library";
import styles from "./subjects.module.css";

export default function SubjectsPage() {
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
      void adminSubjects(query).then(rows => { if (current) { setSubjects(rows); setError(""); } },
        err => { if (current) setError(err instanceof Error ? err.message : "Không tải được môn học."); })
        .finally(() => { if (current) setLoading(false); });
    }, 250);
    return () => { current = false; window.clearTimeout(timer); };
  }, [query, refresh]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy(true); setError("");
    try {
      await saveSubject({ code: code.trim().toUpperCase(), name: name.trim(), source_note: source.trim(), is_active: active });
      setCode(""); setName(""); setSource(""); setActive(true); setRefresh(value => value + 1);
    } catch (err) { setError(err instanceof Error ? err.message : "Không lưu được môn học."); }
    finally { setBusy(false); }
  };

  const toggle = async (subject: Subject) => {
    setBusy(true); setError("");
    try { await saveSubject({ code: subject.code, name: subject.name, source_note: subject.source_note, is_active: !subject.is_active }); setRefresh(value => value + 1); }
    catch (err) { setError(err instanceof Error ? err.message : "Không đổi được trạng thái môn học."); }
    finally { setBusy(false); }
  };

  return <main className="admin-console"><header className="admin-page-heading"><div><span>STUDY CATALOG</span><h1>Danh mục môn học</h1><p>Chỉ thêm môn học đã xác minh của Học viện Ngân hàng; kho tài liệu không cho nhập môn tùy ý.</p></div></header>
    {error && <div className="admin-error" role="alert">{error}</div>}
    <div className={styles.layout}><section className={styles.panel}><h2>{code ? "Thêm hoặc cập nhật môn học" : "Thêm môn học đã xác minh"}</h2><p>Danh mục khởi đầu trống. Ghi rõ nguồn để quản trị viên khác có thể đối chiếu.</p><form onSubmit={event => void submit(event)}><label>Mã môn học <b>*</b><input value={code} onChange={event => setCode(event.target.value)} placeholder="Mã theo nguồn đã xác minh" maxLength={40} minLength={2} required /></label><label>Tên môn học <b>*</b><input value={name} onChange={event => setName(event.target.value)} placeholder="Tên môn học chính thức" maxLength={255} minLength={2} required /></label><label>Nguồn xác minh <b>*</b><textarea value={source} onChange={event => setSource(event.target.value)} placeholder="Ví dụ: tên tài liệu nội bộ, đơn vị cung cấp, thời điểm kiểm tra" maxLength={500} minLength={5} rows={3} required /></label><label className={styles.checkbox}><input type="checkbox" checked={active} onChange={event => setActive(event.target.checked)} /> Cho phép chọn khi chia sẻ tài liệu</label><button type="submit" disabled={busy}>{busy ? "Đang lưu…" : "Lưu môn học"}</button></form></section>
    <section className={styles.panel}><div className={styles.listHeader}><div><h2>Môn học trong hệ thống</h2><p>{subjects.length} kết quả</p></div><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Tìm mã hoặc tên môn…" aria-label="Tìm môn học" /></div>{loading ? <div className={styles.empty}>Đang tải…</div> : subjects.length ? <div className={styles.list}>{subjects.map(subject => <article key={subject.id}><div><strong>{subject.name}</strong><span>{subject.code} · {subject.institution}</span><small>Nguồn: {subject.source_note}</small></div><div><em className={subject.is_active ? styles.enabled : styles.disabled}>{subject.is_active ? "Đang dùng" : "Đã tắt"}</em><button onClick={() => { setCode(subject.code); setName(subject.name); setSource(subject.source_note); setActive(subject.is_active); window.scrollTo({ top: 0, behavior: "smooth" }); }}>Chỉnh sửa</button><button disabled={busy} onClick={() => void toggle(subject)}>{subject.is_active ? "Tắt" : "Bật"}</button></div></article>)}</div> : <div className={styles.empty}><strong>Chưa có môn học được xác minh</strong><p>Thêm môn từ nguồn đáng tin cậy trước khi sinh viên chia sẻ tài liệu.</p></div>}</section></div>
  </main>;
}
