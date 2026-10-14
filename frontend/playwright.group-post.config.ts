import { defineConfig, devices } from '@playwright/test';

// Isolated UI contracts: intercepted API fixtures, no live DB writes or seed data.
export default defineConfig({
  testDir: './tests-ui',
  testMatch: 'group-post.spec.ts',
  workers: 1,
  timeout: 60000,
  expect: { timeout: 15000 },
  reporter: 'list',
  use: { baseURL: 'http://localhost:3101', ...devices['Desktop Chrome'], screenshot: 'only-on-failure', trace: 'retain-on-failure' },
  webServer: {
    command: 'npm.cmd run dev -- --port 3101',
    url: 'http://localhost:3101/login',
    reuseExistingServer: false,
    timeout: 120000,
    env: { NEXT_DIST_DIR: '.next/group-post-ui', NEXT_PUBLIC_API_URL: 'http://localhost:8999/api/v1' },
  },
});
