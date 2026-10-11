import Link from "next/link";
import LoginForm from "@/components/auth/LoginForm";
import PublicAuthShell from "@/components/auth/PublicAuthShell";

export default function LoginPage() {
  return <PublicAuthShell step="login" title="Đăng nhập" description="Tiếp tục cùng cộng đồng sinh viên Học viện Ngân hàng." footer={<>Chưa có tài khoản? <Link href="/signup">Đăng ký ngay <span aria-hidden="true">→</span></Link></>}>
    <LoginForm />
  </PublicAuthShell>;
}
