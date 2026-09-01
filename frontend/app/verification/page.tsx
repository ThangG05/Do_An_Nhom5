import Link from "next/link";
import VerificationForm from "../../components/auth/VerificationForm";

type VerificationPageProps = {
  searchParams: Promise<{ email?: string }>;
};

export default async function VerificationPage({
  searchParams,
}: VerificationPageProps) {
  const params = await searchParams;
  const email = params.email ?? "";

  return (
    <main className="verification-page">
      <section
        className="verification-screen"
        aria-labelledby="verification-title"
      >
        <div className="verification-content">
          {/* <p className="eyebrow">Xác thực tài khoản</p> */}
          <h1 id="verification-title">Nhập mã xác thực</h1>
          <p className="verification-intro">Nhập mã đã được gửi qua email</p>
          <VerificationForm email={email} />
        </div>
        <p className="verification-login">
          Đã có tài khoản? <Link href="/login">Đăng nhập</Link>
        </p>
      </section>
    </main>
  );
}
