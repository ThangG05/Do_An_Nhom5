import Link from "next/link";
import PasswordForm from "../../components/auth/PasswordForm";

export default function PasswordPage() {
  return (
    <main className="password-page">
      <section className="password-screen" aria-labelledby="password-title">
        <div className="password-content">
          <h1 id="password-title">Nhập mật khẩu</h1>
          <p className="password-intro">Giúp bảo vệ tài khoản của bạn</p>
          <PasswordForm />
        </div>
        <p className="password-login">
          Đã có tài khoản? <Link href="/login">Đăng nhập</Link>
        </p>
      </section>
    </main>
  );
}
