"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function PasswordForm() {
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [message, setMessage] = useState("");
  const router = useRouter();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!password || !confirmation) {
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
    setMessage("Mật khẩu hợp lệ. Tài khoản đã sẵn sàng.");
    router.push("/welcome");
  }

  return (
    <form className="password-form" onSubmit={handleSubmit}>
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
      <button className="password-submit" type="submit">
        Tiếp tục
      </button>
      {message ? (
        <p className="password-message" role="status">
          {message}
        </p>
      ) : null}
    </form>
  );
}
