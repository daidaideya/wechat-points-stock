<template>
  <router-view v-if="isPublicPage" />

  <div v-else class="app-layout">
    <header class="mobile-topbar">
      <button class="mobile-menu-button" type="button" @click="mobileNavVisible = true">
        <el-icon><Menu /></el-icon>
      </button>
      <div class="mobile-topbar-main">
        <div class="mobile-topbar-title">库存监控</div>
        <div class="mobile-topbar-subtitle">{{ pageTitle }}</div>
      </div>
    </header>

    <aside class="sidebar desktop-sidebar">
      <div class="brand brand-enhanced">
        <div class="brand-mark">
          <el-icon><DataAnalysis /></el-icon>
        </div>
        <div class="brand-content">
          <div class="brand-title">库存监控</div>
          <div class="brand-subtitle">Vue SPA + FastAPI API</div>
        </div>
      </div>

      <div class="sidebar-section-label">
        <span class="sidebar-section-icon"><el-icon><Compass /></el-icon></span>
        <span>主导航</span>
      </div>

      <el-menu :default-active="activeMenu" class="side-menu" router>
        <el-menu-item index="/dashboard">
          <router-link to="/dashboard" custom v-slot="{ href }">
            <a :href="href" class="menu-item-anchor" @click.prevent>
              <span class="menu-item-icon"><el-icon><House /></el-icon></span>
              <span class="menu-item-text">仪表盘</span>
              <span class="menu-item-badge">总览</span>
            </a>
          </router-link>
        </el-menu-item>
        <el-menu-item index="/programs">
          <router-link to="/programs" custom v-slot="{ href }">
            <a :href="href" class="menu-item-anchor" @click.prevent>
              <span class="menu-item-icon"><el-icon><Grid /></el-icon></span>
              <span class="menu-item-text">小程序列表</span>
              <span class="menu-item-badge">检索</span>
            </a>
          </router-link>
        </el-menu-item>
        <el-menu-item index="/users">
          <router-link to="/users" custom v-slot="{ href }">
            <a :href="href" class="menu-item-anchor" @click.prevent>
              <span class="menu-item-icon"><el-icon><UserFilled /></el-icon></span>
              <span class="menu-item-text">用户管理</span>
              <span class="menu-item-badge">账号</span>
            </a>
          </router-link>
        </el-menu-item>
        <el-menu-item index="/points">
          <router-link to="/points" custom v-slot="{ href }">
            <a :href="href" class="menu-item-anchor" @click.prevent>
              <span class="menu-item-icon"><el-icon><Histogram /></el-icon></span>
              <span class="menu-item-text">积分总览</span>
              <span class="menu-item-badge">数据</span>
            </a>
          </router-link>
        </el-menu-item>
        <el-menu-item index="/stock">
          <router-link to="/stock" custom v-slot="{ href }">
            <a :href="href" class="menu-item-anchor" @click.prevent>
              <span class="menu-item-icon"><el-icon><Box /></el-icon></span>
              <span class="menu-item-text">库存管理</span>
              <span class="menu-item-badge">库存</span>
            </a>
          </router-link>
        </el-menu-item>
        <el-menu-item index="/settings">
          <router-link to="/settings" custom v-slot="{ href }">
            <a :href="href" class="menu-item-anchor" @click.prevent>
              <span class="menu-item-icon"><el-icon><Setting /></el-icon></span>
              <span class="menu-item-text">系统设置</span>
              <span class="menu-item-badge">配置</span>
            </a>
          </router-link>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-status-panel">
        <div class="sidebar-section-label compact">
          <span class="sidebar-section-icon"><el-icon><Bell /></el-icon></span>
          <span>当前状态</span>
        </div>
        <div class="sidebar-status-list">
          <div class="sidebar-status-item active">
            <span class="sidebar-status-dot"></span>
            <span class="sidebar-status-text">当前页面：{{ pageTitle }}</span>
          </div>
          <div class="sidebar-status-item muted">
            <span class="sidebar-status-icon"><el-icon><Connection /></el-icon></span>
            <span class="sidebar-status-text">后端 API 已接入</span>
          </div>
          <div class="sidebar-status-item muted">
            <span class="sidebar-status-icon"><el-icon><Monitor /></el-icon></span>
            <span class="sidebar-status-text">前端 SPA 模式运行</span>
          </div>
        </div>
      </div>
    </aside>

    <el-drawer
      v-model="mobileNavVisible"
      direction="ltr"
      size="84vw"
      :with-header="false"
      class="mobile-nav-drawer"
      modal-class="mobile-nav-drawer-overlay"
    >
      <aside class="sidebar mobile-sidebar">
        <div class="brand brand-enhanced mobile-brand">
          <div class="brand-mark">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="brand-content">
            <div class="brand-title">库存监控</div>
            <div class="brand-subtitle">Vue SPA + FastAPI API</div>
          </div>
        </div>

        <div class="sidebar-section-label">
          <span class="sidebar-section-icon"><el-icon><Compass /></el-icon></span>
          <span>主导航</span>
        </div>

        <el-menu :default-active="activeMenu" class="side-menu" router @select="handleMobileMenuSelect">
          <el-menu-item index="/dashboard">
            <router-link to="/dashboard" custom v-slot="{ href }">
              <a :href="href" class="menu-item-anchor" @click.prevent>
                <span class="menu-item-icon"><el-icon><House /></el-icon></span>
                <span class="menu-item-text">仪表盘</span>
                <span class="menu-item-badge">总览</span>
              </a>
            </router-link>
          </el-menu-item>
          <el-menu-item index="/programs">
            <router-link to="/programs" custom v-slot="{ href }">
              <a :href="href" class="menu-item-anchor" @click.prevent>
                <span class="menu-item-icon"><el-icon><Grid /></el-icon></span>
                <span class="menu-item-text">小程序列表</span>
                <span class="menu-item-badge">检索</span>
              </a>
            </router-link>
          </el-menu-item>
          <el-menu-item index="/users">
            <router-link to="/users" custom v-slot="{ href }">
              <a :href="href" class="menu-item-anchor" @click.prevent>
                <span class="menu-item-icon"><el-icon><UserFilled /></el-icon></span>
                <span class="menu-item-text">用户管理</span>
                <span class="menu-item-badge">账号</span>
              </a>
            </router-link>
          </el-menu-item>
          <el-menu-item index="/points">
            <router-link to="/points" custom v-slot="{ href }">
              <a :href="href" class="menu-item-anchor" @click.prevent>
                <span class="menu-item-icon"><el-icon><Histogram /></el-icon></span>
                <span class="menu-item-text">积分总览</span>
                <span class="menu-item-badge">数据</span>
              </a>
            </router-link>
          </el-menu-item>
          <el-menu-item index="/stock">
            <router-link to="/stock" custom v-slot="{ href }">
              <a :href="href" class="menu-item-anchor" @click.prevent>
                <span class="menu-item-icon"><el-icon><Box /></el-icon></span>
                <span class="menu-item-text">库存管理</span>
                <span class="menu-item-badge">库存</span>
              </a>
            </router-link>
          </el-menu-item>
          <el-menu-item index="/settings">
            <router-link to="/settings" custom v-slot="{ href }">
              <a :href="href" class="menu-item-anchor" @click.prevent>
                <span class="menu-item-icon"><el-icon><Setting /></el-icon></span>
                <span class="menu-item-text">系统设置</span>
                <span class="menu-item-badge">配置</span>
              </a>
            </router-link>
          </el-menu-item>
        </el-menu>

        <div class="sidebar-status-panel mobile-status-panel">
          <div class="sidebar-section-label compact">
            <span class="sidebar-section-icon"><el-icon><Bell /></el-icon></span>
            <span>当前状态</span>
          </div>
          <div class="sidebar-status-list">
            <div class="sidebar-status-item active">
              <span class="sidebar-status-dot"></span>
              <span class="sidebar-status-text">当前页面：{{ pageTitle }}</span>
            </div>
            <div class="sidebar-status-item muted">
              <span class="sidebar-status-icon"><el-icon><Connection /></el-icon></span>
              <span class="sidebar-status-text">后端 API 已接入</span>
            </div>
            <div class="sidebar-status-item muted">
              <span class="sidebar-status-icon"><el-icon><Monitor /></el-icon></span>
              <span class="sidebar-status-text">前端 SPA 模式运行</span>
            </div>
          </div>
        </div>
      </aside>
    </el-drawer>

    <div class="main-panel">
      <header class="top-header">
        <div>
          <h1>{{ pageTitle }}</h1>
          <p>{{ pageDescription }}</p>
        </div>
      </header>

      <main class="page-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import {
  Bell,
  Box,
  Compass,
  Connection,
  DataAnalysis,
  Grid,
  Histogram,
  House,
  Menu,
  Monitor,
  Setting,
  UserFilled,
} from '@element-plus/icons-vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const mobileNavVisible = ref(false)

const isPublicPage = computed(() => Boolean(route.meta?.public))

const activeMenu = computed(() => {
  if (route.path.startsWith('/programs/')) {
    return '/programs'
  }
  return route.path
})

const pageTitle = computed(() => route.meta?.title || '库存监控')

const pageDescription = computed(() => {
  const descriptions = {
    '/dashboard': '统一查看用户、小程序、库存和更新情况。',
    '/programs': '更清晰地浏览小程序、筛选标签、管理备注与库存状态。',
    '/users': '管理微信账号、设备和手机号信息。',
    '/points': '按账号查看积分详情与活跃小程序数量。',
    '/stock': '按小程序和商品维度查看库存信息。',
    '/settings': '维护日志保留与系统清理参数。',
  }

  if (route.path.startsWith('/programs/')) {
    return '查看单个小程序的排行榜与库存详情。'
  }

  return descriptions[route.path] || '前后端分离单页应用。'
})

const handleMobileMenuSelect = () => {
  mobileNavVisible.value = false
}

watch(
  () => route.fullPath,
  () => {
    mobileNavVisible.value = false
  },
)
</script>
