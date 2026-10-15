import { test, expect, type Page } from '@playwright/test';

const user = { id: '11111111-1111-4111-8111-111111111111', email: 'test@hvnh.edu.vn', username: 'test', full_name: 'Sinh viên kiểm thử', avatar_url: '/assets/logo.png', system_role: 'USER', admin_group_slugs: [], is_new_user: false };
const groups = [
  { id: 'market', name: 'Pass đồ', slug: 'pass-do', description: 'Mua bán, trao đổi đồ dùng sinh viên' },
  { id: 'event', name: 'Sự kiện', slug: 'su-kien', description: 'Tin tức và các hoạt động sinh viên' },
  { id: 'roommate', name: 'Ghép phòng', slug: 'ghep-phong-tim-tro', description: 'Tìm phòng và bạn cùng phòng' },
  { id: 'study', name: 'Học tập', slug: 'hoc-tap', description: 'Chia sẻ kiến thức và tài liệu' },
].map(group => ({ ...group, membership: 'MEMBER', member_count: 12 }));

async function setup(page: Page, rejectSubmit = false) {
  const submissions: Record<string, any>[] = [];
  await page.addInitScript(user => {
    sessionStorage.setItem('hvnh-hub-access-token', 'test-ui-only');
    sessionStorage.setItem('hvnh-hub-user', JSON.stringify(user));
  }, user);
  await page.route('**/api/v1/**', async route => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace('/api/v1', '');
    let body: unknown = [];
    if (path === '/auth/me') body = user;
    else if (path === '/system/status') body = { enabled: false };
    else if (path === '/groups') body = groups;
    else if (path.endsWith('unread-count')) body = { count: 0 };
    else if (route.request().method() === 'POST' && (/\/groups\/[^/]+\/posts$/.test(path) || path === '/users/me/posts')) {
      const payload = route.request().postDataJSON(); submissions.push(payload);
      if (rejectSubmit) { await route.fulfill({ status: 422, json: { detail: [{ msg: 'Máy chủ yêu cầu kiểm tra lại nội dung.' }] } }); return; }
      body = { id: 'created', ...payload, author: { id: user.id, name: user.full_name, avatar: user.avatar_url }, media: [], likesCount: 0, commentsCount: 0, privacy: 'public', category: path.split('/')[2] || payload.category, groupId: path.split('/')[2], groupName: 'Nhóm kiểm thử', status: 'PENDING', createdAt: new Date().toISOString() };
    }
    await route.fulfill({ status: 200, json: body });
  });
  return submissions;
}

async function openGroup(page: Page, category: string) {
  await page.goto('/groups?group=' + category);
  await page.getByRole('button', { name: '＋ Tạo bài viết', exact: true }).click();
  await expect(page.getByRole('dialog', { name: /Tạo bài/ })).toBeVisible();
}

test('market: validation, optional description, free price, preview and one submission', async ({ page }) => {
  const sent = await setup(page);
  await openGroup(page, 'market');
  await page.getByRole('button', { name: 'Gửi bài chờ duyệt', exact: true }).click();
  await expect(page.getByLabel('Tên vật phẩm')).toBeFocused();
  await expect(page.getByText('Vui lòng nhập tên vật phẩm.', { exact: true })).toBeVisible();
  expect(sent).toHaveLength(0);
  await page.getByLabel('Tên vật phẩm').fill('Bàn phím Keychron K6');
  await page.getByLabel('Giá bán (VNĐ)').fill('0');
  await page.getByLabel('Vị trí', { exact: false }).first().fill('Đống Đa, Hà Nội');
  await expect(page.getByText('Tặng miễn phí')).toBeVisible();
  await page.getByRole('button', { name: 'Xem trước', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Bàn phím Keychron K6' })).toBeVisible();
  await page.getByRole('button', { name: 'Gửi bài chờ duyệt', exact: true }).click();
  await expect(page.getByRole('dialog', { name: /Tạo bài/ })).not.toBeVisible();
  expect(sent).toHaveLength(1);
  expect(sent[0]).toMatchObject({ form_version: 2, content: '', media_ids: [], marketListing: { productName: 'Bàn phím Keychron K6', price: '0', location: 'Đống Đa, Hà Nội' } });
});

for (const category of ['event', 'roommate', 'study']) {
  test(category + ': required structured fields are sent to the group endpoint', async ({ page }) => {
    const sent = await setup(page);
    await openGroup(page, category);
    await page.locator('#gp-content').fill('Nội dung chia sẻ có ích cho sinh viên.');
    if (category === 'event') {
      await page.getByLabel('Tên sự kiện').fill('Ngày hội kết nối');
      await page.getByLabel('Ngày diễn ra').fill('2026-12-20');
      await page.getByLabel('Giờ bắt đầu').fill('18:30');
    }
    if (category === 'study') await page.getByLabel('Tên môn học').fill('Giải tích 1');
    else await page.locator('#gp-location').fill('Học viện Ngân hàng');
    await page.getByRole('button', { name: 'Gửi bài chờ duyệt', exact: true }).click();
    await expect(page.getByRole('dialog', { name: /Tạo bài/ })).not.toBeVisible();
    expect(sent).toHaveLength(1);
    expect(sent[0].form_version).toBe(2);
    expect(sent[0].media_ids).toEqual([]);
    if (category === 'study') expect(sent[0].studyListing.subjectName).toBe('Giải tích 1');
    if (category === 'roommate') expect(sent[0].roomListing.rentPerMonth).toBe('');
    if (category === 'event') expect(sent[0].eventListing.eventTime).toBe('18:30');
  });
}

test('server failure keeps draft and presents readable error; files preview and limits', async ({ page }) => {
  await setup(page, true);
  await openGroup(page, 'study');
  await page.getByLabel('Tên môn học').fill('Kinh tế vĩ mô');
  await page.locator('#gp-content').fill('Tổng hợp chương 1');
  await page.getByRole('button', { name: 'Gửi bài chờ duyệt', exact: true }).click();
  await expect(page.getByRole('dialog', { name: /Tạo bài/ }).getByRole('alert')).toContainText('Máy chủ yêu cầu kiểm tra lại nội dung.');
  await expect(page.getByLabel('Tên môn học')).toHaveValue('Kinh tế vĩ mô');
  await page.locator('input[type=file]').setInputFiles({ name: 'bai-tap.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-1.4 test') });
  await expect(page.getByRole('button', { name: 'Xóa bai-tap.pdf' })).toBeVisible();
  await expect(page.locator('video')).toHaveCount(0);
  await page.locator('input[type=file]').setInputFiles(Array.from({ length: 10 }, (_, i) => ({ name: 'file-' + i + '.txt', mimeType: 'text/plain', buffer: Buffer.from('test') })));
  await expect(page.getByRole('dialog', { name: /Tạo bài/ }).getByRole('alert')).toContainText('tối đa 10 tệp');
  await expect(page.getByRole('button', { name: 'Xóa bai-tap.pdf' })).toBeVisible();
});

test('desktop and narrow dark layouts keep fields, preview and submit reachable', async ({ page }, testInfo) => {
  await setup(page);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openGroup(page, 'event');
  await page.getByLabel('Tên sự kiện').fill('Movie Night — Xem phim & giao lưu');
  await page.locator('#gp-content').fill('Cùng nhau xem phim, gặp gỡ bạn mới và chia sẻ những câu chuyện đáng nhớ.');
  await page.getByLabel('Ngày diễn ra').fill('2026-12-20');
  await page.getByLabel('Giờ bắt đầu').fill('18:00');
  await page.locator('#gp-location').fill('Hội trường A, Học viện Ngân hàng');
  await page.screenshot({ path: testInfo.outputPath('desktop.png') });
  await page.evaluate(() => { document.documentElement.dataset.theme = 'dark'; });
  await page.screenshot({ path: testInfo.outputPath('desktop-dark.png') });
  await page.setViewportSize({ width: 390, height: 844 });
  const shell = page.getByRole('dialog', { name: /Tạo bài/ });
  expect(await shell.evaluate(el => el.scrollWidth <= el.clientWidth + 1)).toBeTruthy();
  await page.getByRole('button', { name: 'Xem trước', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Movie Night — Xem phim & giao lưu' })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath('narrow-dark.png') });
  await page.getByRole('button', { name: '← Chỉnh sửa', exact: true }).click();
  await expect(page.getByLabel('Tên sự kiện')).toHaveValue('Movie Night — Xem phim & giao lưu');
  await page.keyboard.press('Escape');
  await expect(shell).not.toBeVisible();
});

test('home composer switches category forms and preserves entered fields', async ({ page }, testInfo) => {
  await setup(page);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/home');
  await page.getByRole('button', { name: 'Sự kiện', exact: true }).click();
  await page.getByLabel('Tên sự kiện').fill('Ngày hội sinh viên');
  const destinations = page.getByRole('navigation', { name: 'Chọn nơi đăng bài' });
  await destinations.getByRole('button', { name: /^Học tập/ }).click();
  await expect(page.getByLabel('Tên môn học')).toBeVisible();
  await expect(page.getByLabel('Tên sự kiện')).toHaveCount(0);
  await destinations.getByRole('button', { name: /^Sự kiện/ }).click();
  await expect(page.getByLabel('Tên sự kiện')).toHaveValue('Ngày hội sinh viên');
  await page.screenshot({ path: testInfo.outputPath('home-category-picker.png') });
});

test('approved group cards show typed metadata instead of only body text', async ({ page }) => {
  await setup(page);
  await page.route('**/api/v1/groups/event/posts?*', route => route.fulfill({ json: [{ id: 'event-post', author: { id: user.id, name: user.full_name, avatar: user.avatar_url }, category: 'event', content: 'Mời các bạn cùng tham gia.', eventListing: { eventName: 'Ngày hội việc làm', eventDate: '2026-12-20', eventTime: '08:00', location: 'Sân trường' }, status: 'APPROVED', privacy: 'public', groupId: 'event', groupName: 'Sự kiện', media: [], createdAt: '2026-10-14T08:00:00Z', likesCount: 0, commentsCount: 0 }] }));
  await page.goto('/groups?group=event');
  await expect(page.getByRole('heading', { name: 'Ngày hội việc làm' })).toBeVisible();
  await expect(page.getByText('20/12/2026 · 08:00 (giờ Việt Nam)')).toBeVisible();
  await expect(page.getByText('Sân trường', { exact: false })).toBeVisible();
});

test('home composer only offers groups the user has joined', async ({ page }) => {
  await setup(page);
  await page.route('**/api/v1/groups', route => route.fulfill({ json: groups.map(group => ({ ...group, membership: ['event', 'study'].includes(group.id) ? 'MEMBER' : 'NONE' })) }));
  await page.goto('/home');
  await page.getByRole('button', { name: 'Sự kiện', exact: true }).click();
  const destinations = page.getByRole('navigation', { name: 'Chọn nơi đăng bài' });
  await expect(destinations.getByRole('button', { name: /^Sự kiện/ })).toBeVisible();
  await expect(destinations.getByRole('button', { name: /^Học tập/ })).toBeVisible();
  await expect(destinations.getByRole('button', { name: /^Pass đồ/ })).toHaveCount(0);
  await expect(destinations.getByRole('button', { name: /^Ghép phòng/ })).toHaveCount(0);
  await expect(page.getByText('Đăng trong Sự kiện · Chờ quản trị viên duyệt')).toBeVisible();
});

test('home composer directs users to join when they open an unjoined group shortcut', async ({ page }) => {
  await setup(page);
  await page.route('**/api/v1/groups', route => route.fulfill({ json: groups.map(group => ({ ...group, membership: 'NONE' })) }));
  await page.goto('/home');
  await page.getByRole('button', { name: 'Sự kiện', exact: true }).click();
  await expect(page.getByText('Bạn chưa tham gia nhóm nào.')).toBeVisible();
  await expect(page.getByRole('link', { name: /Khám phá và tham gia nhóm/ })).toBeVisible();
  await expect(page.getByText('Bạn cần tham gia nhóm trước khi đăng bài.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Gửi bài chờ duyệt', exact: true })).toBeDisabled();
});
