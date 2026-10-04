"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { clearPreviousAuthSession, completeRegistration, saveAuthSession } from "@/lib/auth";

export default function PasswordForm() {
  const [fullName, setFullName] = useState("");
  const [requiresFullName, setRequiresFullName] = useState(true);
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const storedName = window.sessionStorage.getItem("hvnh-hub-registration-name") || "";
    const requiresName = window.sessionStorage.getItem("hvnh-hub-registration-requires-name") !== "false";
    setFullName(storedName);
    setRequiresFullName(requiresName);
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if ((requiresFullName && !fullName.trim()) || !password || !confirmation) {
      setMessage("Vui lòng nhập đầy đủ thông tin.");
      return;
    }
    if (password.length < 8) {
      setMessage("Mật khẩu cần có ít nhất 8 ký tự.");
      return;
    }
    if (password !== confirmation) {
      setMessage("Mật khẩu xác nhận chưa khớp.");
      return;
    }
    if (!/[A-Za-zÀ-ỹ]/.test(password) || !/\d/.test(password)) {
      setMessage("Mật khẩu cần có ít nhất một chữ cái và một chữ số.");
      return;
    }

    const registrationToken = window.sessionStorage.getItem(
      "hvnh-hub-registration-token",
    );
    if (!registrationToken) {
      setMessage("Phiên xác thực đã hết hạn. Vui lòng đăng ký lại.");
      return;
    }

    setIsLoading(true);
    setMessage("");
    try {
      await clearPreviousAuthSession();
      const tokens = await completeRegistration(registrationToken, fullName, password);
      saveAuthSession(tokens);
      window.sessionStorage.removeItem("hvnh-hub-registration-token");
      window.sessionStorage.removeItem("hvnh-hub-registration-name");
      window.sessionStorage.removeItem("hvnh-hub-registration-requires-name");
      router.replace(tokens.user.system_role === "SUPER_ADMIN" ? "/admin" : tokens.user.admin_group_slugs.length ? "/group-admin" : "/home");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Không thể hoàn tất đăng ký.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <form className="password-form" onSubmit={handleSubmit}>
      {requiresFullName ? <div className="password-field">
        <label htmlFor="full-name">Họ và tên</label>
        <input id="full-name" name="fullName" type="text" autoComplete="name" value={fullName} onChange={(event) => setFullName(event.target.value)} required />
      </div> : <p className="password-existing-name">Tên tài khoản: <strong>{fullName}</strong></p>}
      <div className="password-field">
        <label htmlFor="password">Mật khẩu</label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
      </div>
      <div className="password-field">
        <label htmlFor="password-confirmation">Xác nhận mật khẩu</label>
        <input
          id="password-confirmation"
          name="passwordConfirmation"
          type="password"
          autoComplete="new-password"
          value={confirmation}
          onChange={(event) => setConfirmation(event.target.value)}
          required
        />
      </div>
      <button className="password-submit" type="submit" disabled={isLoading}>
        {isLoading ? "Đang tạo tài khoản…" : "Tiếp tục"}
      </button>
      {message ? (
        <p className="password-message" role="status">
          {message}
        </p>
      ) : null}
    </form>
  );
}
