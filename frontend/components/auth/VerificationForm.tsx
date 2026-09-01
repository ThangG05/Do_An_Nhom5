"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

type VerificationFormProps = {
  email: string;
};

export default function VerificationForm({ email }: VerificationFormProps) {
  const [code, setCode] = useState(["", "", "", ""]);
  const [seconds, setSeconds] = useState(60);
  const [message, setMessage] = useState("");
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

  function updateCode(index: number, value: string) {
    const digit = value.replace(/\D/g, "").slice(-1);
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

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (code.some((digit) => !digit)) {
      setMessage("Vui lòng nhập đủ 4 chữ số xác thực.");
      return;
    }
    router.push(`/password?email=${encodeURIComponent(email)}`);
  }

  function resendCode() {
    if (seconds > 0) return;
    setSeconds(60);
    setMessage("Mã xác thực mới đã được gửi.");
  }

  return (
    <form className="verification-form" onSubmit={handleSubmit}>
      <div className="code-inputs" aria-label="Mã xác thực gồm 4 chữ số">
        {code.map((digit, index) => (
          <input
            key={index}
            ref={(element) => {
              inputRefs.current[index] = element;
            }}
            className="code-input"
            inputMode="numeric"
            maxLength={1}
            value={digit}
            aria-label={`Chữ số ${index + 1}`}
            onChange={(event) => updateCode(index, event.target.value)}
            onKeyDown={(event) => handleKeyDown(index, event)}
          />
        ))}
      </div>
      <p className="resend-copy">
        Chưa nhận được mã?{" "}
        <button type="button" onClick={resendCode} disabled={seconds > 0}>
          Gửi lại{" "}
          {seconds > 0 ? `trong 0:${String(seconds).padStart(2, "0")}` : "mã"}
        </button>
      </p>
      <button className="verification-submit" type="submit">
        Tiếp tục
      </button>
      {message ? (
        <p className="verification-message" role="status">
          {message}
        </p>
      ) : null}
    </form>
  );
}
