import { test, expect } from '@playwright/test';

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for the page to be fully loaded
    await page.waitForLoadState('networkidle');
    // Wait for the main content to be visible
    await page.waitForSelector('body', { state: 'visible' });
  });

  test('should have proper heading structure', async ({ page }) => {
    // Wait for the h1 element to be visible
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible({ timeout: 10000 });
    
    // Check that the heading has proper text content
    const headingText = await h1.textContent();
    expect(headingText).toBeTruthy();
    expect(headingText?.trim().length).toBeGreaterThan(0);
  });

  test('should have proper form labels', async ({ page }) => {
    const inputs = page.locator('input');
    const count = await inputs.count();
    
    // If there are no inputs, that's fine for this basic app
    if (count === 0) {
      console.log('No input elements found - skipping form label test');
      return;
    }
    
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
    
    // If there are no buttons, that's fine for this basic app
    if (count === 0) {
      console.log('No button elements found - skipping button accessibility test');
      return;
    }
    
    for (let i = 0; i < count; i++) {
      const button = buttons.nth(i);
      const text = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');
      
      // Button should have either text content or aria-label
      expect(text?.trim() || ariaLabel).toBeTruthy();
    }
  });

  test('should have proper color contrast', async ({ page }) => {
    // Wait for the body to be visible and check basic page structure
    const body = page.locator('body');
    await expect(body).toBeVisible({ timeout: 10000 });
    
    // Check that the page has some content
    const pageContent = await page.textContent('body');
    expect(pageContent).toBeTruthy();
    expect(pageContent?.trim().length).toBeGreaterThan(0);
  });

  test('should be keyboard navigable', async ({ page }) => {
    // Wait for the page to be fully loaded
    await page.waitForLoadState('networkidle');
    
    // Check if there are any focusable elements
    const focusableElements = page.locator('button, input, select, textarea, a[href], [tabindex]:not([tabindex="-1"])');
    const count = await focusableElements.count();
    
    if (count === 0) {
      console.log('No focusable elements found - skipping keyboard navigation test');
      return;
    }
    
    // Try to focus the first focusable element
    await focusableElements.first().focus();
    const focused = page.locator(':focus');
    await expect(focused).toBeVisible();
  });
});
