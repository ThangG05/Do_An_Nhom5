"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { requestPasswordReset, resetPassword } from "@/lib/api";
import styles from "./ForgotPasswordForm.module.css";

const OTP_LIFETIME_SECONDS = 5 * 60;
const RESEND_COOLDOWN_SECONDS = 60;

function formatTime(seconds: number) {
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

export default function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [code, setCode] = useState(["", "", "", ""]);
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [step, setStep] = useState<1 | 2>(1);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [expiresAt, setExpiresAt] = useState(0);
  const [resendAt, setResendAt] = useState(0);
  const [now, setNow] = useState(Date.now());
  const inputRefs = useRef<Array<HTMLInputElement | null>>([]);
  const router = useRouter();
  const otpSeconds = Math.max(0, Math.ceil((expiresAt - now) / 1000));
  const resendSeconds = Math.max(0, Math.ceil((resendAt - now) / 1000));

  useEffect(() => {
    const savedEmail = window.sessionStorage.getItem("hvnh-password-reset-otp-email");
    const savedExpiry = Number(window.sessionStorage.getItem("hvnh-password-reset-otp-expires"));
    const savedResendAt = Number(window.sessionStorage.getItem("hvnh-password-reset-otp-resend-at"));
    if (savedEmail && savedExpiry > 0) {
      setEmail(savedEmail);
      setExpiresAt(savedExpiry);
      setResendAt(savedResendAt || 0);
      setStep(2);
    }
  }, []);

  useEffect(() => {
    if (step !== 2) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [step]);

  function setExpiryTimers(normalizedEmail: string) {
    const requestedAt = Date.now();
    const nextExpiry = requestedAt + OTP_LIFETIME_SECONDS * 1000;
    const nextResendAt = requestedAt + RESEND_COOLDOWN_SECONDS * 1000;
    setNow(requestedAt);
    setExpiresAt(nextExpiry);
    setResendAt(nextResendAt);
    window.sessionStorage.setItem("hvnh-password-reset-otp-email", normalizedEmail);
    window.sessionStorage.setItem("hvnh-password-reset-otp-expires", String(nextExpiry));
    window.sessionStorage.setItem("hvnh-password-reset-otp-resend-at", String(nextResendAt));
  }

  function updateCode(index: number, value: string) {
    const digits = value.replace(/\D/g, "");
    if (digits.length > 1) {
      const pasted = digits.slice(0, 4).split("");
      setCode(pasted.concat(["", "", "", ""]).slice(0, 4));
      inputRefs.current[Math.min(pasted.length, 3)]?.focus();
      return;
    }
    setCode((current) => current.map((digit, item) => item === index ? digits : digit));
    if (digits && index < 3) inputRefs.current[index + 1]?.focus();
  }

  function handleCodeKeyDown(index: number, event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Backspace" && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
    if (event.key === "ArrowLeft" && index > 0) inputRefs.current[index - 1]?.focus();
    if (event.key === "ArrowRight" && index < 3) inputRefs.current[index + 1]?.focus();
  }

  async function requestCode(normalizedEmail: string, isResend = false) {
    await requestPasswordReset(normalizedEmail);
    setCode(["", "", "", ""]);
    setExpiryTimers(normalizedEmail);
    if (isResend) setMessage("Mã OTP mới đã được gửi nếu tài khoản hợp lệ.");
    else {
      setStep(2);
      setMessage("Nếu tài khoản hợp lệ, mã OTP đã được gửi tới email.");
    }
    inputRefs.current[0]?.focus();
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setBusy(true);
    try {
      const normalizedEmail = email.trim().toLowerCase();
      if (!normalizedEmail.endsWith("@hvnh.edu.vn")) {
        throw new Error("Hãy sử dụng email @hvnh.edu.vn.");
      }
      if (step === 1) {
        await requestCode(normalizedEmail);
      } else {
        if (otpSeconds <= 0) throw new Error("Mã OTP đã hết hạn. Hãy gửi lại mã mới.");
        if (code.some((digit) => !digit)) throw new Error("Vui lòng nhập đủ 4 chữ số OTP.");
        if (password !== confirmation) throw new Error("Mật khẩu xác nhận chưa khớp.");
        await resetPassword(normalizedEmail, code.join(""), password);
        window.sessionStorage.removeItem("hvnh-password-reset-otp-email");
        window.sessionStorage.removeItem("hvnh-password-reset-otp-expires");
        window.sessionStorage.removeItem("hvnh-password-reset-otp-resend-at");
        setMessage("Đặt lại mật khẩu thành công.");
        window.setTimeout(() => router.replace("/login"), 1000);
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Không thể khôi phục mật khẩu.");
    } finally {
      setBusy(false);
    }
  }

  async function resendCode() {
    if (busy || resendSeconds > 0) return;
    setBusy(true);
    setMessage("");
    try {
      await requestCode(email.trim().toLowerCase(), true);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Không thể gửi lại mã OTP.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className={styles.forgotPasswordForm} onSubmit={submit}>
      <div className={styles.formField}>
        <label htmlFor="forgot-email">Email HVNH</label>
        <input
          id="forgot-email"
          type="email"
          value={email}
          disabled={step === 2}
          onChange={(event) => setEmail(event.target.value)}
          autoComplete="email"
          required
        />
      </div>
      {step === 2 && <>
        <div className={styles.otpField}>
          <label>Mã OTP 4 số</label>
          <div className={styles.otpInputs} role="group" aria-label="Mã OTP gồm 4 chữ số">
            {code.map((digit, index) => (
              <input
                key={index}
                ref={(element) => { inputRefs.current[index] = element; }}
                className={styles.otpInput}
                aria-label={`Chữ số ${index + 1}`}
                inputMode="numeric"
                autoComplete={index === 0 ? "one-time-code" : "off"}
                maxLength={4}
                value={digit}
                onChange={(event) => updateCode(index, event.target.value)}
                onKeyDown={(event) => handleCodeKeyDown(index, event)}
                onPaste={(event) => {
                  const pasted = event.clipboardData.getData("text").replace(/\D/g, "").slice(0, 4);
                  if (!pasted) return;
                  event.preventDefault();
                  const digits = pasted.split("");
                  setCode(digits.concat(["", "", "", ""]).slice(0, 4));
                  inputRefs.current[Math.min(digits.length, 3)]?.focus();
                }}
                required={index === 0}
              />
            ))}
          </div>
          <div className={styles.otpMeta}>
            <span className={otpSeconds > 0 ? "" : styles.expired} role="timer" aria-live="off">
              {otpSeconds > 0 ? `Mã có hiệu lực ${formatTime(otpSeconds)}` : "Mã OTP đã hết hạn"}
            </span>
            <button type="button" onClick={resendCode} disabled={busy || resendSeconds > 0}>
              {resendSeconds > 0 ? `Gửi lại sau ${formatTime(resendSeconds)}` : "Gửi lại mã"}
            </button>
          </div>
        </div>
        <div className={styles.formField}>
          <label htmlFor="new-password">Mật khẩu mới</label>
          <input id="new-password" type="password" minLength={8} autoComplete="new-password" value={password} onChange={(event) => setPassword(event.target.value)} required />
        </div>
        <div className={styles.formField}>
          <label htmlFor="confirm-password">Xác nhận mật khẩu</label>
          <input id="confirm-password" type="password" autoComplete="new-password" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} required />
        </div>
      </>}
      <button className={styles.forgotPasswordSubmit} disabled={busy || (step === 2 && otpSeconds <= 0)}>
        {busy ? "Đang xử lý..." : step === 1 ? "Gửi mã khôi phục" : "Đặt lại mật khẩu"}
      </button>
      {message && <p className={styles.forgotPasswordMessage} role="status">{message}</p>}
    </form>
  );
}
