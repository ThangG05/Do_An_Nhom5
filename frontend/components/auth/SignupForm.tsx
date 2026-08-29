"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function SignupForm() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const router = useRouter();

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
    router.push(`/verification?email=${encodeURIComponent(normalizedEmail)}`);
  }

  return (
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
      <button className="signup-submit" type="submit">
        Tiếp tục
      </button>
      {message ? (
        <p className="signup-message" role="status">
          {message}
        </p>
      ) : null}
    </form>
  );
}
