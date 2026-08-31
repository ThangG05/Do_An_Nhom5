"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  IconInfo,
  IconMarket,
  IconHousing,
  IconEvent,
  IconMessage,
  IconCheck,
  IconMail,
  IconLock,
  IconSend,
} from "@/components/ui/Icons";

export default function AboutPage() {
  const [feedbackName, setFeedbackName] = useState("");
  const [feedbackEmail, setFeedbackEmail] = useState("");
  const [feedbackMsg, setFeedbackMsg] = useState("");
  const [sentStatus, setSentStatus] = useState(false);

  const handleSendFeedback = (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedbackEmail || !feedbackMsg) return;
    setSentStatus(true);
    setTimeout(() => {
      setFeedbackMsg("");
      setSentStatus(false);
      alert("Cảm ơn bạn đã gửi ý kiến đóng góp cho Ban quản trị HVNH Hub!");
    }, 1200);
  };

  const coreModules = [
    {
      title: "Pass Đồ & Chợ Sinh Viên",
      desc: "Mua bán, trao đổi giáo trình, máy tính, tài liệu học tập và đồ dùng cá nhân an toàn dành riêng cho sinh viên BAV.",
      icon: IconMarket,
      badge: "Phân hệ Hot",
    },
    {
      title: "Tìm Trọ & Ghép Phòng",
      desc: "Kết nối nhu cầu tìm phòng trọ, ở ghép xung quanh khu vực Chùa Bộc, Tây Sơn, Phạm Ngọc Thạch và lân cận Học viện.",
      icon: IconHousing,
      badge: "Xác thực vị trí",
    },
    {
      title: "Sự Kiện & Hoạt Động CLB",
      desc: "Cập nhật liên tục các workshop, hội thảo, giải thể thao và chương trình nghệ thuật đến từ Liên chi đoàn & các CLB BAV.",
      icon: IconEvent,
      badge: "Lịch sự kiện",
    },
    {
      title: "Nhắn Tin Realtime (WebSocket)",
      desc: "Hệ thống tin nhắn 1-1 thời gian thực tốc độ cao, hỗ trợ gửi hình ảnh, tệp tin đính kèm và nhận thông báo tức thì.",
      icon: IconMessage,
      badge: "Tốc độ cao",
    },
    {
      title: "Xác Thực Email @hvnh.edu.vn",
      desc: "Chỉ cho phép đăng ký và kích hoạt tài khoản bằng email sinh viên chính thức của Học viện Ngân hàng để đảm bảo uy tín.",
      icon: IconLock,
      badge: "Bảo mật",
    },
    {
      title: "Trợ Lý AI Agent (RAG)",
      desc: "Hệ thống AI thông minh hỗ trợ tra cứu thông tin tuyển sinh, quy chế đào tạo, chương trình học HVNH nhanh chóng và chính xác.",
      icon: IconInfo,
      badge: "AI Hỗ trợ",
    },
  ];

  const techStack = [
    { name: "FastAPI", role: "Backend API Framework" },
    { name: "Next.js & React", role: "Web App Core UI" },
    { name: "PostgreSQL", role: "Chủ sở hữu cơ sở dữ liệu chính" },
    { name: "Cloudflare R2", role: "Lưu trữ đa phương tiện an toàn" },
    { name: "Qdrant & BAAI/bge-m3", role: "Vector DB & Embedding AI Agent" },
    { name: "WebSocket & Redis", role: "Giao tiếp & Chat thời gian thực" },
  ];

  return (
    <main className="info-about-workspace-page">
      <div className="info-about-container">
        {/* 1. Hero Section */}
        <header className="info-hero-card">
          <div className="hero-brand-wrap">
            <img
              src="/assets/logo.png"
              alt="HVNH Hub Shield Logo"
              className="hero-bav-logo-img"
            />
            <span className="hero-badge-pill">Dự án Đồ án Tốt nghiệp 2026</span>
          </div>

          <h1 className="hero-main-title">
            HVNH Hub — Nền Tảng Cộng Đồng Đa Chức Năng Sinh Viên Học Viện Ngân Hàng
          </h1>

          <p className="hero-mission-copy">
            HVNH Hub được phát triển nhằm kiến tạo một môi trường cộng đồng văn minh,
            an toàn và tiện ích dành riêng cho sinh viên Học viện Ngân hàng.
            Ứng dụng hỗ trợ giao thương pass đồ, kết nối phòng trọ, tổng hợp sự kiện
            và tích hợp Trợ lý Trí tuệ Nhân tạo tra cứu thông tin chính thống.
          </p>

          <div className="hero-actions-row">
            <Link href="/groups" className="hero-primary-btn">
              Khám phá Hội nhóm HVNH
            </Link>
            <Link href="/home" className="hero-secondary-btn">
              Về Trang chủ
            </Link>
          </div>
        </header>

        {/* 2. Core Modules Matrix Grid */}
        <section className="info-section-block" aria-labelledby="modules-title">
          <div className="section-header-row">
            <h2 id="modules-title">Tính Năng & Phân Hệ Trọng Tâm</h2>
            <p>Hệ sinh thái dịch vụ chuyên biệt cho nhu cầu sinh viên BAV</p>
          </div>

          <div className="info-modules-grid">
            {coreModules.map((mod) => {
              const Icon = mod.icon;
              return (
                <div key={mod.title} className="info-module-card">
                  <div className="card-top-icon-row">
                    <div className="module-navy-icon-bg">
                      <Icon size={24} color="#1E3A8A" strokeWidth={1.8} />
                    </div>
                    <span className="module-card-chip">{mod.badge}</span>
                  </div>
                  <h3>{mod.title}</h3>
                  <p>{mod.desc}</p>
                </div>
              );
            })}
          </div>
        </section>

        {/* 3. Tech Architecture & Organization */}
        <section className="info-section-block" aria-labelledby="tech-title">
          <div className="section-header-row">
            <h2 id="tech-title">Kiến Trúc Công Nghệ Hệ Thống</h2>
            <p>Xây dựng theo mô hình Client - Backend API - Cloud Data Services</p>
          </div>

          <div className="tech-stack-grid">
            {techStack.map((tech) => (
              <div key={tech.name} className="tech-item-row">
                <IconCheck size={18} color="#2563EB" strokeWidth={2} />
                <div className="tech-item-text">
                  <strong>{tech.name}</strong>
                  <small>{tech.role}</small>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* 4. Community Guidelines & Listing Policies */}
        <section className="info-section-block" aria-labelledby="policy-title">
          <div className="section-header-row">
            <h2 id="policy-title">Quy Định & Chính Sách Cộng Đồng</h2>
            <p>Đảm bảo tính văn minh, tôn trọng và an toàn thông tin</p>
          </div>

          <div className="policy-cards-flex">
            <div className="policy-card">
              <h3>1. Xác thực định danh tài khoản</h3>
              <p>
                Tất cả thành viên bắt buộc đăng ký tài khoản bằng email <code>@hvnh.edu.vn</code> và xác thực trước khi tham gia tương tác, đăng tin pass đồ hay nhắn tin.
              </p>
            </div>
            <div className="policy-card">
              <h3>2. Quy trình kiểm duyệt bài đăng</h3>
              <p>
                Nội dung bài viết trong các hội nhóm (Pass đồ, Tìm trọ, Sự kiện) được kiểm duyệt bởi Ban quản trị nhóm (Group Admin) nhằm loại bỏ thông tin sai sự thật hoặc quảng cáo vi phạm.
              </p>
            </div>
            <div className="policy-card">
              <h3>3. Tiếp nhận báo cáo & xử lý vi phạm</h3>
              <p>
                Hệ thống tiếp nhận báo cáo bài viết/người dùng 24/7. Các hành vi gian lận, lừa đảo pass đồ hoặc spam sẽ bị khóa tài khoản vĩnh viễn bởi Super Admin.
              </p>
            </div>
          </div>
        </section>

        {/* 5. Contact & Feedback Support Form */}
        <section className="info-contact-card" aria-labelledby="contact-title">
          <div className="contact-card-header">
            <IconMail size={28} color="#1E3A8A" />
            <div>
              <h2 id="contact-title">Liên Hệ & Góp Ý Cho Ban Quản Trị</h2>
              <p>Gửi câu hỏi hoặc đóng góp ý kiến để hoàn thiện nền tảng HVNH Hub</p>
            </div>
          </div>

          <form className="info-contact-form" onSubmit={handleSendFeedback}>
            <div className="form-two-col">
              <div className="form-field-wrap">
                <label htmlFor="fb-name">Họ và tên sinh viên</label>
                <input
                  id="fb-name"
                  type="text"
                  placeholder="Ví dụ: Nguyễn Văn A"
                  value={feedbackName}
                  onChange={(e) => setFeedbackName(e.target.value)}
                />
              </div>
              <div className="form-field-wrap">
                <label htmlFor="fb-email">Email Học viện (@hvnh.edu.vn)</label>
                <input
                  id="fb-email"
                  type="email"
                  placeholder="tenban@hvnh.edu.vn"
                  value={feedbackEmail}
                  onChange={(e) => setFeedbackEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-field-wrap">
              <label htmlFor="fb-msg">Nội dung góp ý / Ý kiến phản hồi</label>
              <textarea
                id="fb-msg"
                rows={4}
                placeholder="Nhập nội dung thắc mắc hoặc ý kiến xây dựng ứng dụng..."
                value={feedbackMsg}
                onChange={(e) => setFeedbackMsg(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="contact-submit-btn" disabled={sentStatus}>
              <IconSend size={18} />
              <span>{sentStatus ? "Đang gửi ý kiến..." : "Gửi góp ý ngay"}</span>
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}
