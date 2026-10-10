"use client";

import { useCallback, useEffect, useState } from "react";
import {
  createBlacklistKeyword,
  deleteBlacklistKeyword,
  fetchBlacklist,
  fetchSystemStatus,
  updateBlacklistKeyword,
  updateMaintenance,
} from "@/lib/api";
import type { BlacklistKeyword, MaintenanceState } from "@/types/system";
import { useDialog } from "@/components/ui/DialogProvider";

function localDatetime(value: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

export default function SystemConfig() {
  const dialog = useDialog();
  const [state, setState] = useState<MaintenanceState>({ enabled: false, message: "Hệ thống đang bảo trì.", expected_end_at: null });
  const [items, setItems] = useState<BlacklistKeyword[]>([]);
  const [keyword, setKeyword] = useState("");
  const [action, setAction] = useState<"BLOCK" | "REVIEW">("BLOCK");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [savingMaintenance, setSavingMaintenance] = useState(false);
  const [addingKeyword, setAddingKeyword] = useState(false);
  const [busyKeywordId, setBusyKeywordId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [systemState, keywords] = await Promise.all([fetchSystemStatus(), fetchBlacklist()]);
      setState(systemState);
      setItems(keywords);
      setError("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không tải được cấu hình.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const saveMaintenance = async () => {
    if (savingMaintenance) return;
    if (state.enabled && !state.message.trim()) {
      setError("Vui lòng nhập thông báo bảo trì trước khi bật chế độ bảo trì.");
      return;
    }
    if (state.enabled && state.expected_end_at && new Date(state.expected_end_at).getTime() <= Date.now()) {
      setError("Thời gian tự động mở lại phải ở tương lai.");
      return;
    }
    setSavingMaintenance(true);
    setError("");
    try {
      setState(await updateMaintenance({ ...state, expected_end_at: state.enabled ? state.expected_end_at : null, message: state.message.trim() }));
      dialog.notify({ title: "Đã lưu cấu hình bảo trì", tone: "success" });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không lưu được cấu hình.");
      dialog.notify({ title: "Lưu cấu hình thất bại", message: cause instanceof Error ? cause.message : "Vui lòng thử lại.", tone: "danger" });
    } finally {
      setSavingMaintenance(false);
    }
  };

  const addKeyword = async () => {
    const normalized = keyword.trim();
    if (!normalized || addingKeyword) return;
    if (items.some((item) => item.keyword.trim().toLocaleLowerCase("vi") === normalized.toLocaleLowerCase("vi"))) {
      setError("Từ khóa này đã có trong danh sách.");
      return;
    }
    setAddingKeyword(true);
    setError("");
    try {
      await createBlacklistKeyword(normalized, action);
      setKeyword("");
      await load();
      dialog.notify({ title: "Đã thêm từ khóa kiểm duyệt", tone: "success" });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể thêm từ khóa.");
    } finally {
      setAddingKeyword(false);
    }
  };

  const toggleKeyword = async (item: BlacklistKeyword, enabled: boolean) => {
    if (busyKeywordId) return;
    setBusyKeywordId(item.id);
    setError("");
    try {
      await updateBlacklistKeyword(item.id, { is_active: enabled });
      setItems((current) => current.map((row) => row.id === item.id ? { ...row, is_active: enabled } : row));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể cập nhật từ khóa.");
    } finally {
      setBusyKeywordId(null);
    }
  };

  const removeKeyword = async (item: BlacklistKeyword) => {
    if (busyKeywordId) return;
    const confirmed = await dialog.confirm({
      title: "Xóa từ khóa?",
      message: `Từ khóa “${item.keyword}” sẽ không còn được dùng để kiểm duyệt.`,
      confirmLabel: "Xóa từ khóa",
      tone: "danger",
    });
    if (!confirmed) return;
    setBusyKeywordId(item.id);
    setError("");
    try {
      await deleteBlacklistKeyword(item.id);
      setItems((current) => current.filter((row) => row.id !== item.id));
      dialog.notify({ title: "Đã xóa từ khóa", tone: "success" });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể xóa từ khóa.");
    } finally {
      setBusyKeywordId(null);
    }
  };

  return (
    <section className="system-config" aria-busy={loading}>
      <header><span>CẤU HÌNH HỆ THỐNG</span><h2>Bảo trì và kiểm duyệt tự động</h2><p>Điều chỉnh thời gian bảo trì và các từ khóa cần kiểm duyệt.</p></header>
      {error && <div className="admin-error" role="alert">{error}</div>}
      {loading ? <div className="admin-empty-state">Đang tải cấu hình hệ thống...</div> : (
        <>
          <div className="maintenance-box">
            <div className="maintenance-heading"><div><strong>Bật chế độ bảo trì</strong><p>Khi bật, sinh viên sẽ thấy thông báo bảo trì cho đến lúc bạn tắt hoặc đến giờ mở lại.</p></div><label className="maintenance-switch"><input type="checkbox" checked={state.enabled} onChange={(event) => setState({ ...state, enabled: event.target.checked, expected_end_at: event.target.checked ? state.expected_end_at : null })} aria-label="Bật chế độ bảo trì" /><span aria-hidden="true" /></label></div>
            <div className="maintenance-fields"><label>Thông báo bảo trì<textarea value={state.message} onChange={(event) => setState({ ...state, message: event.target.value })} placeholder="Nội dung hiển thị cho sinh viên" /></label><label>Tự động mở lại<input type="datetime-local" value={localDatetime(state.expected_end_at)} disabled={!state.enabled} onChange={(event) => setState({ ...state, expected_end_at: event.target.value ? new Date(event.target.value).toISOString() : null })} /><small>Để trống nếu bạn muốn tắt bảo trì thủ công.</small></label></div>
            <button type="button" disabled={savingMaintenance} onClick={() => void saveMaintenance()}><span aria-hidden="true">✓</span>{savingMaintenance ? "Đang lưu..." : "Lưu cấu hình bảo trì"}</button>
          </div>
          <div className="blacklist-box">
            <h3>Danh sách từ khóa kiểm duyệt</h3><p>Tự động xử lý bài viết và bình luận chứa các từ khóa này.</p>
            <div className="blacklist-add">
              <input value={keyword} onChange={(event) => setKeyword(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") void addKeyword(); }} placeholder="Nhập từ khóa..." />
              <select value={action} onChange={(event) => setAction(event.target.value as "BLOCK" | "REVIEW")}><option value="BLOCK">Chặn hoàn toàn</option><option value="REVIEW">Chuyển kiểm duyệt</option></select>
              <button type="button" disabled={!keyword.trim() || addingKeyword} onClick={() => void addKeyword()}><span aria-hidden="true">＋</span>{addingKeyword ? "Đang thêm..." : "Thêm từ khóa"}</button>
            </div>
            {items.map((item) => (
              <article key={item.id} aria-busy={busyKeywordId === item.id}>
                <strong>{item.keyword}</strong>
                <span>{item.action === "BLOCK" ? "Chặn hoàn toàn" : "Chuyển kiểm duyệt"}</span>
                <label><input type="checkbox" checked={item.is_active} disabled={busyKeywordId !== null} onChange={(event) => void toggleKeyword(item, event.target.checked)} /> Đang dùng</label>
                <button type="button" disabled={busyKeywordId !== null} onClick={() => void removeKeyword(item)}><span aria-hidden="true">×</span>{busyKeywordId === item.id ? "Đang xử lý..." : "Xóa"}</button>
              </article>
            ))}
            {!items.length && <p className="admin-empty-state">Chưa có từ khóa kiểm duyệt nào.</p>}
          </div>
        </>
      )}
    </section>
  );
}
