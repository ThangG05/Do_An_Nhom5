// Run against a local frontend: node scripts/profile-media-smoke.cjs
// All API requests are mocked. This test never writes to the real DB or R2.
const { chromium, expect } = require('@playwright/test');

const baseURL = process.env.PROFILE_TEST_URL || 'http://127.0.0.1:3100';
const authUser = { id: 'u1', email: '26a4041668@hvnh.edu.vn', username: '26a4041668', full_name: 'Nguyen Manh Thang', avatar_url: '/assets/logo.png', system_role: 'USER', admin_group_slugs: [], is_new_user: false };
const cover = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="500"><defs><linearGradient id="g"><stop stop-color="#082847"/><stop offset="1" stop-color="#367eaa"/></linearGradient></defs><path fill="url(#g)" d="M0 0h1400v500H0z"/><circle cx="1100" cy="60" r="240" fill="#ffffff" opacity=".08"/><circle cx="850" cy="380" r="280" fill="#ffffff" opacity=".05"/></svg>');
const initialProfile = { id: 'u1', name: 'Nguyen Manh Thang', username: '26a4041668', studentCode: '26A4041668', avatar: '/assets/logo.png', coverBanner: cover, bio: 'Chia sẻ kiến thức, kết nối cộng đồng HVNH.', faculty: 'Công nghệ thông tin', education: 'Học viện Ngân hàng', joinedDate: '2025-09-15T00:00:00Z', friendsCount: 2, followersCount: 0, mutualFriendsCount: 0, mutualFriendsAvatars: [], friendshipStatus: 'self', socialLinks: {} };

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    let profile = { ...initialProfile };
    let uploadFailed = false;
    const writes = [];
    const pageErrors = [];
    page.on('pageerror', error => pageErrors.push(error.message));
    await page.addInitScript(user => {
      sessionStorage.setItem('hvnh-hub-access-token', 'profile-ui-test');
      sessionStorage.setItem('hvnh-hub-user', JSON.stringify(user));
    }, authUser);
    await page.route('**/api/v1/**', async route => {
      const request = route.request();
      const path = new URL(request.url()).pathname.replace('/api/v1', '');
      const headers = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': '*' };
      if (request.method() === 'OPTIONS') return route.fulfill({ status: 204, headers });
      let data = [];
      if (request.method() !== 'GET') writes.push({ path, method: request.method() });
      if (path === '/auth/me') data = authUser;
      else if (path === '/system/status') data = { enabled: false };
      else if (path.includes('header-counts')) data = { notifications: 0, messages: 0 };
      else if (path === '/media/upload/cover') {
        if (uploadFailed) return route.fulfill({ status: 503, headers, json: { detail: 'Không thể tải ảnh bìa. Vui lòng thử lại.' } });
        data = { media_id: 'cover-test' };
      } else if (path === '/users/me/cover') {
        profile.coverBanner = '/assets/logo.png?cover=updated';
        data = { cover_url: profile.coverBanner };
      } else if (path === '/users/me' || path === '/users/u1') {
        if (request.method() === 'PATCH') Object.assign(profile, request.postDataJSON());
        data = profile;
      } else if (path === '/users/u2') data = { ...profile, id: 'u2', name: 'Nguyễn Quốc Việt', friendshipStatus: 'none' };
      await route.fulfill({ status: 200, headers, json: data });
    });

    await page.goto(`${baseURL}/profile`);
    const coverButton = page.getByRole('button', { name: 'Xem ảnh bìa của Nguyen Manh Thang', exact: true });
    await expect(coverButton).toBeVisible();
    await page.screenshot({ path: '.next/profile-cover-desktop.png', fullPage: true });
    await coverButton.click();
    const viewer = page.getByRole('dialog', { name: 'Ảnh bìa của Nguyen Manh Thang', exact: true });
    await expect(viewer).toBeVisible();
    await expect(viewer.locator('img')).toHaveAttribute('src', cover);
    await page.keyboard.press('Escape');
    await expect(viewer).toHaveCount(0);
    await expect(coverButton).toBeFocused();
    await coverButton.click();
    await viewer.getByRole('button', { name: 'Đổi ảnh bìa', exact: true }).click();
    const editor = page.getByRole('dialog', { name: 'Chỉnh sửa trang cá nhân', exact: true });
    await expect(editor).toBeVisible();
    await expect(editor.getByRole('button', { name: 'Tải ảnh bìa từ máy tính' })).toBeFocused();
    await expect(page.locator('body')).toHaveCSS('overflow', 'hidden');
    await page.keyboard.press('Escape');
    await expect(editor).toHaveCount(0);

    await page.getByRole('button', { name: 'Xem ảnh đại diện của Nguyen Manh Thang', exact: true }).click();
    await expect(page.getByRole('dialog', { name: 'Ảnh đại diện của Nguyen Manh Thang', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Đóng ảnh' }).click();
    await page.getByRole('navigation', { name: 'Điều hướng hồ sơ' }).getByRole('button', { name: 'Ảnh', exact: true }).click();
    await expect(page.locator('.profile-nav-tab-btn.active')).toHaveText('Ảnh');

    // The own-profile-by-ID route must upload cover media too (previous regression).
    await page.goto(`${baseURL}/profile/u1`);
    await page.getByRole('button', { name: 'Đổi ảnh bìa', exact: true }).click();
    const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jXioAAAAASUVORK5CYII=', 'base64');
    await editor.locator('input[type=file]').nth(1).setInputFiles({ name: 'cover.png', mimeType: 'image/png', buffer: png });
    uploadFailed = true;
    await editor.getByRole('button', { name: 'Lưu thay đổi' }).click();
    await expect(editor.getByRole('alert')).toContainText('Không thể tải ảnh bìa');
    await expect(editor).toBeVisible();
    uploadFailed = false;
    await editor.getByRole('button', { name: 'Lưu thay đổi' }).click();
    await expect(editor).toHaveCount(0);
    await expect(page.locator('.cover-banner-img')).toHaveAttribute('src', '/assets/logo.png?cover=updated');
    expect(writes.some(item => item.path === '/media/upload/cover' && item.method === 'POST')).toBeTruthy();
    expect(writes.some(item => item.path === '/users/me/cover' && item.method === 'PUT')).toBeTruthy();

    profile.coverBanner = cover;
    await page.goto(`${baseURL}/profile/u2`);
    await page.getByRole('button', { name: 'Xem ảnh bìa của Nguyễn Quốc Việt', exact: true }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Đổi ảnh bìa', exact: true })).toHaveCount(0);
    await page.keyboard.press('Escape');

    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${baseURL}/profile`);
    await expect(coverButton).toBeVisible();
    await page.screenshot({ path: '.next/profile-cover-mobile.png', fullPage: true });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
    await coverButton.click();
    await expect(viewer).toBeVisible();
    await page.screenshot({ path: '.next/profile-cover-viewer.png' });
    await page.keyboard.press('Escape');
    expect(pageErrors).toEqual([]);
    console.log('PASS: cover/avatar viewer, Escape/focus, focused editor, own-ID upload + retry, visitor permissions, mobile overflow, no browser errors. API mocked; no DB/R2 writes.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
