"use client";

import { useEffect, useState } from "react";
import UserAvatar from "@/components/ui/UserAvatar";
import { searchUsers, type UserSearchResult } from "@/lib/api";

export default function NewConversationModal({ onClose, onStart }: { onClose: () => void; onStart: (userId: string) => Promise<unknown> }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<UserSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const value = query.trim();
    if (value.length < 2) { setResults([]); setLoading(false); return; }
    let active = true;
    const timer = window.setTimeout(async () => {
      setLoading(true);
      setError("");
      try {
        const rows = await searchUsers(value);
        if (active) setResults(rows.filter((row) => row.friendshipStatus === "friends"));
      } catch (cause) {
        if (active) setError(cause instanceof Error ? cause.message : "Không thể tìm sinh viên.");
      } finally {
        if (active) setLoading(false);
      }
    }, 300);
    return () => { active = false; window.clearTimeout(timer); };
  }, [query]);

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape" && !busy) onClose(); };
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [busy, onClose]);

  const start = async (userId: string) => {
    if (busy) return;
    setBusy(userId);
    setError("");
    try { await onStart(userId); onClose(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Không thể bắt đầu cuộc trò chuyện."); }
    finally { setBusy(""); }
  };

  return (
    <div className="chat-modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !busy) onClose(); }}>
      <section className="chat-modal-card" role="dialog" aria-modal="true" aria-labelledby="new-chat-title">
        <header><div><small>TIN NHẮN MỚI</small><h3 id="new-chat-title">Chọn người bạn muốn nhắn tin</h3></div><button type="button" onClick={onClose} disabled={!!busy} aria-label="Đóng">×</button></header>
        <label className="chat-modal-search"><span>⌕</span><input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Nhập tên hoặc mã sinh viên..." /></label>
        {error && <p className="chat-modal-error" role="alert">{error}</p>}
        <div className="chat-user-results">
          {loading && <p>Đang tìm kiếm...</p>}
          {!loading && query.trim().length >= 2 && !results.length && !error && <p>Không tìm thấy bạn bè phù hợp.</p>}
          {results.map((user) => (
            <button type="button" key={user.id} disabled={!!busy} onClick={() => void start(user.id)}>
              <UserAvatar src={user.avatar} name={user.name} imageClassName="chat-user-result-avatar" fallbackClassName="chat-user-result-avatar chat-avatar-initials" />
              <span><strong>{user.name}</strong><small>@{user.username}{user.faculty ? ` · ${user.faculty}` : ""}</small></span>
              <b>{busy === user.id ? "Đang mở..." : "Nhắn tin"}</b>
            </button>
          ))}
        </div>
        <footer>Vì quyền riêng tư, bạn chỉ có thể bắt đầu trò chuyện với bạn bè.</footer>
      </section>
    </div>
  );
}
