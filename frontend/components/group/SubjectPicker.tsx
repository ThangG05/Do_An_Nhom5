"use client";

import { useEffect, useState } from "react";
import { listMajors, searchSubjects, type Major, type Subject, type CatalogScope } from "@/lib/study-library";
import styles from "./SubjectPicker.module.css";

export default function SubjectPicker({ value, onChange, onScopeChange, required = false }: {
  value: string; onChange: (id: string) => void; onScopeChange?: (scope: CatalogScope) => void; required?: boolean;
}) {
  const [majors, setMajors] = useState<Major[]>([]);
  const [category, setCategory] = useState<CatalogScope["category"]>("");
  const [majorId, setMajorId] = useState("");
  const [query, setQuery] = useState("");
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [focused, setFocused] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    void listMajors().then(rows => { if (alive) setMajors(rows); }, () => {
      if (alive) setError("Không tải được danh mục ngành. Bạn vẫn có thể tìm môn theo tên hoặc mã.");
    });
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    const timer = window.setTimeout(() => {
      void searchSubjects(query, { category, majorId }, 0, 8).then(rows => {
        if (alive) { setSubjects(rows); setError(""); }
      }, err => {
        if (alive) setError(err instanceof Error ? err.message : "Không tải được danh mục môn.");
      }).finally(() => { if (alive) setLoading(false); });
    }, query.trim() ? 180 : 0);
    return () => { alive = false; window.clearTimeout(timer); };
  }, [query, category, majorId]);

  const changeScope = (nextCategory: CatalogScope["category"], nextMajor: string) => {
    setCategory(nextCategory);
    setMajorId(nextMajor);
    setSubjects([]);
    setFocused(false);
    onChange("");
    onScopeChange?.({ category: nextCategory, majorId: nextMajor });
  };

  const selected = subjects.find(subject => subject.id === value);
  const suggestionsOpen = focused && !value;

  return <fieldset className={styles.picker}>
    <legend>{required ? "Chọn môn cho tài liệu *" : "Tìm theo ngành và môn học"}</legend>
    <div className={styles.row}>
      <label>Phân loại<select aria-label="Phân loại" value={category} onChange={event => changeScope(event.target.value as CatalogScope["category"], "")}>
        <option value="">Tất cả học phần</option><option value="GENERAL">Đại cương</option><option value="SPECIALIZED">Theo ngành</option>
      </select></label>
      {category !== "GENERAL" && <label>Ngành<select aria-label="Ngành" value={majorId} onChange={event => changeScope(event.target.value ? "SPECIALIZED" : category, event.target.value)}>
        <option value="">Tất cả ngành</option>{majors.map(major => <option key={major.id} value={major.id}>{major.name}{major.code ? ` (${major.code})` : ""} · {major.subject_count} môn</option>)}
      </select></label>}
    </div>

    <div className={styles.searchArea}>
      <label htmlFor={`subject-search-${required ? "upload" : "filter"}`}>Tìm môn
        <input id={`subject-search-${required ? "upload" : "filter"}`} value={query}
          onChange={event => { setQuery(event.target.value); onChange(""); setFocused(true); }}
          onFocus={() => setFocused(true)} onBlur={() => window.setTimeout(() => setFocused(false), 120)}
          onKeyDown={event => { if (event.key === "Escape") setFocused(false); }}
          placeholder="Nhập tên hoặc mã học phần…" autoComplete="off" role="combobox"
          aria-expanded={suggestionsOpen} aria-controls={`subject-options-${required ? "upload" : "filter"}`} aria-autocomplete="list" />
      </label>
      {value && selected && <div className={styles.selected}>
        <span><b>{selected.code || "Chưa có mã"}</b><span>{selected.name}</span></span>
        <button type="button" onClick={() => { onChange(""); setFocused(true); }} aria-label="Bỏ chọn môn">×</button>
      </div>}
      {suggestionsOpen && <div className={styles.suggestions} id={`subject-options-${required ? "upload" : "filter"}`} role="listbox" aria-label="Môn học phù hợp">
        {loading ? <div className={styles.suggestionHint}>Đang tìm môn phù hợp…</div>
          : subjects.length ? subjects.map(subject => <button type="button" role="option" aria-selected={subject.id === value}
            key={subject.id} onMouseDown={event => event.preventDefault()}
            onClick={() => { onChange(subject.id); setFocused(false); }}>
            <span className={styles.suggestionCode}>{subject.code || "Môn chưa có mã"}</span>
            <span className={styles.suggestionName}>{subject.name}</span>
            <small>{subject.category === "GENERAL" ? "Đại cương" : "Chuyên ngành"}</small>
          </button>)
          : <div className={styles.suggestionHint}>{query.trim() ? "Chưa có môn khớp. Thử nhập một phần tên hoặc mã môn." : "Nhập tên hoặc mã để lọc nhanh; chọn môn trong danh sách."}</div>}
      </div>}
    </div>

    {category === "GENERAL" && <small>Danh mục dùng chung; không có nghĩa mọi ngành đều bắt buộc học tất cả môn này.</small>}
    {selected?.needs_review && <small>Tên và mã môn đang được giữ theo tài liệu nguồn, có thông tin cần quản trị viên đối chiếu.</small>}
    {error && <small role="alert">{error}</small>}
  </fieldset>;
}
