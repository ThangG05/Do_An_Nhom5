"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { fetchSystemStatus } from "@/lib/api";
import { formatFullDateTime } from "@/lib/dateTime";
import type { MaintenanceState } from "@/types/system";

export default function MaintenancePage() {
  const router = useRouter();
  const checkingRef = useRef(false);
  const [state, setState] = useState<MaintenanceState | null>(null);
  const [error, setError] = useState("");
  const [checking, setChecking] = useState(true);

  const checkStatus = useCallback(async () => {
    if (checkingRef.current) return;
    checkingRef.current = true;
    setChecking(true);
    try {
      const next = await fetchSystemStatus();
      setState(next);
      setError("");
      if (!next.enabled) router.replace("/home");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể kiểm tra trạng thái hệ thống.");
    } finally {
      checkingRef.current = false;
      setChecking(false);
    }
  }, [router]);

  useEffect(() => {
    void checkStatus();
    const timer = window.setInterval(() => void checkStatus(), 30_000);
    return () => window.clearInterval(timer);
  }, [checkStatus]);

  return (
    <main className="maintenance-page">
      <section aria-busy={checking}>
        <img src="/assets/logo.png" alt="HVNH Hub" />
        <span>HVNH HUB</span>
        <h1>Hệ thống đang bảo trì</h1>
        <p>{state?.message || "Chúng tôi đang nâng cấp hệ thống để phục vụ bạn tốt hơn."}</p>
        {state?.expected_end_at && <strong title={formatFullDateTime(state.expected_end_at)}>Dự kiến hoàn thành: {formatFullDateTime(state.expected_end_at)}</strong>}
        {error ? (
          <div className="maintenance-check-error" role="alert">
            <small>{error}</small>
            <button type="button" onClick={() => void checkStatus()} disabled={checking}>{checking ? "Đang kiểm tra..." : "Thử kiểm tra lại"}</button>
          </div>
        ) : <small>{checking ? "Đang kiểm tra trạng thái hệ thống..." : "Trang sẽ tự động kiểm tra lại sau mỗi 30 giây."}</small>}
        <Link href="/login">Đăng nhập quản trị</Link>
      </section>
    </main>
  );
}
