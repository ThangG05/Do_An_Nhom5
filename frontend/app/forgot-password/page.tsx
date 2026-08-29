// import Link from "next/link";
// import ForgotPasswordForm from "../../components/auth/ForgotPasswordForm";

// export default function ForgotPasswordPage() {
//   return (
//     <main className="forgot-password-page">
//       <section
//         className="forgot-password-screen"
//         aria-labelledby="forgot-password-title"
//       >
//         <div className="forgot-password-content">
//           <h1 id="forgot-password-title">Quên mật khẩu</h1>
//           <p className="forgot-password-intro">
//             Cùng khôi phục lại mật khẩu của bạn nhé
//           </p>
//           <ForgotPasswordForm />
//         </div>
//         <p className="forgot-password-register">
//           Chưa có tài khoản? <Link href="/signup">Đăng ký</Link>
//         </p>
//       </section>
//     </main>
//   );
// }

import Link from "next/link";
import ForgotPasswordForm from "../../components/auth/ForgotPasswordForm.tsx";

export default function ForgotPasswordPage() {
  return (
    <main className="login-page">
      <section className="login-panel">
        <Link href="/login" className="login-back">
          ← Quay lại
        </Link>
        <h1 id="forgot-password-title">Quên mật khẩu</h1>
        <p className="login-intro">
          Cùng khôi phục lại mật khẩu của bạn nhé
        </p>
        
        <ForgotPasswordForm />

        <p className="login-register">
          Chưa có tài khoản? <Link href="/signup">Đăng ký ngay</Link>
        </p>
      </section>
    </main>
  );
}
