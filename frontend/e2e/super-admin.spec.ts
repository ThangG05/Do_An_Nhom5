import { expect, test } from '@playwright/test';
import { login } from './helpers';
import { readState } from './seed';

test('Super Admin vào dashboard, quản lý tài khoản và xem audit log', async ({ page }) => {
  const state = readState();
  await login(page, state, 'super_admin');
  await expect(page.locator('.admin-shell')).toBeVisible();
  await expect(page.locator('.admin-overview-metrics')).toBeVisible();

  await page.locator('.admin-sidebar a[href="/admin/users"]').click();
  await expect(page).toHaveURL(/\/admin\/users$/);
  await page.locator('.admin-users input').fill(state.emails.target);
  const target = page.locator('.admin-user-list article').filter({ hasText: state.emails.target });
  await expect(target).toBeVisible();

  page.once('dialog', async dialog => dialog.accept('Cảnh báo từ Playwright E2E'));
  await target.locator('.discipline-actions button').first().click();
  await expect(target.locator('.discipline-actions button').first()).toContainText('(1)');

  await page.locator('.admin-sidebar a[href="/admin/audit"]').click();
  await expect(page).toHaveURL(/\/admin\/audit$/);
  await expect(page.locator('.admin-console')).toContainText(/USER_WARN|cảnh báo/i);
});
