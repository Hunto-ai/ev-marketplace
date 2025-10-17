const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: 'ci/playwright',
  retries: 0,
  fullyParallel: false,
  timeout: 30000,
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:8000',
    headless: true,
    ignoreHTTPSErrors: true,
  },
});