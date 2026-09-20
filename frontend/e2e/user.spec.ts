import { expect, test } from '@playwright/test';
import { login } from './helpers';
import { readState } from './seed';

test('User đăng nhập, tạo listing và xem lại trên hồ sơ', async ({ page }) => {
  const state = readState();
  await login(page, state, 'user');
  await expect(page.locator('header.global-navbar-header')).toBeVisible();

  await page.locator('.create-post-card button').first().click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  await dialog.locator('select').first().selectOption('market');
  await dialog.locator('textarea').first().fill('E2E listing giáo trình ngân hàng');
  await dialog.locator('#market-price').fill('125.000đ');
  await dialog.locator('#market-location').fill('Học viện Ngân hàng');
  await dialog.locator('button.submit-post-btn').click();
  await expect(dialog).toBeHidden();

  await page.getByRole('button', { name: /Menu tài khoản/i }).click();
  await page.locator('a[href="/profile"]').click();
  await expect(page.getByText('E2E User', { exact: true }).first()).toBeVisible();
  await page.locator('.profile-nav-tabs-container button').filter({ hasText: /niêm yết/i }).click();
  await expect(page.getByText('E2E listing giáo trình ngân hàng', { exact: true })).toBeVisible();
});
