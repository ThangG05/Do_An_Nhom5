// Local frontend only; mock all API traffic, no DB/R2 writes.
// Usage: node scripts/home-sticky-smoke.cjs
const { chromium, expect } = require('@playwright/test');
const baseURL = process.env.HOME_TEST_URL || 'http://127.0.0.1:3100';
const user = { id: 'u1', email: '26a4041668@hvnh.edu.vn', username: '26a4041668', full_name: 'Nguyen Manh Thang', avatar_url: '/assets/logo.png', system_role: 'USER', admin_group_slugs: [], is_new_user: false };
(async () => {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    await page.addInitScript(user => {
      sessionStorage.setItem('hvnh-hub-access-token', 'home-layout-test');
      sessionStorage.setItem('hvnh-hub-user', JSON.stringify(user));
    }, user);
    await page.route('**/api/v1/**', async route => {
      const headers = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': '*' };
      if (route.request().method() === 'OPTIONS') return route.fulfill({ status: 204, headers });
      const path = new URL(route.request().url()).pathname;
      const data = path.endsWith('/auth/me') ? user : path.endsWith('/system/status') ? { enabled: false }
        : path.includes('header-counts') ? { notifications: 0, messages: 0 } : { items: [], nextCursor: null };
      await route.fulfill({ headers, json: data });
    });
    await page.goto(`${baseURL}/home`);
    await expect(page.locator('.home-user-shortcut')).toBeVisible();
    // Simulate a long feed without depending on seeded posts or live DB data.
    await page.locator('.home-feed').evaluate(el => { el.style.minHeight = '6000px'; });
    for (const height of [900, 480]) {
      await page.setViewportSize({ width: 1440, height });
      for (const y of [600, 2400, 4500]) {
        await page.evaluate(y => window.scrollTo({ top: y, behavior: 'instant' }), y);
        for (const selector of ['.home-left-rail', '.home-side-panel']) {
          await expect.poll(() => page.locator(selector).evaluate(el => Math.round(el.getBoundingClientRect().top))).toBe(86);
          const box = await page.locator(selector).boundingBox();
          expect(box.y + box.height).toBeLessThanOrEqual(height - 15);
        }
      }
      await page.evaluate(() => window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'instant' }));
      for (const selector of ['.home-left-rail', '.home-side-panel']) {
        const box = await page.locator(selector).boundingBox();
        expect(box.y).toBeGreaterThanOrEqual(68);
      }
    }
    const right = page.locator('.home-side-panel');
    await right.evaluate(el => { el.scrollTop = el.scrollHeight; });
    expect(await right.evaluate(el => el.scrollTop)).toBeGreaterThan(0);
    await page.setViewportSize({ width: 1000, height: 800 });
    await expect(page.locator('.home-left-rail')).toBeVisible();
    await expect(right).toBeHidden();
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(page.locator('.home-left-rail')).toBeHidden();
    await expect(right).toBeHidden();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    console.log('PASS: both rails remain visible through deep/end scrolling, short viewport internal scroll, tablet/mobile breakpoints.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
