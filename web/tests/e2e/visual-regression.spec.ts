import { test, expect } from '@playwright/test';

test.describe('Visual Regression Tests', () => {
  test('homepage should match snapshot', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveScreenshot('homepage.png');
  });

  test('dashboard should match snapshot', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveScreenshot('dashboard.png');
  });

  test('call history should match snapshot', async ({ page }) => {
    await page.goto('/call-history');
    await expect(page).toHaveScreenshot('call-history.png');
  });

  test('config page should match snapshot', async ({ page }) => {
    await page.goto('/config');
    await expect(page).toHaveScreenshot('config.png');
  });

  test('mobile view should match snapshot', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await expect(page).toHaveScreenshot('homepage-mobile.png');
  });

  test('tablet view should match snapshot', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/dashboard');
    await expect(page).toHaveScreenshot('dashboard-tablet.png');
  });

  test('dark mode should match snapshot', async ({ page }) => {
    await page.goto('/');
    
    // Toggle dark mode
    await page.click('[data-testid="theme-toggle"]');
    await expect(page).toHaveScreenshot('homepage-dark.png');
  });

  test('form states should match snapshots', async ({ page }) => {
    await page.goto('/config');
    
    // Test form in different states
    await expect(page).toHaveScreenshot('config-form-empty.png');
    
    // Fill form
    await page.fill('input[name="sip_domain"]', 'example.com');
    await page.fill('input[name="sip_user"]', 'testuser');
    await expect(page).toHaveScreenshot('config-form-filled.png');
    
    // Test error state
    await page.fill('input[name="sip_domain"]', '');
    await page.click('button[type="submit"]');
    await expect(page).toHaveScreenshot('config-form-error.png');
  });

  test('loading states should match snapshots', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Simulate loading state
    await page.evaluate(() => {
      document.body.classList.add('loading');
    });
    await expect(page).toHaveScreenshot('dashboard-loading.png');
    
    // Simulate error state
    await page.evaluate(() => {
      document.body.classList.remove('loading');
      document.body.classList.add('error');
    });
    await expect(page).toHaveScreenshot('dashboard-error.png');
  });

  test('data tables should match snapshots', async ({ page }) => {
    await page.goto('/call-history');
    
    // Test table with data
    await expect(page).toHaveScreenshot('call-history-table.png');
    
    // Test table with no data
    await page.evaluate(() => {
      const table = document.querySelector('table');
      if (table) {
        table.innerHTML = '<tbody><tr><td colspan="4">No calls found</td></tr></tbody>';
      }
    });
    await expect(page).toHaveScreenshot('call-history-empty.png');
  });

  test('modal dialogs should match snapshots', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Open modal
    await page.click('[data-testid="open-modal"]');
    await expect(page).toHaveScreenshot('modal-open.png');
    
    // Close modal
    await page.click('[data-testid="close-modal"]');
    await expect(page).toHaveScreenshot('modal-closed.png');
  });
});
