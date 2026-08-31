import Link from "next/link";
import LoginForm from "../../components/auth/LoginForm";

export default function Login() {
  return (
    <main className="login-page">
      <section className="login-panel" aria-labelledby="login-title">
        <Link className="login-back" href="/">
          ← Quay lại
        </Link>
        <div className="auth-brand-header">
          <img
            src="/assets/logo.png"
            alt="HVNH Hub Logo"
            className="auth-brand-logo"
          />
          <h2 className="auth-brand-title">HVNH Hub</h2>
        </div>
        <h1 id="login-title">Đăng nhập</h1>
        <p className="login-intro">
          Sử dụng email Học viện để tiếp tục vào cộng đồng HVNH.
        </p>
        <LoginForm />
        <p className="login-register">
          Chưa có tài khoản? <Link href="/signup">Đăng ký ngay</Link>
        </p>
      </section>
    </main>
  );
}
