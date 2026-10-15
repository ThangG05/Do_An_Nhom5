"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { changePassword } from "@/lib/api";
import { logoutSession } from "@/lib/auth";
import styles from "./AdminPasswordForm.module.css";

export default function AdminPasswordForm({ backHref }: { backHref: string }) {
  const router = useRouter();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [visible, setVisible] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const valid = current.length > 0 && next.length >= 8 && /[A-Za-zÀ-ỹ]/.test(next)
    && /\d/.test(next) && confirmation.length > 0;

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    if (next !== confirmation) {
      setError("Mật khẩu xác nhận chưa khớp.");
      return;
    }
    if (current === next) {
      setError("Mật khẩu mới phải khác mật khẩu hiện tại.");
      return;
    }
    setBusy(true);
    try {
      await changePassword(current, next);
      await logoutSession();
      router.replace("/login");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể đổi mật khẩu. Vui lòng thử lại.");
      setBusy(false);
    }
  };

  return (
    <main className={styles.page}>
      <div className={styles.shell}>
        <Link className={styles.back} href={backHref}>← Quay lại trang quản trị</Link>
        <div className={styles.heading}>
          <span className={styles.eyebrow}>BẢO MẬT TÀI KHOẢN</span>
          <h1>Đổi mật khẩu</h1>
          <p>Cập nhật mật khẩu quản trị để bảo vệ tài khoản và dữ liệu của nhóm.</p>
        </div>
        <div className={styles.columns}>
          <form className={styles.form} onSubmit={(event) => void submit(event)}>
            <label htmlFor="admin-current-password">Mật khẩu hiện tại</label>
            <input id="admin-current-password" type={visible ? "text" : "password"} autoComplete="current-password" value={current} onChange={(event) => setCurrent(event.target.value)} required />
            <label htmlFor="admin-new-password">Mật khẩu mới</label>
            <input id="admin-new-password" type={visible ? "text" : "password"} autoComplete="new-password" minLength={8} maxLength={128} value={next} onChange={(event) => setNext(event.target.value)} required />
            <label htmlFor="admin-confirm-password">Nhập lại mật khẩu mới</label>
            <input id="admin-confirm-password" type={visible ? "text" : "password"} autoComplete="new-password" minLength={8} maxLength={128} value={confirmation} onChange={(event) => setConfirmation(event.target.value)} required />
            <label className={styles.showPassword}>
              <input type="checkbox" checked={visible} onChange={(event) => setVisible(event.target.checked)} />
              Hiện mật khẩu
            </label>
            {error && <p className={styles.error} role="alert">{error}</p>}
            <button type="submit" disabled={busy || !valid}>{busy ? "Đang cập nhật..." : "Lưu mật khẩu mới"}</button>
          </form>
          <aside className={styles.note}>
            <span className={styles.noteIcon} aria-hidden="true">✦</span>
            <h2>Mật khẩu an toàn hơn</h2>
            <p>Dùng ít nhất 8 ký tự, có cả chữ và số. Tránh dùng lại mật khẩu của tài khoản khác.</p>
            <p>Sau khi đổi, bạn sẽ đăng nhập lại. Các mã làm mới phiên đăng nhập cũ sẽ bị thu hồi.</p>
            <Link href="/forgot-password">Không nhớ mật khẩu hiện tại?</Link>
          </aside>
        </div>
      </div>
    </main>
  );
}
