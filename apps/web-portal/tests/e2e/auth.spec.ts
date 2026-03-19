import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  test('should show login page', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('text=DREAMVFIA')).toBeVisible()
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
  })

  test('should reject empty login', async ({ page }) => {
    await page.goto('/login')
    await page.click('button[type="submit"]')
    await expect(page.locator('text=请填写邮箱和密码')).toBeVisible()
  })

  test('should show register page', async ({ page }) => {
    await page.goto('/register')
    await expect(page.locator('text=DREAMVFIA')).toBeVisible()
    await expect(page.locator('input[type="email"]')).toBeVisible()
  })

  test('should redirect unauthenticated to login', async ({ page }) => {
    await page.goto('/overview')
    await page.waitForURL('**/login**')
    expect(page.url()).toContain('/login')
  })

  test('should show forgot password page', async ({ page }) => {
    await page.goto('/forgot')
    await expect(page.locator('input[type="email"]')).toBeVisible()
  })

  test('should navigate from login to register', async ({ page }) => {
    await page.goto('/login')
    await page.click('text=注册账号')
    await page.waitForURL('**/register')
    expect(page.url()).toContain('/register')
  })
})
