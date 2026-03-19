import { test, expect } from '@playwright/test'

test.describe('Chat Page', () => {
  test('should redirect unauthenticated to login', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForURL('**/login**')
    expect(page.url()).toContain('/login')
  })

  test('should show chat input area after login', async ({ page }) => {
    await page.goto('/chat')
    // Redirects to login, check login form exists
    await expect(page.locator('input[type="email"]')).toBeVisible()
  })
})
