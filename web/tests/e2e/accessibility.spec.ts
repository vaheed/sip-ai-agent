import { test, expect } from '@playwright/test';

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    
    // Wait for the page to have some content (either static HTML or React-rendered)
    await page.waitForFunction(() => {
      const body = document.body;
      return body && body.textContent && body.textContent.length > 100;
    }, { timeout: 10000 });
    
    // Debug: Log page content to help diagnose issues
    const title = await page.title();
    const bodyText = await page.textContent('body');
    console.log('Page title:', title);
    console.log('Body content length:', bodyText?.length || 0);
  });

  test('should load the application', async ({ page }) => {
    // Check that the page loads and has content
    const bodyText = await page.textContent('body');
    expect(bodyText).toBeTruthy();
    expect(bodyText?.length).toBeGreaterThan(0);
    
    // Check that the page title is correct
    const title = await page.title();
    expect(title).toContain('SIP AI Agent');
  });

  test('should have proper page title', async ({ page }) => {
    // Check that the page has a proper title
    const title = await page.title();
    expect(title).toBeTruthy();
    expect(title.length).toBeGreaterThan(0);
    expect(title).toContain('SIP AI Agent');
  });

  test('should have accessible content', async ({ page }) => {
    // Check that the page has some content
    const pageContent = await page.textContent('body');
    expect(pageContent).toBeTruthy();
    expect(pageContent?.trim().length).toBeGreaterThan(0);
    
    // Check that the page has a proper structure (HTML elements)
    const html = await page.content();
    expect(html).toContain('<html');
    expect(html).toContain('<head');
    expect(html).toContain('<body');
    
    // Check for any headings (if they exist)
    const headings = page.locator('h1, h2, h3, h4, h5, h6');
    const headingCount = await headings.count();
    
    // If there are headings, check they have content
    if (headingCount > 0) {
      const firstHeading = headings.first();
      const headingText = await firstHeading.textContent();
      expect(headingText).toBeTruthy();
      expect(headingText?.trim().length).toBeGreaterThan(0);
    }
  });

  test('should be keyboard navigable', async ({ page }) => {
    // Check if there are any focusable elements
    const focusableElements = page.locator('button, input, select, textarea, a[href], [tabindex]:not([tabindex="-1"])');
    const count = await focusableElements.count();
    
    // If there are focusable elements, test keyboard navigation
    if (count > 0) {
      // Test keyboard navigation
      await focusableElements.first().focus();
      const focused = page.locator(':focus');
      await expect(focused).toBeVisible();
      
      // Test tab navigation if there are multiple focusable elements
      if (count > 1) {
        await page.keyboard.press('Tab');
        const nextFocused = page.locator(':focus');
        await expect(nextFocused).toBeVisible();
      }
    } else {
      // If no focusable elements, just verify the page is accessible
      const bodyText = await page.textContent('body');
      expect(bodyText).toBeTruthy();
      expect(bodyText?.length).toBeGreaterThan(0);
    }
  });
});
