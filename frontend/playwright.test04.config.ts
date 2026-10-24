import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests-ui',
  testMatch: 'test04-feedback.spec.ts',
  workers: 1,
  timeout: 60000,
  expect: { timeout: 15000 },
  reporter: 'list',
  use: { baseURL: 'http://localhost:3102', ...devices['Desktop Chrome'], screenshot: 'only-on-failure' },
  webServer: {
    command: 'npm.cmd run dev -- --port 3102',
    url: 'http://localhost:3102/login',
    reuseExistingServer: process.env.PLAYWRIGHT_REUSE_SERVER === '1',
    timeout: 120000,
    env: { NEXT_DIST_DIR: '.next/test04-ui', NEXT_PUBLIC_API_URL: 'http://localhost:8999/api/v1' },
  },
});
