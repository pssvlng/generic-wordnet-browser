import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: process.env['E2E_BASE_URL'] || 'http://127.0.0.1:4200',
    browserName: 'chromium',
    launchOptions: process.env['CHROME_BIN'] ? { executablePath: process.env['CHROME_BIN'] } : {},
    trace: 'retain-on-failure',
  },
});
