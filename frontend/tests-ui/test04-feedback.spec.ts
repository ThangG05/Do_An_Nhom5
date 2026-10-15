import { expect, test, type Page } from '@playwright/test';

const viewerId = '11111111-1111-4111-8111-111111111111';
const ownerId = '22222222-2222-4222-8222-222222222222';
const friendId = '33333333-3333-4333-8333-333333333333';
const strangerId = '44444444-4444-4444-8444-444444444444';

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
  await page.getByRole('button', { name: /Đã thêm gần đây/ }).click();
  await expect(strangerCard).toHaveCount(0);
  await expect(friendCard).toBeVisible();
});

test('super admin can open reported comments and user accounts', async ({ page }, testInfo) => {
  await setup(page, 'SUPER_ADMIN');
  await page.route('**/api/v1/reports/admin?status=PENDING', route => route.fulfill({ json: [
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
