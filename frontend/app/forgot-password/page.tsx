import Link from "next/link";
import ForgotPasswordForm from "@/components/auth/ForgotPasswordForm";
import PublicAuthShell from "@/components/auth/PublicAuthShell";

export default function ForgotPasswordPage() {
  return <PublicAuthShell step="reset" title="Quên mật khẩu?" description="Nhập email Học viện để nhận hướng dẫn khôi phục tài khoản." backHref="/login" backLabel="Về đăng nhập" footer={<>Nhớ lại mật khẩu? <Link href="/login">Đăng nhập</Link></>}>
    <ForgotPasswordForm />
  </PublicAuthShell>;
}
