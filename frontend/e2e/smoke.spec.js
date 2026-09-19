import { expect, test } from '@playwright/test'

const desktopRoutes = [
  ['/dashboard', '仪表盘'],
  ['/programs', '小程序列表'],
  ['/apps', 'APP列表'],
  ['/programs/demo', '小程序详情'],
  ['/users', '用户管理'],
  ['/points', '积分总览'],
  ['/stock', '库存管理'],
  ['/qinglong-crons', '青龙定时'],
  ['/settings', '系统设置'],
  ['/settings?section=qinglong', '系统设置'],
  ['/settings?section=bark', '系统设置'],
  ['/settings?section=database', '系统设置'],
]

function mockJson(route, data, status = 200) {
  return route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(data),
  })
}

async function installApiMock(page, options = {}) {
  await page.route('**/api/v1/**', async (route) => {
    const { pathname } = new URL(route.request().url())
    const apiPath = pathname.replace(/^\/api\/v1/, '')

    if (apiPath === '/access/status') {
      await mockJson(route, { enabled: false, authenticated: false })
      return
    }

    if (apiPath === '/stock/center' && options.stockCenter) {
      await mockJson(route, options.stockCenter)
      return
    }

    if (apiPath === '/qinglong/crons' && options.qinglongCrons) {
      await mockJson(route, options.qinglongCrons)
      return
    }

    if (apiPath === '/accounts' && options.accounts) {
      await mockJson(route, options.accounts)
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
    await page.waitForLoadState('networkidle')
  }

  expect(issues).toEqual([])
})

test('Users empty form keeps the dialog open and shows validation feedback', async ({ page }) => {
  const issues = collectBrowserIssues(page)

  await page.goto('/app/users')
  await page.getByRole('button', { name: '新增用户' }).click()
  const dialog = page.getByRole('dialog')
  await expect(dialog).toBeVisible()
  await expect(dialog).toHaveAttribute('aria-modal', 'true')
  await expect(dialog).toHaveAttribute('aria-label', '新增用户')
  await expect(page.getByRole('textbox', { name: '微信号' })).toBeVisible()
  await page.getByRole('button', { name: '保存' }).click()
  await expect(page.getByText('微信号不能为空')).toBeVisible()
  await expect(dialog).toBeVisible()
  await page.getByRole('button', { name: '取消' }).click()
  await expect(dialog).toBeHidden()
  await expect(page.getByRole('button', { name: '新增用户' })).toBeFocused()

  expect(issues).toEqual([])
})

test('Points account data opens and closes both detail drawers', async ({ page }) => {
  const issues = collectBrowserIssues(page)

  await page.route('**/api/v1/points', async (route) => {
    await mockJson(route, {
      items: [
        {
          account: {
            nickname: '测试账号',
            wechat_id: 'wx-test',
            phone: '13800000000',
            device: 'iPhone',
          },
          active_program_count: 1,
          points: [
            {
              program_id: 'program-1',
              program_name: '积分小程序',
              points: 100,
              cash: 2,
              diff: 5,
              cash_diff: 0.5,
              report_time: '2026-09-19T10:00:00+08:00',
            },
            {
              program_id: 'unregistered-1',
              program_name: '未注册小程序',
              points: '未注册',
              cash: '未注册',
              diff: 0,
              cash_diff: 0,
              report_time: '2026-09-19T10:00:00+08:00',
            },
          ],
        },
      ],
    })
  })

  await page.goto('/app/points')
  await expect(page.getByRole('heading', { name: '测试账号' })).toBeVisible()
  await expect(page.getByText('积分小程序', { exact: true })).toBeVisible()

  await page.getByRole('button', { name: '查看明细' }).click()
  const detailDrawer = page.locator('.points-detail-drawer')
  await expect(detailDrawer).toBeVisible()
  await expect(detailDrawer.getByRole('heading', { name: '测试账号' })).toBeVisible()
  await expect(detailDrawer.getByText('积分小程序', { exact: true })).toBeVisible()
  await detailDrawer.getByRole('button', { name: '关闭' }).click()
  await expect(detailDrawer).toBeHidden()

  await page.locator('.points-icon-button').click()
  const unregisteredDrawer = page.locator('.points-unregistered-drawer')
  await expect(unregisteredDrawer).toBeVisible()
  await expect(unregisteredDrawer.getByRole('heading', { name: '未注册小程序' })).toBeVisible()
  await expect(
    unregisteredDrawer.locator('.points-unregistered-card').getByText('未注册小程序', { exact: true }),
  ).toHaveCount(1)
  await unregisteredDrawer.getByRole('button', { name: '关闭' }).click()
  await expect(unregisteredDrawer).toBeHidden()

  expect(issues).toEqual([])
})

test('stock cards keep their metrics readable in a narrow desktop grid', async ({ page }) => {
  const issues = collectBrowserIssues(page)

  await page.setViewportSize({ width: 1120, height: 900 })
  await page.unroute('**/api/v1/**')
  await installApiMock(page, {
    stockCenter: {
      items: [
        {
          id: 1,
          product_id: 'layout-product-1',
          product_name: '窄屏布局回归商品',
          program_id: 'layout-program',
          program_name: '布局回归小程序',
          points: 120,
          cash: 3.5,
          stock: 8,
          max_user_points: 999,
          max_user_cash: 3.5,
        },
        {
          id: 2,
          product_id: 'layout-product-2',
          product_name: '窄屏布局回归商品二',
          program_id: 'layout-program',
          program_name: '布局回归小程序',
          points: 2930,
          cash: 0,
          stock: 2,
          max_user_points: 2930,
          max_user_cash: 0,
        },
      ],
      total: 2,
      page: 1,
      has_more: false,
      available_tags: [],
      summary: {
        totalProducts: 2,
        inStockProducts: 2,
        outOfStockProducts: 0,
        redeemableProducts: 2,
        pointsOnlyProducts: 1,
        mixedProducts: 1,
      },
    },
  })

  await page.goto('/app/stock')
  const cards = page.locator('.stock-gallery-item')
  await expect(cards).toHaveCount(2)
  await expect(cards.first()).toBeVisible()

  const layouts = await cards.evaluateAll((elements) =>
    elements.map((card) => {
      const image = card.querySelector('.stock-gallery-image-wrap').getBoundingClientRect()
      const main = card.querySelector('.stock-gallery-main').getBoundingClientRect()
      const core = card.querySelector('.stock-gallery-core-row').getBoundingClientRect()
      const coreItems = [...card.querySelectorAll('.stock-gallery-core-item')].map((item) => {
        const rect = item.getBoundingClientRect()
        return { left: rect.left, right: rect.right, width: rect.width }
      })

      return {
        cardGrid: getComputedStyle(card).gridTemplateColumns,
        imageBottom: image.bottom,
        mainTop: main.top,
        mainWidth: main.width,
        coreWidth: core.width,
        coreItems,
      }
    }),
  )

  for (const layout of layouts) {
    expect(layout.cardGrid.split(' ')).toHaveLength(1)
    expect(layout.mainWidth).toBeGreaterThan(200)
    expect(layout.coreWidth).toBeGreaterThan(200)
    expect(layout.mainTop).toBeGreaterThanOrEqual(layout.imageBottom)
    expect(layout.coreItems.every((item) => item.width > 0)).toBe(true)
    expect(layout.coreItems[1].left).toBeGreaterThanOrEqual(layout.coreItems[0].right - 1)
    expect(layout.coreItems[2].left).toBeGreaterThanOrEqual(layout.coreItems[1].right - 1)
  }

  expect(issues).toEqual([])
})

test('QingLong cron rows render names from the API payload', async ({ page }) => {
  const issues = collectBrowserIssues(page)

  await page.unroute('**/api/v1/**')
  await installApiMock(page, {
    qinglongCrons: {
      status: 'success',
      total: 2,
      items: [
        {
          id: 101,
          name: 'code版_积分同步任务',
          command: 'python /scripts/code/sync_points.py',
          schedule: '0 7 * * *',
          is_disabled: 0,
          is_system: 0,
          is_pinned: 0,
          earliest_minute: 420,
        },
        {
          id: 102,
          name: 'code版_库存同步任务',
          command: 'python /scripts/code/sync_stock.py',
          schedule: '30 7 * * *',
          is_disabled: 0,
          is_system: 0,
          is_pinned: 0,
          earliest_minute: 450,
        },
      ],
    },
  })

  await page.goto('/app/qinglong-crons')
  const rows = page.locator('.ql-cron-row')
  await expect(rows).toHaveCount(2)
  await expect(rows.nth(0).locator('.ql-cron-name')).toHaveText('code版_积分同步任务')
  await expect(rows.nth(1).locator('.ql-cron-name')).toHaveText('code版_库存同步任务')
  await expect(rows.nth(0).locator('.ql-cron-command')).toHaveText('python /scripts/code/sync_points.py')
  await expect(rows.nth(1).locator('.ql-cron-command')).toHaveText('python /scripts/code/sync_stock.py')
  await expect(page.getByText('(未命名)', { exact: true })).toHaveCount(0)

  expect(issues).toEqual([])
})

test('Users switches to readable cards when the content area is narrow', async ({ page }) => {
  const issues = collectBrowserIssues(page)

  await page.setViewportSize({ width: 1120, height: 900 })
  await page.unroute('**/api/v1/**')
  await installApiMock(page, {
    accounts: {
      items: [
        {
          wechat_id: 'wx-layout-1',
          nickname: '窄内容区用户',
          phone: '13800000000',
          device: 'iPhone',
          active_program_count: 3,
          active_app_count: 2,
        },
        {
          wechat_id: 'wx-layout-2',
          nickname: '第二个用户',
          phone: '',
          device: 'Android',
          active_program_count: 1,
          active_app_count: 0,
        },
      ],
    },
  })

  await page.goto('/app/users')
  const cards = page.locator('.users-mobile-card')
  await expect(cards).toHaveCount(2)
  await expect(cards.first()).toBeVisible()
  await expect(cards.first().locator('.users-mobile-title')).toContainText('窄内容区用户')
  await expect(cards.first().locator('.users-mobile-meta-value').filter({ hasText: '13800000000' })).toBeVisible()
  await expect(page.locator('.users-desktop-table-wrap')).toBeHidden()

  const layout = await page.locator('.users-list-card').evaluate((card) => ({
    clientWidth: card.clientWidth,
    scrollWidth: card.scrollWidth,
    cardWidth: card.querySelector('.users-mobile-card').getBoundingClientRect().width,
  }))
  expect(layout.cardWidth).toBeLessThanOrEqual(layout.clientWidth)
  expect(layout.scrollWidth).toBeLessThanOrEqual(layout.clientWidth + 1)

  expect(issues).toEqual([])
})

test('settings mutations share one busy boundary', async ({ page }) => {
  const issues = collectBrowserIssues(page)

  await page.route('**/api/v1/settings/logs', async (route) => {
    if (route.request().method() === 'POST') {
      await new Promise((resolve) => setTimeout(resolve, 400))
    }
    await mockJson(route, {})
  })

  await page.goto('/app/settings')
  const saveButton = page.getByRole('button', { name: '保存设置' })
  await saveButton.click()
  await expect(page.getByRole('button', { name: '刷新当前页' })).toBeDisabled()
  await expect(page.getByRole('button', { name: '青龙联动' })).toBeDisabled()
  await expect(saveButton).toBeDisabled()
  await expect(saveButton).toBeEnabled({ timeout: 3000 })

  expect(issues).toEqual([])
})

test('mobile navigation opens and closes at the responsive breakpoint', async ({ page }) => {
  const issues = collectBrowserIssues(page)

  await page.setViewportSize({ width: 1120, height: 844 })
  await page.goto('/app/dashboard')
  await expect(page.locator('.mobile-topbar')).toBeHidden()
  await expect(page.locator('.desktop-sidebar')).toBeVisible()

  await page.setViewportSize({ width: 390, height: 844 })
  await expect(page.locator('.mobile-topbar')).toBeVisible()
  await expect(page.locator('.desktop-sidebar')).toBeHidden()

  await page.getByRole('button', { name: '打开主导航' }).click()
  await expect(page.locator('.mobile-nav-panel')).toBeVisible()
  await expect(page.getByText('用户管理', { exact: true }).last()).toBeVisible()
  await expect(page.getByRole('button', { name: '打开主导航' })).toHaveAttribute('aria-expanded', 'true')
  const firstNavItem = page.locator('.mobile-nav-panel .menu-item-anchor').first()
  const lastNavItem = page.locator('.mobile-nav-panel .menu-item-anchor').last()
  await expect(firstNavItem).toBeFocused()
  await page.keyboard.press('Shift+Tab')
  await expect(lastNavItem).toBeFocused()
  await page.keyboard.press('Tab')
  await expect(firstNavItem).toBeFocused()

  await page.keyboard.press('Escape')
  await expect(page.locator('.mobile-nav-panel')).toBeHidden()
  await expect(page.getByRole('button', { name: '打开主导航' })).toHaveAttribute('aria-expanded', 'false')
  await expect(page.getByRole('button', { name: '打开主导航' })).toBeFocused()

  expect(issues).toEqual([])
})
