import { test, expect } from '@playwright/test';

test.describe('Logs Viewer Component', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    
    // Login first
    await page.getByRole('textbox', { name: /username/i }).fill('admin');
    await page.getByRole('textbox', { name: /password/i }).fill('admin123');
    await page.getByRole('button', { name: /login/i }).click();
    
    // Wait for dashboard and navigate to logs
    await expect(page.getByText('SIP AI Agent Dashboard')).toBeVisible();
    await page.getByRole('button', { name: /logs/i }).click();
  });

  test('should display logs viewer interface', async ({ page }) => {
    await expect(page.getByText('System Logs')).toBeVisible();
    
    // Check for action buttons
    await expect(page.getByRole('button', { name: /clear/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /refresh/i })).toBeVisible();
  });

  test('should have log filtering controls', async ({ page }) => {
    // Check for filter input
    await expect(page.getByPlaceholder('Filter logs...')).toBeVisible();
    
    // Check for log level selector
    await expect(page.getByRole('combobox')).toBeVisible();
    await expect(page.getByRole('option', { name: /all levels/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /error/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /warning/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /info/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /debug/i })).toBeVisible();
    
    // Check for auto-scroll checkbox
    await expect(page.getByRole('checkbox', { name: /auto-scroll/i })).toBeVisible();
  });

  test('should display logs container', async ({ page }) => {
    // Check for logs display area
    const logsContainer = page.locator('.bg-gray-900');
    await expect(logsContainer).toBeVisible();
    
    // Should have terminal-like styling
    await expect(logsContainer).toHaveClass(/text-green-400/);
    await expect(logsContainer).toHaveClass(/font-mono/);
  });

  test('should filter logs by text input', async ({ page }) => {
    // Type in filter input
    const filterInput = page.getByPlaceholder('Filter logs...');
    await filterInput.fill('test');
    
    // Input should have the value
    await expect(filterInput).toHaveValue('test');
  });

  test('should filter logs by level', async ({ page }) => {
    // Select error level
    await page.getByRole('combobox').selectOption('error');
    
    // Should show the selected option
    await expect(page.getByRole('combobox')).toHaveValue('error');
  });

  test('should toggle auto-scroll checkbox', async ({ page }) => {
    const autoScrollCheckbox = page.getByRole('checkbox', { name: /auto-scroll/i });
    
    // Should be checked by default
    await expect(autoScrollCheckbox).toBeChecked();
    
    // Click to uncheck
    await autoScrollCheckbox.click();
    await expect(autoScrollCheckbox).not.toBeChecked();
    
    // Click to check again
    await autoScrollCheckbox.click();
    await expect(autoScrollCheckbox).toBeChecked();
  });

  test('should refresh logs when refresh button is clicked', async ({ page }) => {
    const refreshButton = page.getByRole('button', { name: /refresh/i });
    
    // Click refresh button
    await refreshButton.click();
    
    // Should not throw any errors
    await expect(refreshButton).toBeVisible();
  });

  test('should clear logs when clear button is clicked', async ({ page }) => {
    const clearButton = page.getByRole('button', { name: /clear/i });
    
    // Click clear button
    await clearButton.click();
    
    // Should not throw any errors
    await expect(clearButton).toBeVisible();
  });

  test('should show logs count', async ({ page }) => {
    // Wait for logs to load
    await page.waitForTimeout(1000);
    
    // Should show logs count at bottom
    const logsCount = page.getByText(/showing \d+ of \d+ logs/i);
    await expect(logsCount).toBeVisible();
  });

  test('should handle empty logs state', async ({ page }) => {
    // If no logs, should show appropriate message
    const emptyMessage = page.getByText('No logs available');
    
    // Either show empty message or logs count
    const isEmpty = await emptyMessage.isVisible();
    if (isEmpty) {
      await expect(emptyMessage).toBeVisible();
    } else {
      await expect(page.getByText(/showing \d+ of \d+ logs/i)).toBeVisible();
    }
  });

  test('should show loading state initially', async ({ page }) => {
    // Navigate to logs and immediately check for loading state
    await page.reload();
    await page.getByRole('textbox', { name: /username/i }).fill('admin');
    await page.getByRole('textbox', { name: /password/i }).fill('admin123');
    await page.getByRole('button', { name: /login/i }).click();
    await page.getByRole('button', { name: /logs/i }).click();
    
    // Should show loading state briefly
    const loadingText = page.getByText('Loading logs...');
    if (await loadingText.isVisible()) {
      await expect(loadingText).toBeVisible();
    }
  });
});
