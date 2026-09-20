import { defineConfig, devices } from '@playwright/test';
import path from 'node:path';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  timeout: 45_000,
  expect: { timeout: 10_000 },
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? [['line'], ['html', { open: 'never' }]] : [['list'], ['html', { open: 'never' }]],
  globalSetup: './e2e/global-setup.ts',
  globalTeardown: './e2e/global-teardown.ts',
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3100',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: '..\\.venv\\Scripts\\python.exe -m uvicorn src.main:app --port 8100',
      cwd: path.resolve(__dirname, '../backend'),
      url: 'http://127.0.0.1:8100/api/v1/auth/health',
      reuseExistingServer: true,
      timeout: 120_000,
      env: {
        ...process.env,
        CORS_ORIGINS: 'http://localhost:3100',
        RAG_CRAWLER_BACKGROUND_ENABLED: 'false',
      },
    },
    {
      command: 'npm.cmd run dev -- --port 3100',
      cwd: __dirname,
      url: 'http://127.0.0.1:3100/login',
      reuseExistingServer: true,
      timeout: 120_000,
      env: { ...process.env, NEXT_DIST_DIR: '.next-e2e', NEXT_PUBLIC_API_URL: process.env.E2E_API_URL || 'http://127.0.0.1:8100/api/v1' },
    },
  ],
});
