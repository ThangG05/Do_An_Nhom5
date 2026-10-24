import { expect, test, type Page } from '@playwright/test';
import type { Post } from '../types/post';

const viewerId = '11111111-1111-4111-8111-111111111111';
const ownerId = '22222222-2222-4222-8222-222222222222';
const friendId = '33333333-3333-4333-8333-333333333333';
const strangerId = '44444444-4444-4444-8444-444444444444';

function samplePost(index: number): Post {
  return { id: `paged-${index}`, content: `Nội dung phân trang ${index}`, category: 'general', privacy: 'public',
    author: { id: ownerId, name: 'Chủ hồ sơ', avatar: '/assets/logo.png' },
    createdAt: '2026-10-01T10:00:00Z', media: [], comments: [], likesCount: 0, commentsCount: 0 };
}

test('group feed and own submissions paginate independently and ignore stale group responses', async ({ page }) => {
  await setup(page);
  const groupA = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
  const groupB = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
  await page.route('**/api/v1/groups', route => route.fulfill({ json: [
    { id: groupA, name: 'Pass đồ', slug: 'pass-do', description: '', member_count: 13, membership: 'MEMBER' },
    { id: groupB, name: 'Sự kiện', slug: 'su-kien', description: '', member_count: 2, membership: 'MEMBER' },
  ] }));
  let slowStarted = false;
  let releaseSlow!: () => void;
  const waitForRelease = new Promise<void>(resolve => { releaseSlow = resolve; });
  await page.route('**/api/v1/groups/*/posts**', async route => {
    const url = new URL(route.request().url());
    if (url.searchParams.get('q') === 'chậm') {
      slowStarted = true;
      await waitForRelease;
      await route.fulfill({ json: [{ ...samplePost(999), status: 'APPROVED' }] });
      return;
    }
    const start = url.pathname.includes(groupB) ? 200 : url.pathname.endsWith('/mine') ? 100 : 0;
    const rows = Array.from({ length: 13 }, (_, index) => ({ ...samplePost(start + index), status: 'APPROVED' }));
    const offset = Number(url.searchParams.get('offset'));
    const limit = Number(url.searchParams.get('limit'));
    await route.fulfill({ json: rows.slice(offset, offset + limit) });
  });
  await page.goto('/groups');
  const feed = page.locator('.live-group-feed');
  await expect(feed.getByText('Nội dung phân trang 0', { exact: true })).toBeVisible();
  await feed.getByRole('button', { name: 'Trang sau' }).click();
  await expect(feed.getByText('Nội dung phân trang 10', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: /^Bài của tôi/ }).click();
  const mine = page.locator('.my-group-posts');
  await expect(mine.getByText('Nội dung phân trang 100', { exact: true })).toBeVisible();
  await mine.getByRole('button', { name: 'Trang sau' }).click();
  await expect(mine.getByText('Nội dung phân trang 110', { exact: true })).toBeVisible();
  await expect(feed.getByText('Nội dung phân trang 10', { exact: true })).toBeVisible();
  await page.getByPlaceholder('Tìm trong nhóm…').fill('chậm');
  await expect.poll(() => slowStarted).toBe(true);
  await page.locator('.live-group-tabs').getByRole('button', { name: /Sự kiện/ }).click();
  await expect(feed.getByText('Nội dung phân trang 200', { exact: true })).toBeVisible();
  const slowResponse = page.waitForResponse(response => new URL(response.url()).searchParams.get('q') === 'chậm');
  releaseSlow();
  await slowResponse;
  await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
  await expect(feed.getByRole('navigation', { name: 'Phân trang bài viết' })).toContainText('Trang 1');
  await expect(feed.getByText('Nội dung phân trang 999', { exact: true })).toHaveCount(0);
});

test('profile requests bounded pages and resets pagination when changing category', async ({ page }) => {
  await setup(page);
  const requests: string[] = [];
  await page.route(`**/api/v1/users/${ownerId}/posts?**`, route => {
    const url = new URL(route.request().url());
    requests.push(url.search);
    const rows = url.searchParams.get('filter') === 'event' ? [] : Array.from({ length: 13 }, (_, i) => samplePost(i));
    const offset = Number(url.searchParams.get('offset'));
    const limit = Number(url.searchParams.get('limit'));
    return route.fulfill({ json: rows.slice(offset, offset + limit) });
  });
  await page.goto(`/profile/${ownerId}`);
  const pager = page.getByRole('navigation', { name: 'Phân trang bài viết' });
  await expect(page.getByText('Nội dung phân trang 0', { exact: true })).toBeVisible();
  await expect(page.getByText('Nội dung phân trang 10', { exact: true })).toHaveCount(0);
  await pager.getByRole('button', { name: 'Trang sau' }).click();
  await expect(page.getByText('Nội dung phân trang 10', { exact: true })).toBeVisible();
  await expect(page.getByText('Nội dung phân trang 0', { exact: true })).toHaveCount(0);
  await expect(pager.getByRole('button', { name: 'Trang sau' })).toBeDisabled();
  await page.getByRole('group', { name: 'Lọc bài viết theo danh mục' }).getByRole('button', { name: 'Sự kiện' }).click();
  await expect(page.getByText('Chưa có bài viết trong mục này')).toBeVisible();
  await expect(pager).toContainText('Trang 1');
  expect(requests.some(query => query.includes('limit=11') && query.includes('offset=10'))).toBeTruthy();
  expect(requests.some(query => query.includes('filter=event') && query.includes('offset=0'))).toBeTruthy();
});

test('failed post page exposes retry without presenting a false empty state', async ({ page }) => {
  await setup(page);
  let fail = true;
  await page.route(`**/api/v1/users/${ownerId}/posts?**`, route => fail
    ? route.fulfill({ status: 503, json: { detail: 'Lỗi tải trang bài viết kiểm thử' } })
    : route.fulfill({ json: [samplePost(0)] }));
  await page.goto(`/profile/${ownerId}`);
  const alert = page.getByRole('alert').filter({ hasText: 'Lỗi tải trang bài viết kiểm thử' });
  await expect(alert).toBeVisible();
  await expect(page.getByText('Chưa có bài viết nào', { exact: true })).toHaveCount(0);
  fail = false;
  await alert.getByRole('button', { name: 'Thử lại' }).click();
  await expect(page.getByText('Nội dung phân trang 0', { exact: true })).toBeVisible();
});

async function setup(page: Page, role: 'USER' | 'SUPER_ADMIN' = 'USER') {
  const user = { id: viewerId, email: 'viewer@hvnh.edu.vn', username: 'viewer', full_name: 'Người đang xem', avatar_url: '/assets/logo.png', system_role: role, admin_group_slugs: [], is_new_user: false };
  const owner = { id: ownerId, name: 'Chủ hồ sơ', username: 'owner', avatar: '/assets/logo.png', coverBanner: '/assets/logo.png', bio: '', studentCode: '26A4041668', joinedDate: '2026-09-01T00:00:00Z', friendsCount: 3, followersCount: 0, mutualFriendsCount: 0, mutualFriendsAvatars: [], friendshipStatus: 'friends' };
  const daysAgo = (days: number) => new Date(Date.now() - days * 86400000).toISOString();
  const friends = [
    { id: viewerId, name: 'Người đang xem', username: 'viewer', avatar: '/assets/logo.png', mutualCount: 0, currentCity: 'Hà lội', connectedAt: daysAgo(3), friendshipStatus: 'self' },
    { id: friendId, name: 'Bạn chung', username: 'friend', avatar: '/assets/logo.png', mutualCount: 1, connectedAt: daysAgo(4), friendshipStatus: 'friends' },
    { id: strangerId, name: 'Chưa kết bạn', username: 'stranger', avatar: '/assets/logo.png', mutualCount: 0, connectedAt: daysAgo(20), friendshipStatus: 'none' },
  ];
  await page.addInitScript(value => {
    sessionStorage.setItem('hvnh-hub-access-token', 'test-ui-only');
    sessionStorage.setItem('hvnh-hub-user', JSON.stringify(value));
  }, user);
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname.replace('/api/v1', '');
    let body: unknown = [];
    if (path === '/auth/me') body = user;
    else if (path === '/system/status') body = { enabled: false };
    else if (path === `/users/${ownerId}` || path === '/users/me') body = { ...owner, id: path === '/users/me' ? viewerId : ownerId, friendshipStatus: path === '/users/me' ? 'self' : 'friends' };
    else if (path.includes('/friends') && route.request().method() === 'GET') body = friends;
    else if (path === `/users/${strangerId}/friendship`) body = { status: 'pending_sent' };
    else if (path.endsWith('/unread-count')) body = { count: 0 };
    await route.fulfill({ status: 200, json: body });
  });
}

test('friend cards use the viewer relationship, and recent means seven days', async ({ page }, testInfo) => {
  await setup(page);
  await page.goto(`/profile/${ownerId}`);
  await page.getByRole('button', { name: 'Xem tất cả bạn bè' }).click();
  const ownCard = page.locator('.friend-matrix-card').filter({ hasText: 'Người đang xem' });
  const friendCard = page.locator('.friend-matrix-card').filter({ hasText: 'Bạn chung' });
  const strangerCard = page.locator('.friend-matrix-card').filter({ hasText: 'Chưa kết bạn' });
  await expect(ownCard.getByRole('link', { name: 'Nhắn tin' })).toHaveCount(0);
  await expect(friendCard.getByRole('link', { name: 'Nhắn tin' })).toBeVisible();
  await expect(strangerCard.getByRole('button', { name: 'Thêm bạn bè' })).toBeVisible();
  await strangerCard.getByRole('button', { name: 'Thêm bạn bè' }).click();
  await expect(strangerCard.getByRole('button', { name: 'Hủy lời mời' })).toBeVisible();
  await expect(page.locator('.friends-location-filters')).toContainText('Hà Nội');
  await expect(page.locator('.friends-location-filters')).not.toContainText('Hà lội');
  await page.screenshot({ path: testInfo.outputPath('friends.png') });
  // Recent connections are private to the owner, not exposed on another profile.
  await expect(page.getByRole('button', { name: /Đã thêm gần đây/ })).toHaveCount(0);
  await page.goto('/profile');
  await page.getByRole('button', { name: 'Xem tất cả bạn bè' }).click();
  await page.getByRole('button', { name: /Đã thêm gần đây/ }).click();
  await expect(strangerCard).toHaveCount(0);
  await expect(friendCard).toBeVisible();
});

test('global search suggests matching names and opens the selected profile', async ({ page }) => {
  await setup(page);
  await page.route('**/api/v1/users/search?**', async route => {
    const query = new URL(route.request().url()).searchParams.get('q') || '';
    await route.fulfill({ json: query.toLowerCase().includes('nguyen manh') ? [{
      id: viewerId, name: 'Nguyen Manh Thang', username: '26a4041668',
      studentCode: '26a4041668', avatar: '/assets/logo.png',
      faculty: 'Khoa Công nghệ thông tin', mutualCount: 0, friendshipStatus: 'self',
    }] : [] });
  });
  await page.goto('/home');
  const search = page.getByRole('combobox', { name: 'Tìm kiếm sinh viên' });
  await search.fill('Nguyen Manh');
  await expect(page.getByRole('option', { name: /Nguyen Manh Thang/ })).toBeVisible();
  await search.press('ArrowDown');
  await expect(search).toHaveAttribute('aria-activedescendant', 'global-user-search-item-0');
  await search.press('Enter');
  await expect(page).toHaveURL(new RegExp(`/profile/${viewerId}$`));
  await page.goto('/home');
  await search.fill('Nguyen Manh');
  await expect(page.getByRole('option', { name: /Nguyen Manh Thang/ })).toBeVisible();
  await search.press('Enter');
  await expect(page).toHaveURL(/\/search\?q=Nguyen(?:%20|\+)Manh$/);
  await expect(page.getByRole('link', { name: /Nguyen Manh Thang/ })).toBeVisible();
});

test('profile does not present a failed friends request as an empty list', async ({ page }) => {
  await setup(page);
  let attempts = 0;
  let allowSuccess = false;
  await page.route(`**/api/v1/users/${ownerId}/friends?**`, async route => {
    attempts += 1;
    if (!allowSuccess) {
      await route.fulfill({ status: 503, json: { detail: 'Tạm thời không tải được bạn bè.' } });
      return;
    }
    await route.fulfill({ status: 200, json: [
      { id: friendId, name: 'Bạn chung', username: 'friend', avatar: '/assets/logo.png', mutualCount: 1, connectedAt: new Date().toISOString(), friendshipStatus: 'friends' },
    ] });
  });
  await page.goto(`/profile/${ownerId}`);
  await expect(page.getByRole('alert').filter({ hasText: 'Không tải được danh sách bạn bè.' })).toBeVisible();
  allowSuccess = true;
  await page.getByRole('button', { name: 'Thử lại' }).click();
  await expect(page.getByText('Bạn chung')).toBeVisible();
  expect(attempts).toBeGreaterThanOrEqual(2);
});

test('super admin can open reported comments and user accounts', async ({ page }, testInfo) => {
  await setup(page, 'SUPER_ADMIN');
  await page.route('**/api/v1/reports/admin?status=OPEN', route => route.fulfill({ json: [
    { id: 'report-1', reporter_id: viewerId, reporter_name: 'Người báo cáo', target_type: 'COMMENT', target_id: 'comment-1', reason: 'Nội dung sai lệch', status: 'PENDING', group_id: null, group_name: null, target_summary: 'Bình luận cần kiểm tra', evidence_url: null, resolution_note: null, created_at: new Date().toISOString(), handled_at: null },
    { id: 'report-2', reporter_id: viewerId, reporter_name: 'Người báo cáo', target_type: 'USER', target_id: ownerId, reason: 'Giả mạo', status: 'PENDING', group_id: null, group_name: null, target_summary: 'Chủ hồ sơ', evidence_url: null, resolution_note: null, created_at: new Date().toISOString(), handled_at: null },
  ] }));
  await page.route('**/api/v1/reports/admin/report-1', route => route.fulfill({ json: { post: { id: 'post-1', author: { id: ownerId, name: 'Chủ bài viết', avatar: '/assets/logo.png' }, createdAt: new Date().toISOString(), content: 'Nội dung bài viết gốc', category: 'general', privacy: 'public', media: [], likesCount: 0, commentsCount: 1 }, comment: { id: 'comment-1', author: { id: friendId, name: 'Người bình luận', avatar: '/assets/logo.png' }, content: 'Bình luận cần kiểm tra', createdAt: new Date().toISOString() }, user: null } }));
  await page.route('**/api/v1/reports/admin/report-2', route => route.fulfill({ json: { post: null, comment: null, user: { id: ownerId, name: 'Chủ hồ sơ', avatar: '/assets/logo.png', student_code: '26A4041668', joined_at: '2026-09-01T00:00:00Z', status: 'ACTIVE' } } }));
  await page.goto('/admin/reports');
  await page.getByRole('button', { name: 'Xem bình luận bị báo cáo' }).click();
  const detail = page.getByRole('dialog', { name: 'Bình luận bị báo cáo' });
  await expect(detail.getByText('Nội dung bài viết gốc')).toBeVisible();
  await expect(detail.getByText('Bình luận cần kiểm tra')).toBeVisible();
  await expect(detail.getByText('Người bình luận')).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath('reported-comment.png') });
  await detail.getByRole('button', { name: 'Đóng chi tiết' }).click();
  await page.getByRole('button', { name: 'Xem tài khoản bị báo cáo' }).click();
  await expect(page.getByRole('dialog', { name: 'Tài khoản bị báo cáo' }).getByText('Mã sinh viên: 26A4041668')).toBeVisible();
});
