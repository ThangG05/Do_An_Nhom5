"use client";

import { useState } from "react";
import { useDialog } from "@/components/ui/DialogProvider";
import { disciplineAdminUser } from "@/lib/api";
import { formatFullDateTime } from "@/lib/dateTime";
import type { AdminUser } from "@/types/admin";

type Action = "WARN" | "SUSPEND" | "BAN" | "UNLOCK";
type ActionResult = { title: string; message: string; tone: "success" | "warning" };

const actionLabels: Record<Action, string> = {
  WARN: "cảnh cáo",
  SUSPEND: "tạm khóa",
  BAN: "khóa vĩnh viễn",
  UNLOCK: "mở khóa",
};

export default function DisciplineActions({ user, onDone }: { user: AdminUser; onDone: () => Promise<void> }) {
  const dialog = useDialog();
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ActionResult | null>(null);

  const run = async (action: Action) => {
    const reason = await dialog.prompt({
      title: "Xử lý tài khoản",
      message: `Nhập lý do ${actionLabels[action]} đối với ${user.full_name}.`,
      placeholder: "Lý do và căn cứ xử lý...",
      multiline: true,
      minLength: 3,
      tone: action === "BAN" ? "danger" : "default",
    });
    if (!reason) return;

    let days: number | undefined;
    if (action === "SUSPEND") {
      const input = await dialog.prompt({
        title: "Thời hạn tạm khóa",
        message: "Nhập số ngày từ 1 đến 365.",
        initialValue: "7",
        inputType: "number",
      });
      if (!input) return;
      days = Number(input);
      if (!Number.isInteger(days) || days < 1 || days > 365) {
        dialog.notify({ title: "Thời hạn không hợp lệ", message: "Số ngày phải nằm trong khoảng 1–365.", tone: "danger" });
        return;
      }
    }

    if (action === "BAN" && !await dialog.confirm({
      title: "Khóa vĩnh viễn?",
      message: `Tài khoản ${user.full_name} sẽ bị vô hiệu hóa và các phiên đăng nhập bị thu hồi.`,
      confirmLabel: "Khóa vĩnh viễn",
      tone: "danger",
    })) return;

    setBusy(true);
    setResult(null);
    try {
      await disciplineAdminUser(user.id, action, reason, days);
      await onDone();

      const expiry = action === "SUSPEND" && days
        ? new Date(Date.now() + days * 24 * 60 * 60 * 1000).toISOString()
        : null;
      const message = action === "SUSPEND"
        ? `Tài khoản đã bị khóa trong ${days} ngày, đến ${formatFullDateTime(expiry)}. Lý do: ${reason}`
        : action === "BAN"
          ? `Tài khoản đã bị khóa vĩnh viễn. Lý do: ${reason}`
          : action === "UNLOCK"
            ? `Tài khoản đã được mở khóa. Lý do: ${reason}`
            : `Đã ghi nhận cảnh cáo số ${user.warning_count + 1}. Lý do: ${reason}`;
      const title = action === "SUSPEND" ? "Đã tạm khóa tài khoản"
        : action === "BAN" ? "Đã khóa vĩnh viễn tài khoản"
          : action === "UNLOCK" ? "Đã mở khóa tài khoản"
            : "Đã cảnh cáo tài khoản";

      setResult({ title, message, tone: action === "SUSPEND" || action === "BAN" ? "warning" : "success" });
      dialog.notify({ title, message, tone: "success" });
    } catch (error) {
      dialog.notify({
        title: "Không thể xử lý tài khoản",
        message: error instanceof Error ? error.message : "Vui lòng thử lại.",
        tone: "danger",
      });
    } finally {
      setBusy(false);
    }
  };

  return <div className="discipline-panel">
    {result && <div className={`discipline-result tone-${result.tone}`} role="status" aria-live="polite">
      <strong>{result.title}</strong>
      <p>{result.message}</p>
      <button type="button" onClick={() => setResult(null)} aria-label="Đóng thông báo">×</button>
    </div>}
    <div className="discipline-actions">
      <button type="button" disabled={busy} onClick={() => void run("WARN")}>Cảnh cáo ({user.warning_count})</button>
      <button type="button" className="warning" disabled={busy} onClick={() => void run("SUSPEND")}>Tạm khóa</button>
      <button type="button" disabled={busy} onClick={() => void run("UNLOCK")}>Mở khóa</button>
      <button type="button" className="danger" disabled={busy} onClick={() => void run("BAN")}>Khóa vĩnh viễn</button>
      {user.suspended_until && <small title={formatFullDateTime(user.suspended_until)}>Tạm khóa đến {formatFullDateTime(user.suspended_until)}</small>}
    </div>
  </div>;
}
