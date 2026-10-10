"use client";

import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function SettingsPage() {
  const router = useRouter();

  return (
    <main className="account-settings-page">
      <section className="account-settings-shell" aria-labelledby="settings-title">
        <header className="account-settings-header">
          <button type="button" onClick={() => router.back()} aria-label="Quay lại">←</button>
          <div>
            <span>TRUNG TÂM TÀI KHOẢN</span>
            <h1 id="settings-title">Cài đặt và quyền riêng tư</h1>
            <p>Quản lý hồ sơ, bảo mật và những người bạn không muốn tương tác.</p>
          </div>
        </header>

        <div className="account-settings-grid">
          <Link href="/profile" className="account-settings-card">
            <span className="account-settings-icon" aria-hidden="true">👤</span>
            <div><strong>Thông tin cá nhân</strong><p>Cập nhật tên, khoa, nơi ở và liên kết mạng xã hội.</p></div>
            <b aria-hidden="true">›</b>
          </Link>
          <Link href="/settings/password" className="account-settings-card">
            <span className="account-settings-icon" aria-hidden="true">🔐</span>
            <div><strong>Mật khẩu và bảo mật</strong><p>Đổi mật khẩu và thu hồi các phiên đăng nhập cũ.</p></div>
            <b aria-hidden="true">›</b>
          </Link>
          <Link href="/settings/blocked" className="account-settings-card">
            <span className="account-settings-icon" aria-hidden="true">🛡️</span>
            <div><strong>Danh sách đã chặn</strong><p>Xem và quản lý các tài khoản bạn đã chặn.</p></div>
            <b aria-hidden="true">›</b>
          </Link>
        </div>
      </section>
    </main>
  );
}
