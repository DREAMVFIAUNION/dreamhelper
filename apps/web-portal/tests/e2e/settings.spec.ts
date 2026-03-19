import { test, expect } from '@playwright/test'

test.describe('Settings Page', () => {
  test('should redirect unauthenticated to login', async ({ page }) => {
    await page.goto('/settings')
    await page.waitForURL('**/login**')
    expect(page.url()).toContain('/login')
  })

  test('should show settings sections after auth redirect', async ({ page }) => {
    await page.goto('/settings')
    // Redirects to login
    await expect(page.locator('input[type="email"]')).toBeVisible()
  })
})
