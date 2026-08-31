import Link from "next/link";

const decorations = [
  { className: "welcome-dot dot-one", shape: "dot" },
  { className: "welcome-dot dot-two", shape: "dot" },
  { className: "welcome-dot dot-three", shape: "dot" },
  { className: "welcome-star star-one", shape: "star" },
  { className: "welcome-star star-two", shape: "star" },
];

export default function WelcomePage() {
  return (
    <main className="welcome-page">
      <section className="welcome-screen" aria-labelledby="welcome-title">
        <p className="welcome-kicker">HVNH Hub / Welcome</p>
        <div className="welcome-content">
          <div className="welcome-visual" aria-hidden="true">
            <div className="welcome-visual-core" style={{ background: 'transparent' }}>
              <img
                src="/assets/logo.png"
                alt="HVNH Hub Logo"
                style={{ width: '80px', height: 'auto', objectFit: 'contain' }}
              />
            </div>
            {decorations.map((decoration) => (
              <span className={decoration.className} key={decoration.className}>
                {decoration.shape === "star" ? "✦" : ""}
              </span>
            ))}
          </div>
          <h1 id="welcome-title">Chào mừng</h1>
          <p className="welcome-copy">
            Tài khoản HVNH Hub của bạn đã sẵn sàng.
          </p>
          <Link className="welcome-submit" href="/login">
            Tiếp tục
          </Link>
        </div>
        <p className="welcome-footer">
          Bắt đầu kết nối cùng cộng đồng sinh viên HVNH
        </p>
      </section>
    </main>
  );
}
