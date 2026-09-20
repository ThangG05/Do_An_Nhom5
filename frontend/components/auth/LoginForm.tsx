"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import GoogleSignInButton from "./GoogleSignInButton";
import { clearPreviousAuthSession, loginWithPassword, saveAuthSession } from "@/lib/auth";

export default function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!email.trim() || !password) {
      setMessage("Vui lòng nhập email và mật khẩu.");
      return;
    }
    setIsLoading(true);
    setMessage("");
    try {
      await clearPreviousAuthSession();
      const tokens = await loginWithPassword(
        email.trim().toLowerCase(),
        password,
      );
      saveAuthSession(tokens);
      router.replace(tokens.user.system_role === "SUPER_ADMIN" ? "/admin" : "/home");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Không thể đăng nhập.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="login-auth-options">
      <form className="login-form" onSubmit={handleSubmit} noValidate>
        <div className="form-field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            placeholder="tenban@hvnh.edu.vn"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>
        <div className="form-field">
          <label htmlFor="password">Mật khẩu</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            placeholder="Nhập mật khẩu"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>
        <div className="login-options">
          <label>
            <input type="checkbox" name="remember" /> Ghi nhớ đăng nhập
          </label>
          <button
            type="button"
            className="text-action"
            onClick={() => router.push("/forgot-password")}
          >
            Quên mật khẩu?
          </button>
        </div>
        <button className="login-submit" type="submit" disabled={isLoading}>
          {isLoading ? "Đang đăng nhập…" : "Đăng nhập"}
        </button>
        {message ? (
          <p className="login-message" role="status">
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
