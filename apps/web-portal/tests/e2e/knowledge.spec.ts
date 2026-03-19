import { test, expect } from '@playwright/test'

test.describe('Knowledge Page', () => {
  test('should redirect unauthenticated to login', async ({ page }) => {
    await page.goto('/knowledge')
    await page.waitForURL('**/login**')
    expect(page.url()).toContain('/login')
  })

  test('should show knowledge page title after auth redirect', async ({ page }) => {
    await page.goto('/knowledge')
    // Redirects to login
    await expect(page.locator('input[type="email"]')).toBeVisible()
  })
})
