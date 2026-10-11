import Link from "next/link";
import PasswordForm from "@/components/auth/PasswordForm";
import PublicAuthShell from "@/components/auth/PublicAuthShell";

export default function PasswordPage() {
  return <PublicAuthShell step="password" title="Hoàn tất tài khoản" description="Đặt mật khẩu an toàn để bắt đầu trải nghiệm HVNH Hub." backHref="/signup" backLabel="Về đăng ký" footer={<>Đã có tài khoản? <Link href="/login">Đăng nhập</Link></>}>
    <PasswordForm />
  </PublicAuthShell>;
}
