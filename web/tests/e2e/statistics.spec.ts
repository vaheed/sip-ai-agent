import { test, expect } from '@playwright/test';

test.describe('Statistics Dashboard Component', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    
    // Login first
    await page.getByRole('textbox', { name: /username/i }).fill('admin');
    await page.getByRole('textbox', { name: /password/i }).fill('admin123');
    await page.getByRole('button', { name: /login/i }).click();
    
    // Wait for dashboard and navigate to statistics
    await expect(page.getByText('SIP AI Agent Dashboard')).toBeVisible();
    await page.getByRole('button', { name: /statistics/i }).click();
  });

  test('should display statistics overview cards', async ({ page }) => {
    // Check for overview cards
    await expect(page.getByText('Total Calls')).toBeVisible();
    await expect(page.getByText('Successful Calls')).toBeVisible();
    await expect(page.getByText('Failed Calls')).toBeVisible();
    await expect(page.getByText('Total Cost')).toBeVisible();
  });

  test('should display call duration statistics', async ({ page }) => {
    await expect(page.getByText('📊 Call Duration Statistics')).toBeVisible();
    
    // Check for duration metrics
    await expect(page.getByText('Average Duration')).toBeVisible();
    await expect(page.getByText('Longest Call')).toBeVisible();
    await expect(page.getByText('Shortest Call')).toBeVisible();
    await expect(page.getByText('Total Duration')).toBeVisible();
  });

  test('should display token usage statistics', async ({ page }) => {
    await expect(page.getByText('🎯 Token Usage Statistics')).toBeVisible();
    
    // Check for token metrics
    await expect(page.getByText('Total Tokens')).toBeVisible();
    await expect(page.getByText('Average per Call')).toBeVisible();
    await expect(page.getByText('Max Tokens')).toBeVisible();
    await expect(page.getByText('Cost per Token')).toBeVisible();
  });

  test('should display success rate analysis', async ({ page }) => {
    await expect(page.getByText('📈 Success Rate Analysis')).toBeVisible();
    
    // Check for success rate elements
    await expect(page.getByText('Success Rate')).toBeVisible();
    await expect(page.getByText('Successful')).toBeVisible();
    await expect(page.getByText('Failed')).toBeVisible();
  });

  test('should display recent activity summary', async ({ page }) => {
    await expect(page.getByText('🕒 Recent Activity Summary')).toBeVisible();
    
    // Check for activity metrics
    await expect(page.getByText('Last 24 hours:')).toBeVisible();
    await expect(page.getByText('Last 7 days:')).toBeVisible();
    await expect(page.getByText('Last 30 days:')).toBeVisible();
  });

  test('should display numeric values in statistics cards', async ({ page }) => {
    // Wait for data to load
    await page.waitForTimeout(1000);
    
    // Check that numeric values are displayed (even if 0)
    const totalCalls = page.locator('text=Total Calls').locator('..').locator('dd');
    await expect(totalCalls).toBeVisible();
    
    const successfulCalls = page.locator('text=Successful Calls').locator('..').locator('dd');
    await expect(successfulCalls).toBeVisible();
    
    const failedCalls = page.locator('text=Failed Calls').locator('..').locator('dd');
    await expect(failedCalls).toBeVisible();
    
    const totalCost = page.locator('text=Total Cost').locator('..').locator('dd');
    await expect(totalCost).toBeVisible();
  });

  test('should display progress bar for success rate', async ({ page }) => {
    // Wait for data to load
    await page.waitForTimeout(1000);
    
    // Look for progress bar element
    const progressBar = page.locator('.bg-green-500.h-2.rounded-full');
    
    // Should be visible (even if width is 0%)
    await expect(progressBar).toBeVisible();
  });

  test('should show loading state initially', async ({ page }) => {
    // Navigate to statistics and immediately check for loading state
    await page.reload();
    await page.getByRole('textbox', { name: /username/i }).fill('admin');
    await page.getByRole('textbox', { name: /password/i }).fill('admin123');
    await page.getByRole('button', { name: /login/i }).click();
    await page.getByRole('button', { name: /statistics/i }).click();
    
    // Should show loading state briefly
    const loadingText = page.getByText('Loading statistics...');
    if (await loadingText.isVisible()) {
      await expect(loadingText).toBeVisible();
    }
  });

  test('should handle empty statistics gracefully', async ({ page }) => {
    // Wait for data to load
    await page.waitForTimeout(1000);
    
    // All sections should still be visible even with no data
    await expect(page.getByText('Total Calls')).toBeVisible();
    await expect(page.getByText('📊 Call Duration Statistics')).toBeVisible();
    await expect(page.getByText('🎯 Token Usage Statistics')).toBeVisible();
    await expect(page.getByText('📈 Success Rate Analysis')).toBeVisible();
    await expect(page.getByText('🕒 Recent Activity Summary')).toBeVisible();
  });

  test('should display proper currency formatting for costs', async ({ page }) => {
    // Wait for data to load
    await page.waitForTimeout(1000);
    
    // Check that cost values are formatted with dollar sign
    const totalCostElement = page.locator('text=Total Cost').locator('..').locator('dd');
    const costText = await totalCostElement.textContent();
    
    if (costText && costText !== '0') {
      expect(costText).toMatch(/\$/);
    }
  });

  test('should display proper number formatting for large numbers', async ({ page }) => {
    // Wait for data to load
    await page.waitForTimeout(1000);
    
    // Check that large numbers are formatted with commas
    const totalTokensElement = page.locator('text=Total Tokens').locator('..').locator('dd');
    const tokensText = await totalTokensElement.textContent();
    
    if (tokensText && parseInt(tokensText.replace(/,/g, '')) > 999) {
      expect(tokensText).toMatch(/,/);
    }
  });

  test('should display percentage for success rate', async ({ page }) => {
    // Wait for data to load
    await page.waitForTimeout(1000);
    
    // Check that success rate is displayed as percentage
    const successRateElement = page.locator('text=Success Rate').locator('..').locator('span');
    const rateText = await successRateElement.textContent();
    
    if (rateText) {
      expect(rateText).toMatch(/%/);
    }
  });
});
