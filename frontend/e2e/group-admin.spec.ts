import { expect, test } from '@playwright/test';
import { login } from './helpers';
import { readState } from './seed';

test('Group Admin xem hàng chờ, duyệt và ghim bài', async ({ page }) => {
  const state = readState();
  await login(page, state, 'group_admin');
  await expect(page.locator('.group-admin-hero h1')).toContainText(state.group.name);

  await page.locator('.group-admin-nav button').nth(1).click();
  const pending = page.locator('.pending-group-post').filter({ hasText: 'E2E bài viết đang chờ duyệt' });
  await expect(pending).toBeVisible();
  await expect(pending.locator('.pending-group-post-avatar')).toBeVisible();
  await expect(pending.locator('time')).toBeVisible();
  await pending.getByRole('button', { name: 'Phê duyệt' }).click();
  await expect(pending).toBeHidden();

  await page.locator('.group-admin-nav button').nth(2).click();
  const approved = page.locator('.managed-post').filter({ hasText: 'E2E bài viết đang chờ duyệt' });
  await expect(approved).toBeVisible();
  await approved.getByRole('button', { name: 'Tùy chọn bài viết' }).click();
  await approved.getByRole('button', { name: 'Ghim bài' }).click();
  await approved.getByRole('button', { name: 'Tùy chọn bài viết' }).click();
  await expect(approved.getByRole('button', { name: 'Bỏ ghim bài' })).toBeVisible();
});
