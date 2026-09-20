import { expect, type Page } from '@playwright/test';
import type { E2EState } from './seed';

export async function login(page: Page, state: E2EState, role: keyof E2EState['emails']): Promise<void> {
  // Each role must start without access data or a rotated refresh cookie from
  // an earlier identity, otherwise initial unread-count calls may race refresh.
  await page.context().clearCookies();
  await page.goto('/login');
  await page.evaluate(() => {
    window.sessionStorage.clear();
    window.localStorage.clear();
  });
  await page.locator('input[name="email"]').fill(state.emails[role]);
  await page.locator('input[name="password"]').fill(state.password);
  await page.locator('button[type="submit"]').click();
  await expect(page).toHaveURL(role === 'super_admin' ? /\/admin$/ : /\/home$/);
}
