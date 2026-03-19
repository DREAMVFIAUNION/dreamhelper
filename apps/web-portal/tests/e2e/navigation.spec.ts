import { test, expect } from '@playwright/test'

test.describe('Landing Pages Navigation', () => {
  test('should load homepage', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=DREAMVFIA')).toBeVisible()
  })

  test('should navigate to features', async ({ page }) => {
    await page.goto('/features')
    await expect(page).toHaveURL('/features')
  })

  test('should navigate to pricing', async ({ page }) => {
    await page.goto('/pricing')
    await expect(page).toHaveURL('/pricing')
  })

  test('should navigate to about', async ({ page }) => {
    await page.goto('/about')
    await expect(page).toHaveURL('/about')
  })

  test('should show 404 for unknown routes', async ({ page }) => {
    await page.goto('/nonexistent-page-xyz')
    await expect(page.locator('text=404')).toBeVisible()
  })
})

test.describe('Admin Access Control', () => {
  test('should redirect unauthenticated admin to admin login', async ({ page }) => {
    await page.goto('/admin')
    await page.waitForURL('**/admin/login**')
    expect(page.url()).toContain('/admin/login')
  })

  test('should show admin login page', async ({ page }) => {
    await page.goto('/admin/login')
    await expect(page.locator('input[type="email"]')).toBeVisible()
  })
})

test.describe('Health Check', () => {
  test('should return health status', async ({ request }) => {
    const response = await request.get('/api/health')
    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    expect(data.status).toBe('ok')
    expect(data.version).toBe('3.0.0-dev')
  })
})
