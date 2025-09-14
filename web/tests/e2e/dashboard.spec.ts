import { test, expect } from '@playwright/test'

test.describe('Dashboard', () => {
  test('should display login form initially', async ({ page }) => {
    await page.goto('/')
    
    await expect(page.getByText('SIP AI Agent')).toBeVisible()
    await expect(page.getByPlaceholder('Username')).toBeVisible()
    await expect(page.getByPlaceholder('Password')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible()
  })

  test('should have proper page title', async ({ page }) => {
    await page.goto('/')
    
    await expect(page).toHaveTitle('SIP AI Agent Dashboard')
  })

  test('should be responsive', async ({ page }) => {
    await page.goto('/')
    
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    await expect(page.getByText('SIP AI Agent')).toBeVisible()
    
    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 })
    await expect(page.getByText('SIP AI Agent')).toBeVisible()
  })
})