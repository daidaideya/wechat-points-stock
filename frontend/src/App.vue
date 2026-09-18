<template>
  <div v-if="isNavigationLoading" class="global-navigation-progress" role="status" aria-label="页面加载中">
    <span class="global-navigation-progress-bar"></span>
  </div>

  <router-view v-if="isPublicPage" />

  <div v-else class="app-layout">
    <header class="mobile-topbar">
      <button
        ref="mobileMenuButtonRef"
        class="mobile-menu-button"
        type="button"
        aria-label="打开主导航"
        aria-controls="mobile-navigation-panel"
        :aria-expanded="mobileNavVisible ? 'true' : 'false'"
        @click.stop="openMobileNav"
      >
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
        <el-menu-item index="/apps">
          <router-link to="/apps" custom v-slot="{ href }">
            <a :href="href" class="menu-item-anchor" @click.prevent>
              <span class="menu-item-icon"><el-icon><Iphone /></el-icon></span>
              <span class="menu-item-text">APP列表</span>
              <span class="menu-item-badge">应用</span>
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
        <el-menu-item index="/stock" @mouseenter="preloadStockPageOnIntent" @focusin="preloadStockPageOnIntent">
          <router-link to="/stock" custom v-slot="{ href }">
            <a :href="href" class="menu-item-anchor" @click.prevent>
              <span class="menu-item-icon"><el-icon><Box /></el-icon></span>
              <span class="menu-item-text">库存管理</span>
              <span class="menu-item-badge">库存</span>
            </a>
          </router-link>
        </el-menu-item>
        <el-menu-item index="/qinglong-crons">
          <router-link to="/qinglong-crons" custom v-slot="{ href }">
            <a :href="href" class="menu-item-anchor" @click.prevent>
              <span class="menu-item-icon"><el-icon><Timer /></el-icon></span>
              <span class="menu-item-text">青龙定时</span>
              <span class="menu-item-badge">调度</span>
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

    <div
      v-if="mobileNavVisible"
      class="mobile-nav-shell"
      @keydown.esc.prevent="closeMobileNav"
    >
      <button
        type="button"
        class="mobile-nav-mask"
        aria-label="关闭主导航"
        @click="closeMobileNav"
      ></button>
      <aside
        id="mobile-navigation-panel"
        ref="mobileNavPanelRef"
        class="sidebar mobile-sidebar mobile-nav-panel"
        role="dialog"
        aria-modal="true"
        aria-label="主导航"
        @keydown="handleMobileNavKeydown"
      >
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
          <el-menu-item index="/apps">
            <router-link to="/apps" custom v-slot="{ href }">
              <a :href="href" class="menu-item-anchor" @click.prevent>
                <span class="menu-item-icon"><el-icon><Iphone /></el-icon></span>
                <span class="menu-item-text">APP列表</span>
                <span class="menu-item-badge">应用</span>
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
          <el-menu-item index="/stock" @mouseenter="preloadStockPageOnIntent" @focusin="preloadStockPageOnIntent">
            <router-link to="/stock" custom v-slot="{ href }">
              <a :href="href" class="menu-item-anchor" @click.prevent>
                <span class="menu-item-icon"><el-icon><Box /></el-icon></span>
                <span class="menu-item-text">库存管理</span>
                <span class="menu-item-badge">库存</span>
              </a>
            </router-link>
          </el-menu-item>
          <el-menu-item index="/qinglong-crons">
            <router-link to="/qinglong-crons" custom v-slot="{ href }">
              <a :href="href" class="menu-item-anchor" @click.prevent>
                <span class="menu-item-icon"><el-icon><Timer /></el-icon></span>
                <span class="menu-item-text">青龙定时整理</span>
                <span class="menu-item-badge">调度</span>
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
    </div>

    <div class="main-panel">
      <header class="top-header">
        <div>
          <h1>{{ pageTitle }}</h1>
          <p>{{ pageDescription }}</p>
        </div>
      </header>

      <main class="page-content" :aria-busy="showNavigationSkeleton">
        <div v-if="showNavigationSkeleton" class="route-navigation-skeleton" aria-hidden="true">
          <div class="route-navigation-skeleton-heading">
            <div class="route-navigation-skeleton-line route-navigation-skeleton-line-title"></div>
            <div class="route-navigation-skeleton-line route-navigation-skeleton-line-subtitle"></div>
          </div>
          <div class="route-navigation-skeleton-grid">
            <div v-for="item in 4" :key="item" class="route-navigation-skeleton-card">
              <div class="route-navigation-skeleton-line route-navigation-skeleton-line-card-title"></div>
              <div class="route-navigation-skeleton-line route-navigation-skeleton-line-card-text"></div>
              <div class="route-navigation-skeleton-line route-navigation-skeleton-line-card-text short"></div>
              <div class="route-navigation-skeleton-block"></div>
            </div>
          </div>
        </div>

        <div
          class="route-view-frame"
          :class="{ 'route-view-frame-obscured': showNavigationSkeleton }"
          :aria-hidden="showNavigationSkeleton ? 'true' : undefined"
        >
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Bell,
  Box,
  Compass,
  Connection,
  DataAnalysis,
  Grid,
  Histogram,
  House,
  Iphone,
  Menu,
  Monitor,
  Setting,
  Timer,
  UserFilled,
} from '@element-plus/icons-vue'
import { useRoute } from 'vue-router'
import { isNavigationLoading, preloadStockPage } from './router'

const route = useRoute()
const mobileNavVisible = ref(false)
const mobileMenuButtonRef = ref(null)
const mobileNavPanelRef = ref(null)
const MOBILE_LAYOUT_MAX = 900

const isPublicPage = computed(() => Boolean(route.meta?.public))
const showNavigationSkeleton = computed(() => !isPublicPage.value && isNavigationLoading.value)

const activeMenu = computed(() => {
  if (route.path.startsWith('/programs/')) {
    return '/programs'
  }
  if (route.path.startsWith('/apps/')) {
    return '/apps'
  }
  return route.path
})

const pageTitle = computed(() => route.meta?.title || '库存监控')

function preloadStockPageOnIntent() {
  void preloadStockPage().catch(() => {})
}

const pageDescription = computed(() => {
  const descriptions = {
    '/dashboard': '统一查看用户、小程序、库存和更新情况。',
    '/programs': '更清晰地浏览小程序、筛选标签、管理备注与库存状态。',
    '/apps': '与小程序列表相同的卡片布局，仅展示 auth_type 为 app 的应用。',
    '/users': '管理微信账号、设备和手机号信息。',
    '/points': '按账号查看积分详情与活跃小程序数量。',
    '/stock': '按小程序和商品维度查看库存信息。',
    '/qinglong-crons': '查看青龙脚本时间线，一键重排执行间隔。',
    '/settings': '基础设置、青龙联动、Bark 推送与数据库备份分栏管理。',
  }

  if (route.path.startsWith('/programs/')) {
    return '查看单个小程序的排行榜与库存详情。'
  }
  if (route.path.startsWith('/apps/')) {
    return '查看单个 APP 的排行榜与库存详情。'
  }

  return descriptions[route.path] || '前后端分离单页应用。'
})

function isMobileLayout() {
  return window.matchMedia(`(max-width: ${MOBILE_LAYOUT_MAX}px)`).matches
}

function openMobileNav() {
  // Guard against desktop accidental open; button is mobile-only by CSS.
  if (!isMobileLayout()) return
  mobileNavVisible.value = true
  void nextTick(() => {
    const firstFocusable = mobileNavPanelRef.value?.querySelector?.(
      'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
    )
    firstFocusable?.focus()
  })
}

function closeMobileNav(restoreFocus = true) {
  const wasVisible = mobileNavVisible.value
  mobileNavVisible.value = false
  if (restoreFocus && wasVisible) {
    void nextTick(() => mobileMenuButtonRef.value?.focus?.())
  }
}

function handleMobileNavKeydown(event) {
  if (event.key !== 'Tab') return
  const panel = mobileNavPanelRef.value
  if (!panel) return
  const focusable = Array.from(
    panel.querySelectorAll('a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'),
  ).filter((element) => element instanceof HTMLElement && !element.hidden)
  if (!focusable.length) return

  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

const handleMobileMenuSelect = () => {
  closeMobileNav()
}

function handleViewportLayoutChange() {
  // Desktop layout should never keep the mobile panel open.
  if (!isMobileLayout() && mobileNavVisible.value) {
    closeMobileNav(false)
  }
}

// 让 element-plus 的图片预览（el-image preview-teleported）支持点击空白处关闭。
// el-image-viewer 不暴露这个 prop，所以全局监听 capture 阶段的 click：
// 命中蒙层 / 包裹层 / 画布空白时，找到对应的关闭按钮触发 click。
function handleImageViewerOutsideClick(event) {
  const target = event.target
  if (!(target instanceof HTMLElement)) return
  const cls = target.classList
  const isBlankArea =
    cls.contains('el-image-viewer__canvas') ||
    cls.contains('el-image-viewer__mask') ||
    cls.contains('el-image-viewer__wrapper')
  if (!isBlankArea) return
  const wrapper = target.closest('.el-image-viewer__wrapper') || document.querySelector('.el-image-viewer__wrapper')
  const closeBtn = wrapper?.querySelector?.('.el-image-viewer__close')
  if (closeBtn instanceof HTMLElement) {
    closeBtn.click()
  }
}

let mobileMediaQuery = null

onMounted(() => {
  document.addEventListener('click', handleImageViewerOutsideClick, true)
  window.addEventListener('resize', handleViewportLayoutChange, { passive: true })
  mobileMediaQuery = window.matchMedia(`(max-width: ${MOBILE_LAYOUT_MAX}px)`)
  if (mobileMediaQuery.addEventListener) {
    mobileMediaQuery.addEventListener('change', handleViewportLayoutChange)
  } else if (mobileMediaQuery.addListener) {
    mobileMediaQuery.addListener(handleViewportLayoutChange)
  }
  handleViewportLayoutChange()
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleImageViewerOutsideClick, true)
  window.removeEventListener('resize', handleViewportLayoutChange)
  if (mobileMediaQuery) {
    if (mobileMediaQuery.removeEventListener) {
      mobileMediaQuery.removeEventListener('change', handleViewportLayoutChange)
    } else if (mobileMediaQuery.removeListener) {
      mobileMediaQuery.removeListener(handleViewportLayoutChange)
    }
    mobileMediaQuery = null
  }
})

watch(
  () => route.fullPath,
  () => {
    closeMobileNav(false)
  },
)

watch(mobileNavVisible, (visible) => {
  // Prevent background scroll while mobile nav is open.
  if (visible) {
    document.body.classList.add('mobile-nav-open')
  } else {
    document.body.classList.remove('mobile-nav-open')
  }
})
</script>
