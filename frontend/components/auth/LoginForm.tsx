"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const router = useRouter();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!email.trim() || !password) {
      setMessage("Vui lòng nhập email và mật khẩu.");
      return;
    }
    window.sessionStorage.setItem("hvnh-hub-mock-authenticated", "true");
    router.push("/home");
  }

  return (
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
      <button className="login-submit" type="submit">
        Đăng nhập
      </button>
      {message ? (
        <p className="login-message" role="status">
          {message}
        </p>
      ) : null}
    </form>
  );
}
