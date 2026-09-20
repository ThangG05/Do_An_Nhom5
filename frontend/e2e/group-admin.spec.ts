import { expect, test } from '@playwright/test';
import { login } from './helpers';
import { readState } from './seed';

test('Group Admin xem hàng chờ, duyệt và ghim bài', async ({ page }) => {
  const state = readState();
  await login(page, state, 'group_admin');
  await page.getByRole('button', { name: /Menu tài khoản/i }).click();
  await page.locator('a[href="/group-admin"]').click();
  await expect(page.locator('.group-admin-hero h1')).toBeVisible();
  await expect(page.locator('.group-admin-hero select')).toHaveValue(state.group.id);

  await page.locator('.group-admin-nav button').nth(1).click();
  const pending = page.locator('.moderation-row').filter({ hasText: 'E2E bài viết đang chờ duyệt' });
  await expect(pending).toBeVisible();
  await pending.locator('button').first().click();
  await expect(pending).toBeHidden();

  await page.locator('.group-admin-nav button').nth(2).click();
  const approved = page.locator('.managed-post').filter({ hasText: 'E2E bài viết đang chờ duyệt' });
  await expect(approved).toBeVisible();
  await approved.locator(':scope > div > button').first().click();
  await expect(approved.locator(':scope > div > button').first()).toContainText(/Bỏ ghim/i);
});
