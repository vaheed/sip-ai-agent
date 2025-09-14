import { test, expect } from '@playwright/test'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the API responses
    await page.route('**/api/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          sip_registered: true,
          active_calls: ['call-123', 'call-456'],
          api_tokens_used: 1500,
          uptime_seconds: 3600,
          system_metrics: {
            cpu_usage: 25.5,
            memory_usage: 60.2,
            disk_usage: 45.8,
            total_calls: 10,
            active_calls_count: 2,
          },
        }),
      })
    })

    await page.route('**/api/logs', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          logs: [
            '[2024-01-01 10:00:00] SIP Registration: Registered',
            '[2024-01-01 10:01:00] New call: call-123',
            '[2024-01-01 10:02:00] Call ended: call-123',
          ],
          total: 3,
        }),
      })
    })

    await page.route('**/api/call_history', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            call_id: 'call-123',
            start_time: 1704110400,
            end_time: 1704110460,
            duration: 60,
            status: 'completed',
          },
          {
            call_id: 'call-456',
            start_time: 1704110500,
            end_time: null,
            duration: null,
            status: 'active',
          },
        ]),
      })
    })

    await page.route('**/api/config', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          config: {
            SIP_DOMAIN: 'test.example.com',
            SIP_USER: '1001',
            SIP_PASS: 'password',
            OPENAI_API_KEY: 'sk-test',
            AGENT_ID: 'agent-123',
            OPENAI_MODE: 'realtime',
            OPENAI_VOICE: 'alloy',
            OPENAI_TEMPERATURE: '0.3',
          },
        }),
      })
    })
  })

  test('should display login form initially', async ({ page }) => {
    await page.goto('/')
    
    await expect(page.getByText('SIP AI Agent')).toBeVisible()
    await expect(page.getByPlaceholder('Username')).toBeVisible()
    await expect(page.getByPlaceholder('Password')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible()
  })

  test('should login and show dashboard', async ({ page }) => {
    await page.goto('/')
    
    // Fill login form
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin123')
    
    // Mock successful login
    await page.route('**/api/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          token: 'mock-token',
        }),
      })
    })

    // Mock auth status check
    await page.route('**/api/auth/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          username: 'admin',
        }),
      })
    })

    await page.click('button[type="submit"]')
    
    // Wait for dashboard to load
    await expect(page.getByText('SIP AI Agent Dashboard')).toBeVisible()
  })

  test('should display status cards', async ({ page }) => {
    // Mock authenticated state
    await page.addInitScript(() => {
      localStorage.setItem('session_token', 'mock-token')
    })

    await page.goto('/')
    
    // Wait for dashboard to load
    await expect(page.getByText('SIP AI Agent Dashboard')).toBeVisible()
    
    // Check status cards
    await expect(page.getByText('SIP Registration')).toBeVisible()
    await expect(page.getByText('Active Calls')).toBeVisible()
    await expect(page.getByText('API Tokens Used')).toBeVisible()
    await expect(page.getByText('Uptime')).toBeVisible()
  })

  test('should display call history table', async ({ page }) => {
    // Mock authenticated state
    await page.addInitScript(() => {
      localStorage.setItem('session_token', 'mock-token')
    })

    await page.goto('/')
    
    // Wait for dashboard to load
    await expect(page.getByText('Call History')).toBeVisible()
    
    // Check table headers
    await expect(page.getByText('Call ID')).toBeVisible()
    await expect(page.getByText('Start Time')).toBeVisible()
    await expect(page.getByText('End Time')).toBeVisible()
    await expect(page.getByText('Duration')).toBeVisible()
    await expect(page.getByText('Status')).toBeVisible()
    
    // Check table data
    await expect(page.getByText('call-123')).toBeVisible()
    await expect(page.getByText('call-456')).toBeVisible()
  })

  test('should toggle dark mode', async ({ page }) => {
    // Mock authenticated state
    await page.addInitScript(() => {
      localStorage.setItem('session_token', 'mock-token')
    })

    await page.goto('/')
    
    // Wait for dashboard to load
    await expect(page.getByText('SIP AI Agent Dashboard')).toBeVisible()
    
    // Click dark mode toggle
    await page.click('button[title*="dark mode"]')
    
    // Check if dark mode is applied (this would need to be adjusted based on actual implementation)
    await expect(page.locator('html')).toHaveClass(/dark/)
  })
})
