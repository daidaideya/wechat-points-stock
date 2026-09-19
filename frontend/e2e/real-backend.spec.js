import { expect, test } from '@playwright/test'

test('real backend data flows through the dashboard and program pages', async ({ page }) => {
  const issues = []
  page.on('console', (message) => {
    if (message.type() === 'error' || message.type() === 'warning') {
      issues.push(`console ${message.type()}: ${message.text()}`)
    }
  })
  page.on('pageerror', (error) => {
    issues.push(`pageerror: ${error.message}`)
  })

  await page.goto('/app/dashboard')
  await expect(page.getByText('真实数据小程序', { exact: true }).first()).toBeVisible()
  await page.waitForLoadState('networkidle')

  await page.goto('/app/programs')
  await expect(page.getByText('真实数据小程序', { exact: true }).first()).toBeVisible()
  await page.waitForLoadState('networkidle')

  await page.goto('/app/programs/e2e-program')
  await expect(page.locator('h1.detail-title')).toHaveText('真实数据小程序')
  await expect(page.getByText('真实商品', { exact: true })).toBeVisible()
  await page.waitForLoadState('networkidle')

  await page.goto('/app/users')
  const visibleUserName = page
    .locator('.users-mobile-card .users-mobile-title:visible, .users-desktop-table-wrap .users-table-nickname:visible')
    .filter({ hasText: '真实用户' })
    .first()
  await expect(visibleUserName).toContainText('真实用户')

  expect(issues).toEqual([])
})
