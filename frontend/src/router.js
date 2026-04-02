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
    meta: { title: '小程序列表' },
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

router.beforeEach(async (to) => {
  if (to.meta?.public) {
    return true
  }

  try {
    const { data } = await api.get('/access/status')
    if (!data?.enabled) {
      return true
    }

    const accessKey = getAccessSession()
    if (!accessKey) {
      return {
        name: 'access-gate',
      }
    }

    await api.get('/access/status')
    return true
  } catch (error) {
    if (error?.response?.status === 401) {
      clearAccessSession()
      return {
        name: 'access-gate',
      }
    }
    return true
  }
})

router.afterEach((to) => {
  document.title = `${to.meta?.title || '库存监控'} - 库存监控`
})

export default router
