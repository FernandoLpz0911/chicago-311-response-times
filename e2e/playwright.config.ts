import { defineConfig, devices } from '@playwright/test';

// Optional: a Socrata app token raises the portal's rate limits.
const appToken = process.env.SOCRATA_APP_TOKEN;

export default defineConfig({
  timeout: 60_000,
  expect: { timeout: 15_000 },
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI
    ? [['html', { open: 'never' }], ['github']]
    : [['html', { open: 'never' }], ['list']],
  use: {
    baseURL: 'https://data.cityofchicago.org',
    trace: 'on-first-retry',
    extraHTTPHeaders: appToken ? { 'X-App-Token': appToken } : {},
  },
  projects: [
    { name: 'api', testDir: './tests/api' },
    { name: 'ui', testDir: './tests/ui', use: { ...devices['Desktop Chrome'] } },
  ],
});
