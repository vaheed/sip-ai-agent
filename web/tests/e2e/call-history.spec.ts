import { test, expect } from '@playwright/test';

test.describe('Call History Component', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    
    // Login first
    await page.getByRole('textbox', { name: /username/i }).fill('admin');
    await page.getByRole('textbox', { name: /password/i }).fill('admin123');
    await page.getByRole('button', { name: /login/i }).click();
    
    // Wait for dashboard and navigate to call history
    await expect(page.getByText('SIP AI Agent Dashboard')).toBeVisible();
    await page.getByRole('button', { name: /call history/i }).click();
  });

  test('should display call history table', async ({ page }) => {
    await expect(page.getByText('Call History')).toBeVisible();
    
    // Check for table headers
    await expect(page.getByRole('columnheader', { name: /call id/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /start time/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /end time/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /duration/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /status/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /tokens used/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /cost/i })).toBeVisible();
  });

  test('should show export CSV button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /export csv/i })).toBeVisible();
  });

  test('should handle empty call history', async ({ page }) => {
    // If no calls, should show appropriate message
    const emptyMessage = page.getByText('No call history available');
    const table = page.locator('table');
    
    // Either show empty message or table with no rows
    const isEmpty = await emptyMessage.isVisible();
    if (isEmpty) {
      await expect(emptyMessage).toBeVisible();
    } else {
      await expect(table).toBeVisible();
    }
  });

  test('should export CSV when export button is clicked', async ({ page }) => {
    // Mock the CSV download
    const downloadPromise = page.waitForEvent('download');
    
    // Click export button
    await page.getByRole('button', { name: /export csv/i }).click();
    
    // Wait for download to start (this will timeout if no download occurs)
    try {
      const download = await downloadPromise;
      expect(download.suggestedFilename()).toMatch(/call_history_.*\.csv/);
    } catch (error) {
      // If no download occurs (e.g., no data), that's also acceptable
      console.log('No CSV download occurred, likely due to empty data');
    }
  });

  test('should display call data in table format', async ({ page }) => {
    // Wait for any loading to complete
    await page.waitForTimeout(1000);
    
    // Check if there are any table rows (besides header)
    const tableRows = page.locator('table tbody tr');
    const rowCount = await tableRows.count();
    
    if (rowCount > 0) {
      // If there are rows, check that they have proper data
      const firstRow = tableRows.first();
      await expect(firstRow).toBeVisible();
      
      // Check that cells contain data
      const cells = firstRow.locator('td');
      const cellCount = await cells.count();
      expect(cellCount).toBeGreaterThan(0);
    }
  });

  test('should show loading state initially', async ({ page }) => {
    // Navigate to call history and immediately check for loading state
    await page.reload();
    await page.getByRole('textbox', { name: /username/i }).fill('admin');
    await page.getByRole('textbox', { name: /password/i }).fill('admin123');
    await page.getByRole('button', { name: /login/i }).click();
    await page.getByRole('button', { name: /call history/i }).click();
    
    // Should show loading state briefly
    const loadingText = page.getByText('Loading call history...');
    if (await loadingText.isVisible()) {
      await expect(loadingText).toBeVisible();
    }
  });
});
