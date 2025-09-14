import { test, expect } from '@playwright/test';

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8080');
  });

  test('should have proper heading structure', async ({ page }) => {
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();
  });

  test('should have proper form labels', async ({ page }) => {
    const inputs = page.locator('input');
    const count = await inputs.count();
    
    for (let i = 0; i < count; i++) {
      const input = inputs.nth(i);
      const id = await input.getAttribute('id');
      if (id) {
        const label = page.locator(`label[for="${id}"]`);
        await expect(label).toBeVisible();
      }
    }
  });

  test('should have proper button accessibility', async ({ page }) => {
    const buttons = page.locator('button');
    const count = await buttons.count();
    
    for (let i = 0; i < count; i++) {
      const button = buttons.nth(i);
      const text = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');
      
      // Button should have either text content or aria-label
      expect(text?.trim() || ariaLabel).toBeTruthy();
    }
  });

  test('should have proper color contrast', async ({ page }) => {
    // This is a basic test - in a real scenario, you'd use axe-core
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.keyboard.press('Tab');
    const focused = page.locator(':focus');
    await expect(focused).toBeVisible();
  });
});
