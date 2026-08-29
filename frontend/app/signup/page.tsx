import Link from "next/link";
import SignupForm from "../../components/auth/SignupForm";

export default function SignupPage() {
  return (
    <main className="signup-page">
      <section className="signup-screen" aria-labelledby="signup-title">
        <div className="signup-content">
          <h1 id="signup-title">Email</h1>
          <SignupForm />
        </div>
        <p className="signup-login">
          Đã có tài khoản? <Link href="/login">Đăng nhập</Link>
        </p>
      </section>
    </main>
  );
}
