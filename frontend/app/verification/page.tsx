import Link from "next/link";
import VerificationForm from "@/components/auth/VerificationForm";
import PublicAuthShell from "@/components/auth/PublicAuthShell";

type VerificationPageProps = { searchParams: Promise<{ email?: string }> };

export default async function VerificationPage({ searchParams }: VerificationPageProps) {
  const { email = "" } = await searchParams;
  return <PublicAuthShell step="verify" title="Kiểm tra email" description="Nhập mã xác thực gồm 4 chữ số chúng tôi vừa gửi đến email của bạn." backHref="/signup" backLabel="Đổi email" footer={<>Chưa nhận được email? Kiểm tra thư rác hoặc <Link href="/signup">thử email khác</Link>.</>}>
    {email && <div className="public-auth-email">Mã được gửi tới <strong>{email}</strong></div>}
    <VerificationForm email={email} />
  </PublicAuthShell>;
}
