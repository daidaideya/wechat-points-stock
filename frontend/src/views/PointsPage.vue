<template>
  <div class="points-page page-stack">
    <section class="points-hero toolbar-card">
      <div class="points-hero-head">
        <div>
          <div class="section-title">积分驾驶舱</div>
          <p class="section-description">
            聚焦账号资产、今日波动和最近同步情况，快速定位高积分账号与异常变化。
          </p>
        </div>
        <div class="points-hero-actions">
          <el-button :loading="loading" @click="loadPoints">
            <el-icon><RefreshRight /></el-icon>
            刷新数据
          </el-button>
        </div>
      </div>

      <div class="points-metrics-grid">
        <article class="points-metric-card tone-blue">
          <div class="points-metric-top">
            <div>
              <div class="points-metric-label">账号总数</div>
              <div class="points-metric-value">{{ summary.accountCount }}</div>
            </div>
            <span class="points-metric-icon">
              <el-icon><UserFilled /></el-icon>
            </span>
          </div>
          <div class="points-metric-foot">已纳入积分统计的微信账号</div>
        </article>

        <article class="points-metric-card tone-cyan">
          <div class="points-metric-top">
            <div>
              <div class="points-metric-label">活跃小程序</div>
              <div class="points-metric-value">{{ summary.activeProgramCount }}</div>
            </div>
            <span class="points-metric-icon">
              <el-icon><Grid /></el-icon>
            </span>
          </div>
          <div class="points-metric-foot">所有账号当前有积分的小程序合计</div>
        </article>

        <article class="points-metric-card tone-amber">
          <div class="points-metric-top">
            <div>
              <div class="points-metric-label">累计积分</div>
              <div class="points-metric-value">{{ formatCompactNumber(summary.totalPoints) }}</div>
            </div>
            <span class="points-metric-icon">
              <el-icon><Coin /></el-icon>
            </span>
          </div>
          <div class="points-metric-foot">按账号最新积分汇总</div>
        </article>

        <article class="points-metric-card" :class="summary.totalDiff >= 0 ? 'tone-green' : 'tone-red'">
          <div class="points-metric-top">
            <div>
              <div class="points-metric-label">今日净变化</div>
              <div class="points-metric-value">{{ formatSigned(summary.totalDiff) }}</div>
            </div>
            <span class="points-metric-icon">
              <el-icon><TrendCharts /></el-icon>
            </span>
          </div>
          <div class="points-metric-foot">
            上涨 {{ summary.positiveAccounts }} 个账号，下降 {{ summary.negativeAccounts }} 个账号
          </div>
        </article>
      </div>

      <div class="points-hero-meta">
        <span class="points-meta-chip">
          <el-icon><Clock /></el-icon>
          最近同步：{{ formatDate(summary.latestReportTime) }}
        </span>
        <span class="points-meta-chip warning" v-if="summary.staleAccounts">
          <el-icon><Warning /></el-icon>
          {{ summary.staleAccounts }} 个账号今日未更新
        </span>
      </div>
    </section>

    <section class="toolbar-card points-toolbar-card">
      <div class="points-toolbar-grid">
        <el-input
          v-model="searchKeyword"
          clearable
          placeholder="搜索昵称 / 微信号 / 手机号 / 设备"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select v-model="sortMode">
          <el-option label="按总积分排序" value="totalPoints" />
          <el-option label="按今日变化排序" value="totalDiff" />
          <el-option label="按活跃小程序排序" value="activePrograms" />
          <el-option label="按最近更新时间排序" value="latestReport" />
        </el-select>

        <el-select v-model="quickFilter">
          <el-option label="全部账号" value="all" />
          <el-option label="只看上涨账号" value="positive" />
          <el-option label="只看下降账号" value="negative" />
          <el-option label="只看异常账号" value="warning" />
          <el-option label="只看未更新账号" value="stale" />
          <el-option label="只看活跃账号" value="active" />
        </el-select>
      </div>

      <div class="points-toolbar-summary">
        <span class="points-toolbar-text">当前展示 {{ filteredItems.length }} / {{ normalizedItems.length }} 个账号</span>
        <div class="points-toolbar-tags">
          <span class="points-filter-chip">Top 账号：{{ summary.topAccountName || '暂无' }}</span>
          <span class="points-filter-chip">最大涨幅：{{ formatSigned(summary.topDiff) }}</span>
        </div>
      </div>
    </section>

    <el-skeleton v-if="loading" :rows="10" animated class="toolbar-card" />

    <section v-else-if="filteredItems.length" class="points-account-grid">
      <article
        v-for="item in filteredItems"
        :key="item.account.wechat_id"
        class="points-account-card"
      >
        <div class="points-account-head">
          <div class="points-account-title-wrap">
            <div class="points-account-title-row">
              <h3 class="points-account-title">{{ item.account.nickname || item.account.wechat_id }}</h3>
              <el-tag v-if="item.totalDiff > 0" type="success" effect="light">今日上涨</el-tag>
              <el-tag v-else-if="item.totalDiff < 0" type="danger" effect="light">今日下降</el-tag>
              <el-tag v-else type="info" effect="light">今日平稳</el-tag>
              <el-tag v-if="item.stale" type="warning" effect="light">未更新</el-tag>
            </div>
            <div class="points-account-subtitle">
              <span>{{ item.account.wechat_id }}</span>
              <span v-if="item.account.phone">手机号：{{ item.account.phone }}</span>
              <span v-if="item.account.device">设备：{{ item.account.device }}</span>
            </div>
          </div>
          <div class="points-account-actions">
            <el-tooltip content="查看未注册小程序" placement="top">
              <el-button
                class="points-icon-button"
                circle
                plain
                :disabled="!item.unregisteredProgramCount"
                @click="openUnregistered(item)"
              >
                <el-icon><Warning /></el-icon>
              </el-button>
            </el-tooltip>
            <el-button type="primary" plain @click="openDetails(item)">
              查看明细
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>

        <div class="points-account-metrics">
          <div class="points-account-metric">
            <span class="points-account-metric-label">账号总积分</span>
            <strong>{{ formatNumber(item.totalPoints) }}</strong>
          </div>
          <div class="points-account-metric">
            <span class="points-account-metric-label">今日变化</span>
            <strong :class="diffClass(item.totalDiff)">{{ formatSigned(item.totalDiff) }}</strong>
          </div>
          <div class="points-account-metric">
            <span class="points-account-metric-label">活跃小程序</span>
            <strong>{{ item.activeProgramCount }}</strong>
          </div>
          <div class="points-account-metric">
            <span class="points-account-metric-label">已登记项目</span>
            <strong>{{ item.registeredProgramCount }}</strong>
          </div>
        </div>

        <div class="points-account-meta">
          <span class="points-meta-chip">
            <el-icon><Clock /></el-icon>
            最近更新：{{ formatDate(item.latestReportTime) }}
          </span>
          <span class="points-meta-chip" :class="item.totalDiff >= 0 ? 'positive' : 'negative'">
            <el-icon><TrendCharts /></el-icon>
            波动：{{ item.totalDiff === 0 ? '平稳' : item.totalDiff > 0 ? '上涨中' : '回落中' }}
          </span>
        </div>

        <div class="points-top-programs">
          <div class="points-block-title">Top 小程序</div>
          <div v-if="item.topPrograms.length" class="points-program-list">
            <div
              v-for="program in item.topPrograms"
              :key="`${item.account.wechat_id}-${program.program_id}`"
              class="points-program-item"
            >
              <div class="points-program-main">
                <div class="points-program-name">{{ program.program_name }}</div>
                <div class="points-program-time">{{ formatDate(program.report_time) }}</div>
              </div>
              <div class="points-program-side">
                <div class="points-program-points">{{ formatNumber(program.points) }}</div>
                <div class="points-program-diff" :class="diffClass(program.diff)">{{ formatSigned(program.diff) }}</div>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无积分明细" :image-size="88" />
        </div>
      </article>
    </section>

    <el-empty v-else description="没有符合筛选条件的账号" class="toolbar-card" />

    <el-drawer
      v-model="detailVisible"
      class="points-detail-drawer"
      :size="drawerSize"
      :with-header="false"
    >
      <template v-if="selectedAccount">
        <div class="points-detail-stack">
          <section class="points-detail-hero">
            <div class="points-detail-hero-main">
              <div class="points-detail-title-row">
                <h2 class="points-detail-title">{{ selectedAccount.account.nickname || selectedAccount.account.wechat_id }}</h2>
                <el-tag v-if="selectedAccount.stale" type="warning" effect="light">今日未更新</el-tag>
              </div>
              <div class="points-detail-subtitle">
                <span>{{ selectedAccount.account.wechat_id }}</span>
                <span v-if="selectedAccount.account.phone">手机号：{{ selectedAccount.account.phone }}</span>
                <span v-if="selectedAccount.account.device">设备：{{ selectedAccount.account.device }}</span>
              </div>
            </div>
            <div class="points-detail-hero-actions">
              <el-button @click="detailVisible = false">关闭</el-button>
            </div>
          </section>

          <section class="points-detail-summary">
            <div class="points-detail-summary-item">
              <span>总积分</span>
              <strong>{{ formatNumber(selectedAccount.totalPoints) }}</strong>
            </div>
            <div class="points-detail-summary-item">
              <span>今日变化</span>
              <strong :class="diffClass(selectedAccount.totalDiff)">{{ formatSigned(selectedAccount.totalDiff) }}</strong>
            </div>
            <div class="points-detail-summary-item">
              <span>活跃项目</span>
              <strong>{{ selectedAccount.activeProgramCount }}</strong>
            </div>
            <div class="points-detail-summary-item">
              <span>最近更新时间</span>
              <strong>{{ formatDate(selectedAccount.latestReportTime) }}</strong>
            </div>
          </section>

          <section class="toolbar-card points-detail-toolbar-card">
            <div class="points-detail-toolbar">
              <el-input
                v-model="detailKeyword"
                clearable
                placeholder="搜索小程序名称 / program_id"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>

              <el-select v-model="detailSortMode">
                <el-option label="按积分排序" value="points" />
                <el-option label="按今日变化排序" value="diff" />
                <el-option label="按更新时间排序" value="report_time" />
                <el-option label="按名称排序" value="name" />
              </el-select>

              <el-switch
                v-model="detailOnlyChanged"
                inline-prompt
                active-text="仅异常"
                inactive-text="全部"
              />
            </div>
          </section>

          <section class="points-detail-programs">
            <article
              v-for="program in detailPrograms"
              :key="`${selectedAccount.account.wechat_id}-${program.program_id}`"
              class="points-detail-program-card"
            >
              <div class="points-detail-program-main">
                <div class="points-detail-program-name">{{ program.program_name }}</div>
                <div class="points-detail-program-id">{{ program.program_id }}</div>
              </div>
              <div class="points-detail-program-side">
                <div class="points-detail-program-points">{{ formatPointsValue(program.points) }}</div>
                <div class="points-detail-program-diff" :class="diffClass(program.diff)">{{ formatSigned(program.diff) }}</div>
              </div>
              <div class="points-detail-program-foot">
                <span>更新时间：{{ formatDate(program.report_time) }}</span>
                <el-tag v-if="program.points === '未注册'" type="info" effect="light">未注册</el-tag>
                <el-tag v-else-if="program.diff > 0" type="success" effect="light">上涨</el-tag>
                <el-tag v-else-if="program.diff < 0" type="danger" effect="light">下降</el-tag>
                <el-tag v-else type="info" effect="light">平稳</el-tag>
              </div>
            </article>

            <el-empty v-if="!detailPrograms.length" description="没有符合条件的小程序数据" :image-size="88" />
          </section>
        </div>
      </template>
    </el-drawer>

    <el-drawer
      v-model="unregisteredVisible"
      class="points-unregistered-drawer"
      :size="drawerSize"
      :with-header="false"
    >
      <template v-if="selectedAccount">
        <div class="points-detail-stack">
          <section class="points-detail-hero points-unregistered-hero">
            <div class="points-detail-hero-main">
              <div class="points-detail-title-row">
                <h2 class="points-detail-title">未注册小程序</h2>
                <el-tag type="warning" effect="light">{{ selectedAccount.unregisteredProgramCount }} 个待处理</el-tag>
              </div>
              <div class="points-detail-subtitle">
                <span>{{ selectedAccount.account.nickname || selectedAccount.account.wechat_id }}</span>
                <span>{{ selectedAccount.account.wechat_id }}</span>
              </div>
            </div>
            <div class="points-detail-hero-actions">
              <el-button @click="unregisteredVisible = false">关闭</el-button>
            </div>
          </section>

          <section class="toolbar-card points-unregistered-summary-card">
            <div class="points-unregistered-summary">
              <div class="points-unregistered-summary-item">
                <span>未注册数量</span>
                <strong>{{ selectedAccount.unregisteredProgramCount }}</strong>
              </div>
              <div class="points-unregistered-summary-item">
                <span>账号设备</span>
                <strong>{{ selectedAccount.account.device || '未填写' }}</strong>
              </div>
              <div class="points-unregistered-summary-item">
                <span>手机号</span>
                <strong>{{ selectedAccount.account.phone || '未填写' }}</strong>
              </div>
            </div>
          </section>

          <section v-if="unregisteredPrograms.length" class="points-unregistered-list">
            <article
              v-for="program in unregisteredPrograms"
              :key="`${selectedAccount.account.wechat_id}-unregistered-${program.program_id}`"
              class="points-unregistered-card"
            >
              <div class="points-unregistered-main">
                <div class="points-unregistered-name">{{ program.program_name || '未命名小程序' }}</div>
                <div class="points-unregistered-id">{{ program.program_id }}</div>
              </div>
              <div class="points-unregistered-side">
                <el-tag type="warning" effect="light">未注册</el-tag>
                <span class="points-unregistered-time">最近记录：{{ formatDate(program.report_time) }}</span>
              </div>
            </article>
          </section>

          <el-empty v-else description="当前账号没有未注册小程序" :image-size="88" />
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  ArrowRight,
  Clock,
  Coin,
  Grid,
  RefreshRight,
  Search,
  TrendCharts,
  UserFilled,
  Warning,
} from '@element-plus/icons-vue'
import api from '../api'

const loading = ref(false)
const items = ref([])
const searchKeyword = ref('')
const sortMode = ref('totalPoints')
const quickFilter = ref('all')

const detailVisible = ref(false)
const selectedAccount = ref(null)
const detailKeyword = ref('')
const detailSortMode = ref('points')
const detailOnlyChanged = ref(false)
const unregisteredVisible = ref(false)

const drawerSize = computed(() => (window.innerWidth <= 768 ? '100%' : '720px'))

function parseDate(value) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function formatDate(value) {
  if (!value) return '暂无'
  const date = parseDate(value)
  if (!date) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

function formatNumber(value) {
  if (typeof value !== 'number') return value
  return value.toLocaleString('zh-CN')
}

function formatCompactNumber(value) {
  if (typeof value !== 'number') return value
  if (Math.abs(value) >= 10000) {
    return `${(value / 10000).toFixed(value >= 100000 ? 0 : 1)}w`
  }
  return formatNumber(value)
}

function formatSigned(value) {
  const numberValue = Number(value || 0)
  if (numberValue > 0) return `+${formatNumber(numberValue)}`
  return `${formatNumber(numberValue)}`
}

function formatPointsValue(value) {
  return typeof value === 'number' ? formatNumber(value) : value
}

function diffClass(value) {
  if (value > 0) return 'is-positive'
  if (value < 0) return 'is-negative'
  return 'is-neutral'
}

function normalizeAccountItem(item) {
  const points = Array.isArray(item.points) ? item.points : []
  const unregisteredPrograms = points.filter((entry) => entry.points === '未注册' || entry.points === 0)
  const registeredPoints = points.filter((entry) => typeof entry.points === 'number' && entry.points > 0)
  const totalPoints = registeredPoints.reduce((sum, entry) => sum + (entry.points || 0), 0)
  const totalDiff = registeredPoints.reduce((sum, entry) => sum + (entry.diff || 0), 0)
  const latestReport = registeredPoints
    .map((entry) => entry.report_time)
    .filter(Boolean)
    .sort((a, b) => new Date(b) - new Date(a))[0] || null

  const latestDate = parseDate(latestReport)
  const now = new Date()
  const stale = !latestDate || latestDate.toDateString() !== now.toDateString()

  const topPrograms = [...registeredPoints]
    .sort((a, b) => (b.points || 0) - (a.points || 0))
    .slice(0, 3)

  return {
    ...item,
    totalPoints,
    totalDiff,
    latestReportTime: latestReport,
    stale,
    registeredProgramCount: registeredPoints.length,
    unregisteredPrograms,
    unregisteredProgramCount: unregisteredPrograms.length,
    activeProgramCount: item.active_program_count || 0,
    topPrograms,
  }
}

const normalizedItems = computed(() => items.value.map(normalizeAccountItem))

const summary = computed(() => {
  const list = normalizedItems.value
  return {
    accountCount: list.length,
    activeProgramCount: list.reduce((sum, item) => sum + item.activeProgramCount, 0),
    totalPoints: list.reduce((sum, item) => sum + item.totalPoints, 0),
    totalDiff: list.reduce((sum, item) => sum + item.totalDiff, 0),
    positiveAccounts: list.filter((item) => item.totalDiff > 0).length,
    negativeAccounts: list.filter((item) => item.totalDiff < 0).length,
    staleAccounts: list.filter((item) => item.stale).length,
    latestReportTime: [...list]
      .map((item) => item.latestReportTime)
      .filter(Boolean)
      .sort((a, b) => new Date(b) - new Date(a))[0] || null,
    topAccountName: [...list].sort((a, b) => b.totalPoints - a.totalPoints)[0]?.account.nickname
      || [...list].sort((a, b) => b.totalPoints - a.totalPoints)[0]?.account.wechat_id
      || '',
    topDiff: [...list].sort((a, b) => b.totalDiff - a.totalDiff)[0]?.totalDiff || 0,
  }
})

const filteredItems = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  const list = normalizedItems.value.filter((item) => {
    const searchable = [
      item.account.nickname,
      item.account.wechat_id,
      item.account.phone,
      item.account.device,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()

    const matchedKeyword = !keyword || searchable.includes(keyword)
    if (!matchedKeyword) return false

    switch (quickFilter.value) {
      case 'positive':
        return item.totalDiff > 0
      case 'negative':
        return item.totalDiff < 0
      case 'warning':
        return item.stale || item.totalDiff < 0
      case 'stale':
        return item.stale
      case 'active':
        return item.activeProgramCount > 0
      default:
        return true
    }
  })

  return list.sort((a, b) => {
    switch (sortMode.value) {
      case 'totalDiff':
        return b.totalDiff - a.totalDiff
      case 'activePrograms':
        return b.activeProgramCount - a.activeProgramCount || b.totalPoints - a.totalPoints
      case 'latestReport': {
        const timeA = a.latestReportTime ? new Date(a.latestReportTime).getTime() : 0
        const timeB = b.latestReportTime ? new Date(b.latestReportTime).getTime() : 0
        return timeB - timeA
      }
      case 'totalPoints':
      default:
        return b.totalPoints - a.totalPoints
    }
  })
})

const detailPrograms = computed(() => {
  if (!selectedAccount.value) return []

  const keyword = detailKeyword.value.trim().toLowerCase()
  const source = selectedAccount.value.points.filter((program) => {
    const matchedKeyword = !keyword || `${program.program_name} ${program.program_id}`.toLowerCase().includes(keyword)
    if (!matchedKeyword) return false
    if (!detailOnlyChanged.value) return true
    return program.diff !== 0 || program.points === '未注册'
  })

  return [...source].sort((a, b) => {
    switch (detailSortMode.value) {
      case 'diff':
        return (b.diff || 0) - (a.diff || 0)
      case 'report_time': {
        const timeA = a.report_time ? new Date(a.report_time).getTime() : 0
        const timeB = b.report_time ? new Date(b.report_time).getTime() : 0
        return timeB - timeA
      }
      case 'name':
        return `${a.program_name}`.localeCompare(`${b.program_name}`, 'zh-CN')
      case 'points':
      default: {
        const pointsA = typeof a.points === 'number' ? a.points : -1
        const pointsB = typeof b.points === 'number' ? b.points : -1
        return pointsB - pointsA
      }
    }
  })
})

const unregisteredPrograms = computed(() => selectedAccount.value?.unregisteredPrograms || [])

function openDetails(item) {
  selectedAccount.value = item
  detailKeyword.value = ''
  detailSortMode.value = 'points'
  detailOnlyChanged.value = false
  detailVisible.value = true
}

function openUnregistered(item) {
  selectedAccount.value = item
  unregisteredVisible.value = true
}

async function loadPoints() {
  loading.value = true
  try {
    const { data } = await api.get('/points')
    items.value = data.items || []
  } catch (error) {
    console.error(error)
    ElMessage.error('加载积分总览失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadPoints)
</script>
