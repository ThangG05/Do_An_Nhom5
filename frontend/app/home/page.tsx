"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const [checked, setChecked] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (
      window.sessionStorage.getItem("hvnh-hub-mock-authenticated") !== "true"
    ) {
      router.replace("/login");
      return;
    }
    setChecked(true);
  }, [router]);

  if (!checked)
    return <main className="home-loading" aria-label="Đang tải trang chủ" />;

  return (
    <main className="home-page">
      <aside className="home-sidebar">
        <a
          className="home-sidebar-brand"
          href="/home"
          aria-label="HVNH Hub, về trang chủ"
        >
          <span className="sidebar-shield">
            BAV<small>1961</small>
          </span>
          <span>HVNH Hub</span>
        </a>
        <nav className="home-sidebar-nav" aria-label="Điều hướng chính">
          <Link className="current" href="/home">
            ⌂ <span>Trang chủ</span>
          </Link>
          <Link href="/market">
            ♧ <span>Pass đồ</span>
          </Link>
          <Link href="/create">
            + <span>Tạo bài viết</span>
          </Link>
          <Link href="/messages">
            □ <span>Tin nhắn</span>
          </Link>
          <Link href="/profile">
            ◎ <span>Hồ sơ</span>
          </Link>
        </nav>
        <p className="sidebar-note">
          Không gian chung cho sinh viên Học viện Ngân hàng.
        </p>
      </aside>

      <div className="home-content">
        <header className="home-topbar">
          <div className="desktop-page-title">
            <span>Trang chủ</span>
            <strong>Bảng tin HVNH</strong>
          </div>
          <form className="home-search" role="search">
            <span aria-hidden="true">⌕</span>
            <input
              aria-label="Tìm kiếm bài viết"
              placeholder="Tìm kiếm trong cộng đồng"
            />
          </form>
          <button type="button" aria-label="Thông báo">
            ♧
          </button>
        </header>

        <section className="home-welcome">
          <p>Cộng đồng HVNH</p>
          <h1>Chào mừng trở lại</h1>
          <span>Khám phá những điều mới trong trường hôm nay.</span>
        </section>

        <div className="home-layout">
          <section className="home-feed" aria-label="Bài viết mới">
            <article>
              <div className="feed-author">
                <span className="feed-avatar">H</span>
                <strong>Học viện Ngân Hàng</strong>
                <small>1 giờ trước</small>
              </div>
              <p>TUYỂN SINH CHƯƠNG TRÌNH TIẾN SĨ UWE BRISTOL</p>
              <img
                src="https://picsum.photos/seed/hvnh-admission/900/560"
                alt="Thông tin tuyển sinh Học viện Ngân Hàng"
              />
            </article>
            <article>
              <div className="feed-author">
                <span className="feed-avatar warm">A</span>
                <strong>Abdul Quayyum</strong>
                <small>1 giờ trước</small>
              </div>
              <p>Tìm bạn ở ghép gần Học viện, ưu tiên sinh viên HVNH.</p>
              <img
                src="https://picsum.photos/seed/hvnh-student/900/560"
                alt="Bài đăng tìm bạn ở ghép"
              />
            </article>
          </section>
          <aside className="home-side-panel">
            <h2>Khám phá cộng đồng</h2>
            <p>
              Tham gia các nhóm phù hợp với lịch học và mối quan tâm của bạn.
            </p>
            <Link href="/market">Xem các nhóm</Link>
          </aside>
        </div>
      </div>

      <nav className="home-nav" aria-label="Điều hướng mobile">
        <Link href="/home" aria-label="Trang chủ">
          ⌂
        </Link>
        <Link href="/market" aria-label="Pass đồ">
          ♧
        </Link>
        <Link href="/create" aria-label="Tạo bài viết">
          +
        </Link>
        <Link href="/messages" aria-label="Tin nhắn">
          □
        </Link>
        <Link href="/profile" aria-label="Hồ sơ">
          ◎
        </Link>
      </nav>
    </main>
  );
}
