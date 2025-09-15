import { test, expect } from '@playwright/test';

test.describe('SIP AI Agent Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    
    // Wait for the React app to load
    await page.waitForFunction(() => {
      const root = document.getElementById('root');
      return root && root.children.length > 0;
    }, { timeout: 10000 });
  });

  test('should display login form initially', async ({ page }) => {
    // Check that login form is visible
    await expect(page.getByRole('textbox', { name: /username/i })).toBeVisible();
    await expect(page.getByRole('textbox', { name: /password/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /login/i })).toBeVisible();
  });

  test('should login successfully with correct credentials', async ({ page }) => {
    // Fill in login form
    await page.getByRole('textbox', { name: /username/i }).fill('admin');
    await page.getByRole('textbox', { name: /password/i }).fill('admin123');
    
    // Submit login form
    await page.getByRole('button', { name: /login/i }).click();
    
    // Wait for dashboard to load
    await expect(page.getByText('SIP AI Agent Dashboard')).toBeVisible();
    await expect(page.getByText('Overview')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    // Fill in invalid credentials
    await page.getByRole('textbox', { name: /username/i }).fill('admin');
    await page.getByRole('textbox', { name: /password/i }).fill('wrongpassword');
    
    // Submit login form
    await page.getByRole('button', { name: /login/i }).click();
    
    // Check for error message
    await expect(page.getByText(/invalid username or password/i)).toBeVisible();
  });

  test('should navigate between tabs after login', async ({ page }) => {
    // Login first
    await page.getByRole('textbox', { name: /username/i }).fill('admin');
    await page.getByRole('textbox', { name: /password/i }).fill('admin123');
    await page.getByRole('button', { name: /login/i }).click();
    
    // Wait for dashboard
    await expect(page.getByText('SIP AI Agent Dashboard')).toBeVisible();
    
    // Test navigation to Call History tab
    await page.getByRole('button', { name: /call history/i }).click();
    await expect(page.getByText('Call History')).toBeVisible();
    
    // Test navigation to Logs tab
    await page.getByRole('button', { name: /logs/i }).click();
    await expect(page.getByText('System Logs')).toBeVisible();
    
    // Test navigation to Configuration tab
    await page.getByRole('button', { name: /configuration/i }).click();
    await expect(page.getByText('Configuration')).toBeVisible();
    
    // Test navigation to Statistics tab
    await page.getByRole('button', { name: /statistics/i }).click();
    await expect(page.getByText('Total Calls')).toBeVisible();
    
    // Test navigation back to Overview
    await page.getByRole('button', { name: /overview/i }).click();
    await expect(page.getByText('Welcome to SIP AI Agent Dashboard')).toBeVisible();
  });

  test('should display status cards on overview tab', async ({ page }) => {
    // Login first
    await page.getByRole('textbox', { name: /username/i }).fill('admin');
    await page.getByRole('textbox', { name: /password/i }).fill('admin123');
    await page.getByRole('button', { name: /login/i }).click();
    
    // Wait for dashboard and check status cards
    await expect(page.getByText('SIP AI Agent Dashboard')).toBeVisible();
    await expect(page.getByText('SIP Registration')).toBeVisible();
    await expect(page.getByText('Active Calls')).toBeVisible();
    await expect(page.getByText('API Tokens Used')).toBeVisible();
    await expect(page.getByText('System Uptime')).toBeVisible();
  });

  test('should toggle dark mode', async ({ page }) => {
    // Login first
    await page.getByRole('textbox', { name: /username/i }).fill('admin');
    await page.getByRole('textbox', { name: /password/i }).fill('admin123');
    await page.getByRole('button', { name: /login/i }).click();
    
    // Wait for dashboard
    await expect(page.getByText('SIP AI Agent Dashboard')).toBeVisible();
    
    // Find and click dark mode toggle
    const darkModeButton = page.getByRole('button', { name: /switch to dark mode/i });
    await expect(darkModeButton).toBeVisible();
    await darkModeButton.click();
    
    // Check that dark mode is applied (body should have dark class)
    await expect(page.locator('body')).toHaveClass(/dark/);
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await page.getByRole('textbox', { name: /username/i }).fill('admin');
    await page.getByRole('textbox', { name: /password/i }).fill('admin123');
    await page.getByRole('button', { name: /login/i }).click();
    
    // Wait for dashboard
    await expect(page.getByText('SIP AI Agent Dashboard')).toBeVisible();
    
    // Click logout button
    await page.getByRole('button', { name: /logout/i }).click();
    
    // Should return to login form
    await expect(page.getByRole('textbox', { name: /username/i })).toBeVisible();
  });
});
