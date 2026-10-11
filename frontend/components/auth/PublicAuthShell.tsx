import Link from "next/link";
import type { ReactNode } from "react";
import BackArrow from "@/components/ui/BackArrow";

type AuthStep = "login" | "signup" | "verify" | "password" | "reset" | "welcome";

interface PublicAuthShellProps {
  step: AuthStep;
  title: string;
  description: string;
  children: ReactNode;
  footer?: ReactNode;
  backHref?: string;
  backLabel?: string;
}

const steps = ["Tài khoản", "Xác thực", "Hoàn tất"];

export default function PublicAuthShell({ step, title, description, children, footer, backHref = "/", backLabel = "Về trang giới thiệu" }: PublicAuthShellProps) {
  const currentStep = step === "signup" ? 0 : step === "verify" ? 1 : step === "password" || step === "welcome" ? 2 : -1;

  return (
    <main className={`public-auth-page public-auth-${step}`}>
      <div className="public-auth-layout">
        <aside className="public-auth-story" aria-label="Giới thiệu HVNH Hub">
          <Link className="public-brand public-brand-light" href="/" aria-label="HVNH Hub - Trang giới thiệu">
            <img src="/assets/logo.png" alt="" />
            <span>HVNH <b>Hub</b></span>
          </Link>
          <div className="public-auth-story-main">
            <span className="public-eyebrow"><i /> CỘNG ĐỒNG SINH VIÊN HVNH</span>
            <h2>Mọi điều bạn cần ở Học viện, <em>cùng một nơi.</em></h2>
            <p>Khám phá tin tức, trao đổi tài liệu, tham gia hội nhóm và kết nối với bạn bè trong một không gian dành riêng cho sinh viên.</p>
            <div className="public-auth-story-preview" aria-hidden="true">
              <div className="story-preview-top"><span className="story-preview-logo">H</span><span><b>Học tập</b><small>Chia sẻ trong cộng đồng</small></span><span className="story-preview-dot">•••</span></div>
              <div className="story-preview-line long" /><div className="story-preview-line medium" />
              <div className="story-preview-tags"><span>📚 Tài liệu</span><span>💬 Thảo luận</span><span>✨ Trợ lý AI</span></div>
            </div>
          </div>
          <p className="public-auth-story-foot">HVNH Hub · Học hỏi, chia sẻ, kết nối</p>
        </aside>

        <section className="public-auth-main" aria-labelledby="public-auth-title">
          <div className="public-auth-main-top">
            <Link className="public-brand public-brand-dark" href="/" aria-label="HVNH Hub - Trang giới thiệu">
              <img src="/assets/logo.png" alt="" />
              <span>HVNH <b>Hub</b></span>
            </Link>
            <Link className="public-auth-back" href={backHref}><BackArrow size={16} /><span>{backLabel}</span></Link>
          </div>
          <div className="public-auth-card">
            {currentStep >= 0 && <div className="public-auth-progress" aria-label={`Bước ${currentStep + 1} trong 3 bước`}>
              {steps.map((item, index) => <span key={item} className={index <= currentStep ? "current" : ""}><i>{index < currentStep ? "✓" : index + 1}</i>{item}</span>)}
            </div>}
            <div className="public-auth-heading">
              <span className="public-auth-kicker">{step === "login" ? "CHÀO MỪNG TRỞ LẠI" : step === "reset" ? "KHÔI PHỤC TÀI KHOẢN" : step === "welcome" ? "SẴN SÀNG KẾT NỐI" : "THAM GIA HVNH HUB"}</span>
              <h1 id="public-auth-title">{title}</h1>
              <p>{description}</p>
            </div>
            {children}
            {footer && <div className="public-auth-footer">{footer}</div>}
          </div>
          <p className="public-auth-help">Chỉ sử dụng email <strong>@hvnh.edu.vn</strong> để tham gia cộng đồng.</p>
        </section>
      </div>
    </main>
  );
}
