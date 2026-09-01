import Link from "next/link";
import SignupForm from "../../components/auth/SignupForm";

export default function SignupPage() {
  return (
    <main className="signup-page">
      <section className="signup-screen" aria-labelledby="signup-title">
        <div className="auth-brand-header">
          <img
            src="/assets/logo.png"
            alt="HVNH Hub Logo"
            className="auth-brand-logo"
          />
          <h2 className="auth-brand-title">HVNH Hub</h2>
        </div>
        <div className="signup-content">
          <h1 id="signup-title">Đăng ký tài khoản</h1>
          <SignupForm />
        </div>
        <p className="signup-login">
          Đã có tài khoản? <Link href="/login">Đăng nhập</Link>
        </p>
      </section>
    </main>
  );
}
