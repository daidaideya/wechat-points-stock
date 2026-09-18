import { expect, test } from '@playwright/test'

const desktopRoutes = [
  ['/dashboard', '仪表盘'],
  ['/programs', '小程序列表'],
  ['/apps', 'APP列表'],
  ['/users', '用户管理'],
  ['/points', '积分总览'],
  ['/stock', '库存管理'],
  ['/qinglong-crons', '青龙定时'],
  ['/settings', '系统设置'],
]

function mockJson(route, data, status = 200) {
  return route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(data),
  })
}

async function installApiMock(page) {
  await page.route('**/api/v1/**', async (route) => {
    const { pathname } = new URL(route.request().url())
    const apiPath = pathname.replace(/^\/api\/v1/, '')

    if (apiPath === '/access/status') {
      await mockJson(route, { enabled: false, authenticated: false })
      return
    }

    // Keep the smoke test deterministic and data-independent. Empty but valid
    // payloads exercise the real Vue route/component lifecycle without a
    // running SQLite database or QingLong instance.
    await mockJson(route, {
      items: [],
      total: 0,
      page: 1,
      has_more: false,
      available_tags: [],
      summary: {},
      failed: [],
      updated: 0,
    })
  })
}

function collectBrowserIssues(page) {
  const issues = []
  page.on('console', (message) => {
    if (message.type() === 'error' || message.type() === 'warning') {
      issues.push(`console ${message.type()}: ${message.text()}`)
    }
  })
  page.on('pageerror', (error) => {
    issues.push(`pageerror: ${error.message}`)
  })
  return issues
}

test.beforeEach(async ({ page }) => {
  await installApiMock(page)
})

test('desktop primary routes render their page shell without browser errors', async ({ page }) => {
  const issues = collectBrowserIssues(page)

  for (const [path, title] of desktopRoutes) {
    await page.goto(`/app${path}`)
    await expect(page.locator('main.page-content')).toBeVisible()
    await expect(page.locator('header.top-header h1')).toHaveText(title)
    await expect(page.locator('.route-view-frame')).toBeVisible()
  }

  expect(issues).toEqual([])
})

test('Users empty form keeps the dialog open and shows validation feedback', async ({ page }) => {
  const issues = collectBrowserIssues(page)

  await page.goto('/app/users')
  await page.getByRole('button', { name: '新增用户' }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.getByRole('button', { name: '保存' }).click()
  await expect(page.getByText('微信号不能为空')).toBeVisible()
  await expect(page.getByRole('dialog')).toBeVisible()

  expect(issues).toEqual([])
})

test('mobile navigation opens and closes at the responsive breakpoint', async ({ page }) => {
  const issues = collectBrowserIssues(page)

  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/app/dashboard')
  await expect(page.locator('.mobile-topbar')).toBeVisible()
  await expect(page.locator('.desktop-sidebar')).toBeHidden()

  await page.getByRole('button', { name: '打开主导航' }).click()
  await expect(page.locator('.mobile-nav-panel')).toBeVisible()
  await expect(page.getByText('用户管理', { exact: true }).last()).toBeVisible()

  // The mask sits behind the side panel, so force the event on its close
  // button instead of relying on a physical point outside the panel.
  await page.getByRole('button', { name: '关闭主导航' }).click({ force: true })
  await expect(page.locator('.mobile-nav-panel')).toBeHidden()

  expect(issues).toEqual([])
})
