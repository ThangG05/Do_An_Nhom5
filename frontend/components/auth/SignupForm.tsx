"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import GoogleSignInButton from "./GoogleSignInButton";
import { requestRegistrationCode } from "@/lib/auth";

export default function SignupForm() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
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
    setIsLoading(true);
    setMessage("");
    try {
      await requestRegistrationCode(normalizedEmail);
      router.push(`/verification?email=${encodeURIComponent(normalizedEmail)}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Không thể gửi mã xác thực.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="signup-auth-options">
      <form className="signup-form" onSubmit={handleSubmit} noValidate>
        <div className="signup-field">
          <span>Nhập email sinh viên</span>
          <input
            id="signup-email"
            name="email"
            type="email"
            autoComplete="email"
            placeholder="@hvnh.edu.vn"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>
        <button className="signup-submit" type="submit" disabled={isLoading}>
          {isLoading ? "Đang gửi mã…" : "Tiếp tục"}
        </button>
        {message ? (
          <p className="signup-message" role="status">
            {message}
          </p>
        ) : null}
      </form>
      <div className="auth-divider">
        <span>hoặc</span>
      </div>
      <GoogleSignInButton />
    </div>
  );
}
