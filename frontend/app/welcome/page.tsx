import Link from "next/link";
import PublicAuthShell from "@/components/auth/PublicAuthShell";

export default function WelcomePage() {
  return <PublicAuthShell step="welcome" title="Chào mừng đến HVNH Hub!" description="Tài khoản của bạn đã sẵn sàng. Hãy bắt đầu khám phá cộng đồng sinh viên HVNH." backHref="/" backLabel="Trang giới thiệu">
    <div className="public-welcome-mark" aria-hidden="true">✓</div>
    <Link className="public-auth-primary-link" href="/login">Tiếp tục đăng nhập <span aria-hidden="true">→</span></Link>
  </PublicAuthShell>;
}
