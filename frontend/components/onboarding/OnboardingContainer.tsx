import Link from "next/link";
import CommunityUniverse from "./CommunityUniverse";

const features = [
  { icon: "✦", number: "01", title: "Cập nhật mỗi ngày", description: "Theo dõi những thông tin và hoạt động đáng chú ý trong cộng đồng HVNH." },
  { icon: "◈", number: "02", title: "Hội nhóm theo nhu cầu", description: "Từ học tập, sự kiện đến pass đồ và tìm phòng: tìm đúng nơi để trao đổi." },
  { icon: "✳", number: "03", title: "Hỏi nhanh, có nguồn", description: "Trợ lý AI giúp bạn tra cứu thông tin Học viện với nguồn tham khảo rõ ràng." },
];

export default function OnboardingContainer() {
  return <main className="public-landing">
    <div className="public-landing-glow" aria-hidden="true" />
    <div className="public-landing-container">
      <header className="public-landing-nav">
        <Link href="/" className="public-brand public-brand-light" aria-label="HVNH Hub - Trang chủ"><img src="/assets/logo.png" alt="" /><span>HVNH <b>Hub</b></span></Link>
        <nav aria-label="Điều hướng giới thiệu"><a href="#tinh-nang">Tính năng</a><a href="#cong-dong">Cộng đồng</a></nav>
        <div className="public-landing-nav-actions"><Link href="/login" className="public-nav-login">Đăng nhập</Link><Link href="/signup" className="public-nav-signup">Tham gia ngay <span aria-hidden="true">↗</span></Link></div>
      </header>

      <section className="public-landing-hero" aria-labelledby="public-landing-title">
        <div className="public-landing-copy">
          <span className="public-eyebrow"><i /> NƠI SINH VIÊN HVNH KẾT NỐI</span>
          <h1 id="public-landing-title">Một cộng đồng.<br /><em>Vô vàn kết nối.</em></h1>
          <p>Học hỏi, chia sẻ và khám phá mọi điều đang diễn ra tại Học viện Ngân hàng — cùng những người bạn thuộc về nơi này.</p>
          <div className="public-landing-cta"><Link href="/signup" className="public-landing-primary">Bắt đầu cùng HVNH Hub <span aria-hidden="true">→</span></Link><Link href="/login" className="public-landing-secondary">Tôi đã có tài khoản</Link></div>
          <div className="public-landing-note"><span className="public-note-icons" aria-hidden="true"><i>H</i><i>V</i><i>N</i></span><span>Dành riêng cho email <strong>@hvnh.edu.vn</strong></span></div>
        </div>

        <CommunityUniverse />
      </section>

      <section id="tinh-nang" className="public-landing-features" aria-labelledby="public-features-title"><div className="public-section-heading"><span>KHÁM PHÁ HVNH HUB</span><h2 id="public-features-title">Mọi trải nghiệm sinh viên, <em>gói trong một nơi.</em></h2></div><div className="public-feature-grid">{features.map(feature => <article key={feature.number}><div className="public-feature-top"><span>{feature.icon}</span><small>{feature.number}</small></div><h3>{feature.title}</h3><p>{feature.description}</p></article>)}</div></section>
      <section id="cong-dong" className="public-landing-bottom"><div><span>BẠN ĐÃ SẴN SÀNG?</span><h2>Bắt đầu câu chuyện của bạn tại HVNH.</h2><p>Đăng ký bằng email Học viện hoặc tiếp tục với Google.</p></div><Link href="/signup">Tham gia cộng đồng <span aria-hidden="true">→</span></Link></section>
      <footer className="public-landing-footer"><span>© HVNH Hub · Không gian kết nối sinh viên</span></footer>
    </div>
  </main>;
}
