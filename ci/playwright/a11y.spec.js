const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

const routes = [
  '/',
  '/listings/',
  '/listings/demo-2024-tesla-model-3-rwd/',
  '/dealers/demo-ev-hub/',
  '/guides/buyers-checklist/',
];

test.describe('accessibility smoke', () => {
  for (const route of routes) {
    test(`axe scan for ${route}`, async ({ page }) => {
      await page.goto(route, { waitUntil: 'networkidle' });
      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();
      const violations = results.violations.filter((item) =>
        ['critical', 'serious'].includes(item.impact)
      );
      expect(violations).toEqual([]);
    });
  }
});
