import { createRouter, createWebHistory } from 'vue-router'
import api, { clearAccessSession, getAccessSession } from './api'

const DashboardPage = () => import('./views/DashboardPage.vue')
const ProgramsPage = () => import('./views/ProgramsPage.vue')
const ProgramDetailPage = () => import('./views/ProgramDetailPage.vue')
const UsersPage = () => import('./views/UsersPage.vue')
const PointsPage = () => import('./views/PointsPage.vue')
const StockPage = () => import('./views/StockPage.vue')
const SettingsPage = () => import('./views/SettingsPage.vue')
const FavoritesPage = () => import('./views/FavoritesPage.vue')
const AccessGatePage = () => import('./views/AccessGatePage.vue')

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

router.beforeEach(async (to) => {
  if (to.meta?.public) {
    return true
  }

  try {
    const cached = readAccessStatusCache()
    if (cached) {
      if (!cached.enabled) return true
      if (!cached.ok || !getAccessSession()) {
        return { name: 'access-gate' }
      }
      return true
    }

    // One request only (previously double-fetched). Backend returns enabled
    // without 401 when no key is stored; validates when X-Access-Key is sent.
    const { data } = await api.get('/access/status')
    const enabled = Boolean(data?.enabled)
    const accessKey = getAccessSession()

    if (!enabled) {
      accessStatusCache = { at: Date.now(), enabled: false, ok: true }
      return true
    }

    if (!accessKey) {
      accessStatusCache = { at: Date.now(), enabled: true, ok: false }
      return { name: 'access-gate' }
    }

    // Key present: if server says not authenticated, treat as invalid.
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
  document.title = `${to.meta?.title || '库存监控'} - 库存监控`
})

export default router
