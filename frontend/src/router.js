import { createRouter, createWebHistory } from 'vue-router'

import DashboardPage from './views/DashboardPage.vue'
import ProgramsPage from './views/ProgramsPage.vue'
import ProgramDetailPage from './views/ProgramDetailPage.vue'
import UsersPage from './views/UsersPage.vue'
import PointsPage from './views/PointsPage.vue'
import StockPage from './views/StockPage.vue'
import SettingsPage from './views/SettingsPage.vue'

const routes = [
  {
    path: '/',
    redirect: '/dashboard',
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
})

router.afterEach((to) => {
  document.title = `${to.meta?.title || '库存监控'} - 库存监控`
})

export default router
