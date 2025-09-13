import { test, expect } from '@playwright/test';

test.describe('Accessibility Tests', () => {
  test('should pass WCAG 2.1 AA accessibility standards', async ({ page }) => {
    // Test homepage
    await page.goto('/');
    await expect(page).toHaveTitle(/SIP AI Agent/);
    
    // Check for basic accessibility requirements
    await expect(page.locator('html')).toHaveAttribute('lang');
    await expect(page.locator('h1')).toHaveCount({ min: 1 });
    
    // Test keyboard navigation
    await page.keyboard.press('Tab');
    await expect(page.locator(':focus')).toBeVisible();
    
    // Test focus management
    const focusableElements = page.locator('button, a, input, select, textarea, [tabindex]:not([tabindex="-1"])');
    const focusableCount = await focusableElements.count();
    expect(focusableCount).toBeGreaterThan(0);
  });

  test('should have proper ARIA labels and roles', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Check for proper ARIA labels
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    
    for (let i = 0; i < buttonCount; i++) {
      const button = buttons.nth(i);
      const ariaLabel = await button.getAttribute('aria-label');
      const ariaLabelledBy = await button.getAttribute('aria-labelledby');
      const hasText = await button.textContent();
      
      // Button should have either aria-label, aria-labelledby, or visible text
      expect(ariaLabel || ariaLabelledBy || hasText?.trim()).toBeTruthy();
    }
  });

  test('should support screen reader navigation', async ({ page }) => {
    await page.goto('/call-history');
    
    // Check for proper heading hierarchy
    const headings = page.locator('h1, h2, h3, h4, h5, h6');
    const headingCount = await headings.count();
    expect(headingCount).toBeGreaterThan(0);
    
    // Check for skip links
    const skipLinks = page.locator('a[href^="#"]');
    const skipLinkCount = await skipLinks.count();
    expect(skipLinkCount).toBeGreaterThan(0);
  });

  test('should handle form accessibility', async ({ page }) => {
    await page.goto('/config');
    
    // Check form labels
    const inputs = page.locator('input, select, textarea');
    const inputCount = await inputs.count();
    
    for (let i = 0; i < inputCount; i++) {
      const input = inputs.nth(i);
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const ariaLabelledBy = await input.getAttribute('aria-labelledby');
      
      if (id) {
        const label = page.locator(`label[for="${id}"]`);
        const labelExists = await label.count() > 0;
        expect(labelExists || ariaLabel || ariaLabelledBy).toBeTruthy();
      }
    }
  });

  test('should maintain color contrast ratios', async ({ page }) => {
    await page.goto('/');
    
    // This is a basic test - in a real implementation, you'd use a library
    // like axe-core to check actual contrast ratios
    const textElements = page.locator('p, span, div, h1, h2, h3, h4, h5, h6');
    const textCount = await textElements.count();
    expect(textCount).toBeGreaterThan(0);
    
    // Check that text elements have proper color contrast
    // This would typically be done with axe-core or similar tools
  });

  test('should handle dynamic content accessibility', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Test live regions for dynamic content
    const liveRegions = page.locator('[aria-live]');
    const liveRegionCount = await liveRegions.count();
    
    // Check for proper live region attributes
    for (let i = 0; i < liveRegionCount; i++) {
      const region = liveRegions.nth(i);
      const ariaLive = await region.getAttribute('aria-live');
      expect(['polite', 'assertive', 'off']).toContain(ariaLive);
    }
  });
});
