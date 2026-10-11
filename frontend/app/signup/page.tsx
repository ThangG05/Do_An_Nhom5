import Link from "next/link";
import SignupForm from "@/components/auth/SignupForm";
import PublicAuthShell from "@/components/auth/PublicAuthShell";

export default function SignupPage() {
  return <PublicAuthShell step="signup" title="Tạo tài khoản" description="Bắt đầu bằng email Học viện của bạn. Chỉ mất vài phút để tham gia." footer={<>Đã có tài khoản? <Link href="/login">Đăng nhập <span aria-hidden="true">→</span></Link></>}>
    <SignupForm />
  </PublicAuthShell>;
}
