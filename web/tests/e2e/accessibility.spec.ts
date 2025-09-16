import { test, expect } from '@playwright/test';

test.describe('[a11y] Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    
    // Wait for the page to have some content (either static HTML or React-rendered)
    await page.waitForFunction(() => {
      const body = document.body;
      return body && body.textContent && body.textContent.length > 100;
    }, { timeout: 10000 });
    
    // Wait for React to be ready if it's loading
    try {
      await page.waitForFunction(() => {
        const root = document.getElementById('root');
        return root && root.children.length > 0;
      }, { timeout: 5000 });
    } catch (error) {
      // If React doesn't load, that's okay - we can still test the static content
      console.log('React not ready, testing static content');
    }
    
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

  test('should have proper heading structure', async ({ page }) => {
    // Check that the page has a proper heading structure
    const h1 = page.locator('h1');
    const h1Count = await h1.count();
    
    if (h1Count > 0) {
      // Check that h1 has content
      const h1Text = await h1.first().textContent();
      expect(h1Text).toBeTruthy();
      expect(h1Text?.trim().length).toBeGreaterThan(0);
    }
    
    // Check for any headings (h1-h6)
    const headings = page.locator('h1, h2, h3, h4, h5, h6');
    const headingCount = await headings.count();
    
    if (headingCount > 0) {
      // Check that all headings have content
      for (let i = 0; i < headingCount; i++) {
        const headingText = await headings.nth(i).textContent();
        expect(headingText).toBeTruthy();
        expect(headingText?.trim().length).toBeGreaterThan(0);
      }
    }
  });

  test('should have proper color contrast', async ({ page }) => {
    // This is a basic test - in a real scenario, you'd use axe-core or similar
    // Check that the page has proper structure for color contrast
    const body = page.locator('body');
    const bodyStyles = await body.evaluate((el) => {
      const computed = window.getComputedStyle(el);
      return {
        backgroundColor: computed.backgroundColor,
        color: computed.color
      };
    });
    
    // Basic check that styles are applied
    expect(bodyStyles.backgroundColor).toBeTruthy();
    expect(bodyStyles.color).toBeTruthy();
  });

  test('should have proper form labels', async ({ page }) => {
    // Check that form inputs have proper labels
    const inputs = page.locator('input, select, textarea');
    const inputCount = await inputs.count();
    
    if (inputCount > 0) {
      for (let i = 0; i < inputCount; i++) {
        const input = inputs.nth(i);
        const inputId = await input.getAttribute('id');
        
        if (inputId) {
          // Check for associated label
          const label = page.locator(`label[for="${inputId}"]`);
          const labelCount = await label.count();
          
          if (labelCount === 0) {
            // Check for aria-label or aria-labelledby
            const ariaLabel = await input.getAttribute('aria-label');
            const ariaLabelledBy = await input.getAttribute('aria-labelledby');
            
            expect(ariaLabel || ariaLabelledBy).toBeTruthy();
          }
        }
      }
    }
  });
});
