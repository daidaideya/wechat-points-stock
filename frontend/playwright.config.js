import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  testMatch: process.env.REAL_BACKEND_E2E ? '**/real-backend.spec.js' : '**/smoke.spec.js',
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  // The smoke suite shares one Vite dev server across browser projects. A
  // single worker keeps Firefox/WebKit module-style requests deterministic.
  workers: 1,
  reporter: process.env.CI ? [['line'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: 'http://127.0.0.1:4173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 4173',
    cwd: '.',
    url: 'http://127.0.0.1:4173/app/access-gate',
    // A stale local Vite process can keep an old dependency optimizer cache
    // after npm install. Reuse is opt-in so each smoke run starts from a
    // server that matches the current lockfile and source tree.
    reuseExistingServer: process.env.PW_REUSE_SERVER === '1',
    timeout: 120_000,
  },
})
