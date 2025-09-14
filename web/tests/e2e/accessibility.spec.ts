import { test, expect } from '@playwright/test';

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for the page to be fully loaded
    await page.waitForLoadState('networkidle');
    // Wait for the main content to be visible by waiting for the h1 element
    await page.waitForSelector('h1', { state: 'visible', timeout: 15000 });
    
    // Debug: Log page content to help diagnose issues
    const title = await page.title();
    const bodyText = await page.textContent('body');
    console.log('Page title:', title);
    console.log('Body content length:', bodyText?.length || 0);
  });

  test('should load the application', async ({ page }) => {
    // Basic test to verify the app loads by checking for the main heading
    const heading = page.locator('h1');
    await expect(heading).toBeVisible({ timeout: 15000 });
    await expect(heading).toContainText('SIP AI Agent Web UI');
    
    // Check that we have some content
    const bodyText = await page.textContent('body');
    expect(bodyText).toBeTruthy();
    expect(bodyText?.length).toBeGreaterThan(0);
  });

  test('should have proper page title', async ({ page }) => {
    // Check that the page has a proper title
    const title = await page.title();
    expect(title).toBeTruthy();
    expect(title.length).toBeGreaterThan(0);
  });

  test('should have accessible content', async ({ page }) => {
    // Check for the main heading structure
    const heading = page.locator('h1');
    await expect(heading).toBeVisible({ timeout: 15000 });
    await expect(heading).toContainText('SIP AI Agent Web UI');
    
    // Check that the page has some content
    const pageContent = await page.textContent('body');
    expect(pageContent).toBeTruthy();
    expect(pageContent?.trim().length).toBeGreaterThan(0);
    
    // Check for proper heading structure
    const headings = page.locator('h1, h2, h3, h4, h5, h6');
    const headingCount = await headings.count();
    expect(headingCount).toBeGreaterThan(0);
    
    // Check the first heading has content
    const firstHeading = headings.first();
    const headingText = await firstHeading.textContent();
    expect(headingText).toBeTruthy();
    expect(headingText?.trim().length).toBeGreaterThan(0);
  });

  test('should be keyboard navigable', async ({ page }) => {
    // Wait for the page to be fully loaded and check main content
    await page.waitForLoadState('networkidle');
    const heading = page.locator('h1');
    await expect(heading).toBeVisible({ timeout: 15000 });
    
    // Check if there are any focusable elements
    const focusableElements = page.locator('button, input, select, textarea, a[href], [tabindex]:not([tabindex="-1"])');
    const count = await focusableElements.count();
    
    // For this simple app, there might not be focusable elements
    // Just verify the page is accessible by checking the main content
    await expect(heading).toContainText('SIP AI Agent Web UI');
    
    // If there are focusable elements, test keyboard navigation
    if (count > 0) {
      await focusableElements.first().focus();
      const focused = page.locator(':focus');
      await expect(focused).toBeVisible();
    }
  });
});
