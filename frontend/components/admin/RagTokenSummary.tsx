"use client";

import { useEffect, useState } from "react";
import { fetchAdminUserRagUsage } from "@/lib/api";
import type { AdminUser, RagPeriod, RagUserUsage } from "@/types/admin";
import styles from "./RagTokenSummary.module.css";

const number = (value: number | null) => value === null ? "—" : new Intl.NumberFormat("vi-VN").format(value);
const dateTime = (value: string) => new Intl.DateTimeFormat("vi-VN", {
  dateStyle: "short", timeStyle: "short", timeZone: "Asia/Ho_Chi_Minh",
}).format(new Date(value));

export default function RagTokenSummary({ user, period, startDate, endDate }: {
  user: AdminUser; period: RagPeriod; startDate: string; endDate: string;
}) {
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState<RagUserUsage | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const validPeriod = period !== "custom" || (!!startDate && !!endDate && startDate <= endDate);

  useEffect(() => {
    if (!open || !validPeriod) { setDetail(null); return; }
    let active = true;
    setLoading(true); setError(""); setDetail(null);
    void fetchAdminUserRagUsage(user.id, period, startDate, endDate).then(
      result => { if (active) setDetail(result); },
      err => { if (active) setError(err instanceof Error ? err.message : "Không tải được dữ liệu RAG."); },
    ).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [open, user.id, period, startDate, endDate, validPeriod]);

  return <div className={styles.summary}>
    <div className={styles.metrics}><div><small>Input Tokens</small><strong>{number(user.rag_input_tokens)}</strong></div><div><small>Output Tokens</small><strong>{number(user.rag_output_tokens)}</strong></div><div><small>Total Tokens</small><strong>{number(user.rag_total_tokens)}</strong></div><button type="button" aria-expanded={open} onClick={() => setOpen(value => !value)}>{open ? "Ẩn chi tiết" : "Chi tiết RAG"}</button></div>
    {user.rag_usage_missing > 0 && <p className={styles.notice}>{user.rag_usage_missing} lượt không có usage do provider trả về; không tính là 0 token.</p>}
    {open && <div className={styles.detail}>{!validPeriod ? <p>Chọn khoảng ngày hợp lệ để xem chi tiết.</p> : loading ? <p>Đang tải chi tiết…</p> : error ? <p className={styles.error}>{error}</p> : detail && <>
      <div className={styles.detailTop}><strong>{detail.usage_calls} lượt gọi model</strong><span>Input {number(detail.input_tokens)} · Output {number(detail.output_tokens)} · Total {number(detail.total_tokens)}</span></div>
      <h4>Token theo ngày</h4>
      {detail.daily.length ? <div className={styles.chart}>{detail.daily.map(day => <div key={day.date}><small>{new Date(`${day.date}T00:00:00`).toLocaleDateString("vi-VN")}</small><span><i style={{ width: `${Math.max(2, Math.round((day.total_tokens || 0) / Math.max(1, ...detail.daily.map(item => item.total_tokens || 0)) * 100))}%` }}/></span><b>{number(day.total_tokens)}</b></div>)}</div> : <p>Chưa có usage trong khoảng này.</p>}
      <h4>Lượt gọi gần nhất</h4><div className={styles.tableWrap}><table><thead><tr><th>Thời gian</th><th>Model</th><th>Input</th><th>Output</th><th>Total</th><th>Trạng thái</th></tr></thead><tbody>{detail.calls.map(call => <tr key={call.id}><td>{dateTime(call.created_at)}</td><td>{call.provider} · {call.model}</td><td>{number(call.input_tokens)}</td><td>{number(call.output_tokens)}</td><td>{number(call.total_tokens)}</td><td>{call.usage_source === "missing" ? "Thiếu usage" : call.status}</td></tr>)}</tbody></table></div>
    </>}</div>}
  </div>;
}
