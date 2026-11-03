"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  requestRegistrationCode,
  verifyRegistrationCode,
} from "@/lib/auth";

type VerificationFormProps = {
  email: string;
};

export default function VerificationForm({ email }: VerificationFormProps) {
  const [code, setCode] = useState(["", "", "", ""]);
  const [seconds, setSeconds] = useState(60);
  const [otpSeconds, setOtpSeconds] = useState(300);
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const inputRefs = useRef<Array<HTMLInputElement | null>>([]);
  const router = useRouter();

  useEffect(() => {
    if (seconds === 0) return;
    const timer = window.setInterval(
      () => setSeconds((value) => value - 1),
      1000,
    );
    return () => window.clearInterval(timer);
  }, [seconds]);

  useEffect(() => {
    const key = `hvnh-registration-otp-expires:${email.toLowerCase()}`;
    const storedExpiry = Number(window.sessionStorage.getItem(key));
    const expiry = Number.isFinite(storedExpiry) && storedExpiry > 0
      ? storedExpiry
      : Date.now() + 5 * 60 * 1000;
    if (!storedExpiry) window.sessionStorage.setItem(key, String(expiry));
    const update = () => {
      const currentExpiry = Number(window.sessionStorage.getItem(key)) || expiry;
      setOtpSeconds(Math.max(0, Math.ceil((currentExpiry - Date.now()) / 1000)));
    };
    update();
    const timer = window.setInterval(update, 1000);
    return () => window.clearInterval(timer);
  }, [email]);

  function updateCode(index: number, value: string) {
    const digits = value.replace(/\D/g, "");
    if (digits.length > 1) {
      const pasted = digits.slice(0, 4).split("");
      setCode(pasted.concat(["", "", "", ""]).slice(0, 4));
      inputRefs.current[Math.min(pasted.length, 3)]?.focus();
      return;
    }
    const digit = digits;
    setCode((current) =>
      current.map((item, itemIndex) => (itemIndex === index ? digit : item)),
    );
    if (digit && index < code.length - 1) inputRefs.current[index + 1]?.focus();
  }

  function handleKeyDown(
    index: number,
    event: React.KeyboardEvent<HTMLInputElement>,
  ) {
    if (event.key === "Backspace" && !code[index] && index > 0)
      inputRefs.current[index - 1]?.focus();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (otpSeconds <= 0) {
      setMessage("Mã xác thực đã hết hạn. Vui lòng gửi lại mã mới.");
      return;
    }
    if (code.some((digit) => !digit)) {
      setMessage("Vui lòng nhập đủ 4 chữ số xác thực.");
      return;
    }
    setIsLoading(true);
    setMessage("");
    try {
      const result = await verifyRegistrationCode(email, code.join(""));
      window.sessionStorage.setItem(
        "hvnh-hub-registration-token",
        result.registration_token,
      );
      window.sessionStorage.setItem("hvnh-hub-registration-name", result.full_name || "");
      window.sessionStorage.setItem("hvnh-hub-registration-requires-name", String(result.requires_full_name));
      router.push("/password");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Mã xác thực không hợp lệ.");
    } finally {
      setIsLoading(false);
    }
  }

  async function resendCode() {
    if (seconds > 0) return;
    setIsLoading(true);
    setMessage("");
    try {
      await requestRegistrationCode(email);
      setSeconds(60);
      const expiry = Date.now() + 5 * 60 * 1000;
      window.sessionStorage.setItem(
        `hvnh-registration-otp-expires:${email.toLowerCase()}`,
        String(expiry),
      );
      setOtpSeconds(300);
      setMessage("Mã xác thực mới đã được gửi.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Không thể gửi lại mã.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <form className="verification-form" onSubmit={handleSubmit}>
      <p className={`otp-expiry${otpSeconds <= 0 ? " is-expired" : ""}`} role="timer" aria-live="off">
        {otpSeconds > 0
          ? `Mã có hiệu lực trong ${Math.floor(otpSeconds / 60)}:${String(otpSeconds % 60).padStart(2, "0")}`
          : "Mã đã hết hạn. Hãy gửi lại mã mới."}
      </p>
      <div className="code-inputs" aria-label="Mã xác thực gồm 4 chữ số">
        {code.map((digit, index) => (
          <input
            key={index}
            ref={(element) => {
              inputRefs.current[index] = element;
            }}
            className="code-input"
            inputMode="numeric"
            maxLength={index === 0 ? 4 : 1}
            autoComplete={index === 0 ? "one-time-code" : "off"}
            value={digit}
            aria-label={`Chữ số ${index + 1}`}
            onChange={(event) => updateCode(index, event.target.value)}
            onKeyDown={(event) => handleKeyDown(index, event)}
            onPaste={(event) => {
              const pasted = event.clipboardData.getData("text").replace(/\D/g, "").slice(0, 4);
              if (!pasted) return;
              event.preventDefault();
              setCode(pasted.split("").concat(["", "", "", ""]).slice(0, 4));
              inputRefs.current[Math.min(pasted.length, 3)]?.focus();
            }}
          />
        ))}
      </div>
      <p className="resend-copy">
        Chưa nhận được mã?{" "}
        <button type="button" onClick={resendCode} disabled={seconds > 0 || isLoading}>
          Gửi lại{" "}
          {seconds > 0 ? `trong 0:${String(seconds).padStart(2, "0")}` : "mã"}
        </button>
      </p>
      <button className="verification-submit" type="submit" disabled={isLoading}>
        {isLoading ? "Đang xác thực…" : "Tiếp tục"}
      </button>
      {message ? (
        <p className="verification-message" role="status">
          {message}
        </p>
      ) : null}
    </form>
  );
}
