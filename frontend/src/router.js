import { readonly, ref } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import api from './api'
import { clearAccessSession } from './composables/useAccessSession'

const DashboardPage = () => import('./views/DashboardPage.vue')
const ProgramsPage = () => import('./views/ProgramsPage.vue')
const ProgramDetailPage = () => import('./views/ProgramDetailPage.vue')
const UsersPage = () => import('./views/UsersPage.vue')
const PointsPage = () => import('./views/PointsPage.vue')
const SettingsPage = () => import('./views/SettingsPage.vue')
const FavoritesPage = () => import('./views/FavoritesPage.vue')
const QinglongCronsPage = () => import('./views/QinglongCronsPage.vue')
const AccessGatePage = () => import('./views/AccessGatePage.vue')

const NAVIGATION_LOADING_DELAY_MS = 120
const NAVIGATION_LOADING_MIN_VISIBLE_MS = 180

const navigationLoadingState = ref(false)
export const isNavigationLoading = readonly(navigationLoadingState)

let navigationLoadingTimer = null
let navigationHideTimer = null
let navigationVisibleAt = 0

function startNavigationLoading() {
  if (navigationHideTimer !== null) {
    clearTimeout(navigationHideTimer)
    navigationHideTimer = null
  }

  if (navigationLoadingState.value || navigationLoadingTimer !== null) {
    return
  }

  navigationLoadingTimer = setTimeout(() => {
    navigationLoadingTimer = null
    navigationLoadingState.value = true
    navigationVisibleAt = Date.now()
  }, NAVIGATION_LOADING_DELAY_MS)
}

function finishNavigationLoading() {
  if (navigationLoadingTimer !== null) {
    clearTimeout(navigationLoadingTimer)
    navigationLoadingTimer = null
  }

  if (!navigationLoadingState.value || navigationHideTimer !== null) {
    return
  }

  const elapsed = Date.now() - navigationVisibleAt
  const remaining = Math.max(0, NAVIGATION_LOADING_MIN_VISIBLE_MS - elapsed)
  if (remaining === 0) {
    navigationLoadingState.value = false
    return
  }

  navigationHideTimer = setTimeout(() => {
    navigationHideTimer = null
    navigationLoadingState.value = false
  }, remaining)
}

let stockPageChunkPromise = null
let stockPagePreloadScheduled = false
let stockPagePreloadHandle = null
let stockPagePreloadUsesIdleCallback = false

function cancelScheduledStockPagePreload() {
  if (!stockPagePreloadScheduled) {
    return
  }

  if (stockPagePreloadHandle !== null && typeof window !== 'undefined') {
    if (stockPagePreloadUsesIdleCallback && typeof window.cancelIdleCallback === 'function') {
      window.cancelIdleCallback(stockPagePreloadHandle)
    } else {
      window.clearTimeout(stockPagePreloadHandle)
    }
  }

  stockPagePreloadScheduled = false
  stockPagePreloadHandle = null
  stockPagePreloadUsesIdleCallback = false
}

export function preloadStockPage() {
  cancelScheduledStockPagePreload()

  if (!stockPageChunkPromise) {
    stockPageChunkPromise = import('./views/StockPage.vue').catch((error) => {
      // Let the next navigation or intent retry a transient chunk failure.
      stockPageChunkPromise = null
      throw error
    })
  }
  return stockPageChunkPromise
}

function runScheduledStockPagePreload() {
  stockPagePreloadScheduled = false
  stockPagePreloadHandle = null
  stockPagePreloadUsesIdleCallback = false
  void preloadStockPage().catch(() => {})
}

export function scheduleStockPagePreload() {
  if (typeof window === 'undefined' || stockPageChunkPromise || stockPagePreloadScheduled) {
    return
  }

  stockPagePreloadScheduled = true
  if (typeof window.requestIdleCallback === 'function') {
    stockPagePreloadUsesIdleCallback = true
    stockPagePreloadHandle = window.requestIdleCallback(runScheduledStockPagePreload, { timeout: 1200 })
  } else {
    stockPagePreloadHandle = window.setTimeout(runScheduledStockPagePreload, 200)
  }
}

const StockPage = () => preloadStockPage()

const routes = [
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/access-gate',
    name: 'access-gate',
    component: AccessGatePage,
    meta: { title: '访问验证', public: true },
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardPage,
    meta: { title: '仪表盘' },
  },
  {
    path: '/programs',
    name: 'programs',
    component: ProgramsPage,
    meta: { title: '小程序列表', listKind: 'mini' },
  },
  {
    path: '/apps',
    name: 'apps',
    component: ProgramsPage,
    meta: { title: 'APP列表', listKind: 'app' },
  },
  {
    path: '/favorites',
    name: 'favorites',
    component: FavoritesPage,
    meta: { title: '重点关注' },
  },
  {
    path: '/programs/:programId',
    name: 'program-detail',
    component: ProgramDetailPage,
    props: true,
    meta: { title: '小程序详情' },
  },
  {
    path: '/apps/:programId',
    name: 'app-detail',
    component: ProgramDetailPage,
    props: true,
    meta: { title: 'APP详情', listKind: 'app' },
  },
  {
    path: '/users',
    name: 'users',
    component: UsersPage,
    meta: { title: '用户管理' },
  },
  {
    path: '/points',
    name: 'points',
    component: PointsPage,
    meta: { title: '积分总览' },
  },
  {
    path: '/stock',
    name: 'stock',
    component: StockPage,
    meta: { title: '库存管理' },
  },
  {
    path: '/qinglong-crons',
    name: 'qinglong-crons',
    component: QinglongCronsPage,
    meta: { title: '青龙定时' },
  },
  {
    path: '/settings',
    name: 'settings',
    component: SettingsPage,
    meta: { title: '系统设置' },
  },
]

const router = createRouter({
  history: createWebHistory('/app/'),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    return { top: 0, left: 0 }
  },
})

// Short-lived access-status cache so client navigations don't hit the API every time.
const ACCESS_STATUS_TTL_MS = 30_000
let accessStatusCache = {
  at: 0,
  enabled: false,
  ok: true,
}

function readAccessStatusCache() {
  if (Date.now() - accessStatusCache.at > ACCESS_STATUS_TTL_MS) return null
  return accessStatusCache
}

export function invalidateAccessStatusCache() {
  accessStatusCache = { at: 0, enabled: false, ok: true }
}

if (typeof window !== 'undefined') {
  window.addEventListener('site-access-required', () => {
    clearAccessSession()
    invalidateAccessStatusCache()
    if (router.currentRoute.value.name !== 'access-gate') {
      router.replace({ name: 'access-gate' })
    }
  })
}

router.beforeEach(async (to) => {
  startNavigationLoading()

  if (to.meta?.public) {
    return true
  }

  try {
    const cached = readAccessStatusCache()
    if (cached) {
      if (!cached.enabled) return true
      if (!cached.ok) {
        return { name: 'access-gate' }
      }
      return true
    }

    // One request only (previously double-fetched). Backend returns enabled
    // without 401 when no session is stored; validates legacy X-Access-Key
    // headers during the migration window.
    const { data } = await api.get('/access/status')
    const enabled = Boolean(data?.enabled)

    if (!enabled) {
      accessStatusCache = { at: Date.now(), enabled: false, ok: true }
      return true
    }

    if (data?.authenticated === true) {
      accessStatusCache = { at: Date.now(), enabled: true, ok: true }
      return true
    }

    if (data?.authenticated === false) {
      clearAccessSession()
      accessStatusCache = { at: Date.now(), enabled: true, ok: false }
      return { name: 'access-gate' }
    }

    accessStatusCache = { at: Date.now(), enabled: true, ok: true }
    return true
  } catch (error) {
    if (error?.response?.status === 401) {
      clearAccessSession()
      accessStatusCache = { at: Date.now(), enabled: true, ok: false }
      return { name: 'access-gate' }
    }
    // Network blip: do not block navigation.
    return true
  }
})

router.afterEach((to) => {
  finishNavigationLoading()
  document.title = `${to.meta?.title || '库存监控'} - 库存监控`

  if (to.name === 'dashboard') {
    scheduleStockPagePreload()
  }
})

router.onError(() => {
  finishNavigationLoading()
})

export default router
