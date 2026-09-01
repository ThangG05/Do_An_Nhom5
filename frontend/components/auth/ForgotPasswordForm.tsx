"use client";

import { FormEvent, useState } from "react";
import styles from "./ForgotPasswordForm.module.css";

export default function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedEmail = email.trim().toLowerCase();

    if (!normalizedEmail) {
      setMessage("Vui lòng nhập email sinh viên.");
      return;
    }

    if (!normalizedEmail.endsWith("@hvnh.edu.vn")) {
      setMessage("Hãy sử dụng email có tên miền @hvnh.edu.vn.");
      return;
    }

    setMessage("Mã khôi phục sẽ được gửi tới email của bạn.");
  }

  return (
    <form className={styles.forgotPasswordForm} onSubmit={handleSubmit} noValidate>
      <div className={styles.formField}>
        <label htmlFor="forgot-password-email">Email</label>
        <input
          id="forgot-password-email"
          name="email"
          type="email"
          autoComplete="email"
          placeholder="@hvnh.edu.vn"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />
      </div>

      <button className={styles.forgotPasswordSubmit} type="submit">
        Tiếp tục
      </button>

      {message ? (
        <p className={styles.forgotPasswordMessage} role="status">
          {message}
        </p>
      ) : null}
    </form>
  );
}