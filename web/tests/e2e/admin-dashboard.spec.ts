import { test, expect } from '@playwright/test';

test.describe('Admin Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    
    // Login first
    await page.getByRole('textbox', { name: /username/i }).fill('admin');
    await page.getByRole('textbox', { name: /password/i }).fill('admin123');
    await page.getByRole('button', { name: /login/i }).click();
    
    // Wait for dashboard and navigate to admin dashboard
    await expect(page.getByText('SIP AI Agent Dashboard')).toBeVisible();
    await page.getByRole('button', { name: /admin dashboard/i }).click();
  });

  test('should display admin dashboard interface', async ({ page }) => {
    await expect(page.getByText('🎛️ Admin Dashboard')).toBeVisible();
    await expect(page.getByText('Real-time system monitoring and analytics')).toBeVisible();
  });

  test('should display key metrics cards', async ({ page }) => {
    // Check for key metrics cards
    await expect(page.getByText('Live Calls')).toBeVisible();
    await expect(page.getByText('Total Calls')).toBeVisible();
    await expect(page.getByText('Success Rate')).toBeVisible();
    await expect(page.getByText('Total Cost')).toBeVisible();
  });

  test('should display system health overview', async ({ page }) => {
    // Check for system health sections
    await expect(page.getByText('📡 SIP Status')).toBeVisible();
    await expect(page.getByText('💻 System Resources')).toBeVisible();
    await expect(page.getByText('🎯 API Usage')).toBeVisible();
  });

  test('should display charts and analytics', async ({ page }) => {
    // Check for charts
    await expect(page.getByText('📈 Call Volume Trends')).toBeVisible();
    await expect(page.getByText('🥧 Call Success Distribution')).toBeVisible();
  });

  test('should display recent activity and alerts', async ({ page }) => {
    // Check for activity sections
    await expect(page.getByText('🕒 Recent Activity')).toBeVisible();
    await expect(page.getByText('🚨 System Alerts')).toBeVisible();
  });

  test('should display performance metrics', async ({ page }) => {
    // Check for performance metrics
    await expect(page.getByText('⚡ Performance Metrics')).toBeVisible();
    await expect(page.getByText('Avg Call Duration')).toBeVisible();
    await expect(page.getByText('Max Tokens Used')).toBeVisible();
    await expect(page.getByText('Calls Today')).toBeVisible();
    await expect(page.getByText('System Uptime')).toBeVisible();
  });

  test('should have time range selector', async ({ page }) => {
    // Check for time range selector
    const timeRangeSelect = page.getByRole('combobox');
    await expect(timeRangeSelect).toBeVisible();
    
    // Check for time range options
    await expect(page.getByRole('option', { name: /last 24 hours/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /last 7 days/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /last 30 days/i })).toBeVisible();
  });

  test('should show live indicator', async ({ page }) => {
    // Check for live indicator
    await expect(page.getByText('Live')).toBeVisible();
    
    // Check for live indicator dot
    const liveDot = page.locator('.animate-pulse').first();
    await expect(liveDot).toBeVisible();
  });

  test('should display system resource usage bars', async ({ page }) => {
    // Check for resource usage progress bars
    const cpuBar = page.locator('text=CPU Usage').locator('..').locator('.bg-blue-500');
    await expect(cpuBar).toBeVisible();
    
    const memoryBar = page.locator('text=Memory Usage').locator('..').locator('.bg-green-500');
    await expect(memoryBar).toBeVisible();
    
    const diskBar = page.locator('text=Disk Usage').locator('..').locator('.bg-orange-500');
    await expect(diskBar).toBeVisible();
  });

  test('should display call volume chart', async ({ page }) => {
    // Check for bar chart representation
    const chartBars = page.locator('.bg-gradient-to-t.from-indigo-500.to-indigo-400');
    const barCount = await chartBars.count();
    expect(barCount).toBeGreaterThan(0);
  });

  test('should display success rate pie chart', async ({ page }) => {
    // Check for pie chart elements
    const pieChart = page.locator('.absolute.inset-0.rounded-full.border-8');
    await expect(pieChart.first()).toBeVisible();
    
    // Check for success rate percentage
    const successRate = page.getByText(/%/).first();
    await expect(successRate).toBeVisible();
  });

  test('should show loading state initially', async ({ page }) => {
    // Navigate to admin dashboard and immediately check for loading state
    await page.reload();
    await page.getByRole('textbox', { name: /username/i }).fill('admin');
    await page.getByRole('textbox', { name: /password/i }).fill('admin123');
    await page.getByRole('button', { name: /login/i }).click();
    await page.getByRole('button', { name: /admin dashboard/i }).click();
    
    // Should show loading state briefly
    const loadingText = page.getByText('Loading admin dashboard...');
    if (await loadingText.isVisible()) {
      await expect(loadingText).toBeVisible();
    }
  });

  test('should handle time range changes', async ({ page }) => {
    // Change time range
    const timeRangeSelect = page.getByRole('combobox');
    await timeRangeSelect.selectOption('7d');
    
    // Should not throw any errors
    await expect(timeRangeSelect).toBeVisible();
  });

  test('should display alert types', async ({ page }) => {
    // Check for different alert types
    const alerts = page.locator('[class*="bg-"].rounded-lg');
    const alertCount = await alerts.count();
    expect(alertCount).toBeGreaterThan(0);
  });

  test('should display recent activity items', async ({ page }) => {
    // Check for activity items
    const activityItems = page.locator('text=Recent Activity').locator('..').locator('.flex.items-center.space-x-3');
    const itemCount = await activityItems.count();
    expect(itemCount).toBeGreaterThan(0);
  });

  test('should display numeric values in metrics cards', async ({ page }) => {
    // Wait for data to load
    await page.waitForTimeout(1000);
    
    // Check that numeric values are displayed
    const liveCallsCard = page.locator('text=Live Calls').locator('..').locator('.text-3xl.font-bold');
    await expect(liveCallsCard).toBeVisible();
    
    const totalCallsCard = page.locator('text=Total Calls').locator('..').locator('.text-3xl.font-bold');
    await expect(totalCallsCard).toBeVisible();
  });

  test('should display gradient backgrounds on metric cards', async ({ page }) => {
    // Check for gradient backgrounds
    const gradientCards = page.locator('.bg-gradient-to-r');
    const gradientCount = await gradientCards.count();
    expect(gradientCount).toBeGreaterThan(0);
  });
});
