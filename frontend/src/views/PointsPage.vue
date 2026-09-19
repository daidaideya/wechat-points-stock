<template>
  <div class="points-page page-stack">
    <section class="points-hero toolbar-card">
      <div class="points-hero-head">
        <div>
          <div class="section-title">积分驾驶舱</div>
          <p class="section-description">聚焦账号资产、今日波动和最近同步情况，快速定位高积分账号与异常变化。</p>
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
        <el-input v-model="searchKeyword" clearable placeholder="搜索昵称 / 微信号 / 手机号 / 设备">
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
        <span class="points-toolbar-text">
          当前展示 {{ filteredItems.length }} / {{ normalizedItems.length }} 个账号
        </span>
        <div class="points-toolbar-tags">
          <span class="points-filter-chip">Top 账号：{{ summary.topAccountName || '暂无' }}</span>
          <span class="points-filter-chip">最大涨幅：{{ formatSigned(summary.topDiff) }}</span>
        </div>
      </div>
    </section>

    <el-skeleton v-if="loading" :rows="10" animated class="toolbar-card" />

    <section v-else-if="filteredItems.length" class="points-account-grid">
      <PointsAccountCard
        v-for="item in filteredItems"
        :key="item.account.wechat_id"
        :item="item"
        :format="formatters"
        @open-details="openDetails"
        @open-unregistered="openUnregistered"
      />
    </section>

    <el-empty v-else description="没有符合筛选条件的账号" class="toolbar-card" />

    <PointsAccountDetailsDrawer
      v-model:detail-visible="detailVisible"
      v-model:unregistered-visible="unregisteredVisible"
      :account="selectedAccount"
      :drawer-size="drawerSize"
      :formatters="formatters"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Clock, Coin, Grid, RefreshRight, Search, TrendCharts, UserFilled, Warning } from '@element-plus/icons-vue'
import api from '../api'
import PointsAccountCard from '../components/PointsAccountCard.vue'
import PointsAccountDetailsDrawer from '../components/PointsAccountDetailsDrawer.vue'
import { useViewport } from '../composables/useViewport'
import { useAbortableRequest } from '../composables/useAbortableRequest'
import { getApiErrorMessage, isRequestCanceled } from '../utils/apiError'
import { formatApiDate as formatDate, getApiDateKey, parseApiDate } from '../utils/date'

const loading = ref(false)
const items = ref([])
const requestController = useAbortableRequest()
const searchKeyword = ref('')
const sortMode = ref('totalPoints')
const quickFilter = ref('all')

const detailVisible = ref(false)
const selectedAccount = ref(null)
const unregisteredVisible = ref(false)

const { isMobile: isNarrowViewport } = useViewport({ mobileMax: 768 })
const drawerSize = computed(() => (isNarrowViewport.value ? '100%' : '720px'))

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
  if (value === '未注册' || value === null || value === undefined) return value === '未注册' ? '未注册' : '—'
  return typeof value === 'number' ? formatNumber(value) : value
}

function formatCash(value) {
  if (value === '未注册') return '未注册'
  if (value === null || value === undefined || value === '') return '—'
  const numberValue = Number(value)
  if (Number.isNaN(numberValue)) return '—'
  return `¥${numberValue.toLocaleString('zh-CN', { maximumFractionDigits: 4 })}`
}

function formatSignedCash(value) {
  const numberValue = Number(value || 0)
  const body = Math.abs(numberValue).toLocaleString('zh-CN', { maximumFractionDigits: 4 })
  if (numberValue > 0) return `+¥${body}`
  if (numberValue < 0) return `-¥${body}`
  return `¥${body}`
}

function diffClass(value) {
  if (value > 0) return 'is-positive'
  if (value < 0) return 'is-negative'
  return 'is-neutral'
}

function isRegisteredEntry(entry) {
  const hasPoints = typeof entry.points === 'number'
  const hasCash = typeof entry.cash === 'number'
  return hasPoints || hasCash
}

function isUnregisteredEntry(entry) {
  const pointsEmpty = entry.points === '未注册' || entry.points === 0 || entry.points == null
  const cashEmpty = entry.cash === '未注册' || entry.cash === 0 || entry.cash == null
  return pointsEmpty && cashEmpty
}

function normalizeAccountItem(item) {
  const points = Array.isArray(item.points) ? item.points : []
  const unregisteredPrograms = points.filter((entry) => isUnregisteredEntry(entry))
  const registeredPoints = points.filter(
    (entry) =>
      isRegisteredEntry(entry) &&
      ((typeof entry.points === 'number' && entry.points > 0) || (typeof entry.cash === 'number' && entry.cash > 0)),
  )
  const totalPoints = registeredPoints.reduce(
    (sum, entry) => sum + (typeof entry.points === 'number' ? entry.points : 0),
    0,
  )
  const totalCash = registeredPoints.reduce((sum, entry) => sum + (typeof entry.cash === 'number' ? entry.cash : 0), 0)
  const totalDiff = registeredPoints.reduce((sum, entry) => sum + (entry.diff || 0), 0)
  const totalCashDiff = registeredPoints.reduce((sum, entry) => sum + (entry.cash_diff || 0), 0)
  const latestReport =
    registeredPoints
      .map((entry) => entry.report_time)
      .filter(Boolean)
      .sort((a, b) => new Date(b) - new Date(a))[0] || null

  const latestDate = parseApiDate(latestReport)
  const stale = !latestDate || getApiDateKey(latestDate) !== getApiDateKey(new Date())

  const topPrograms = [...registeredPoints]
    .sort((a, b) => {
      const ap = typeof a.points === 'number' ? a.points : 0
      const bp = typeof b.points === 'number' ? b.points : 0
      const ac = typeof a.cash === 'number' ? a.cash : 0
      const bc = typeof b.cash === 'number' ? b.cash : 0
      return bp - ap || bc - ac
    })
    .slice(0, 3)

  return {
    ...item,
    totalPoints,
    totalCash,
    totalDiff,
    totalCashDiff,
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
    latestReportTime:
      [...list]
        .map((item) => item.latestReportTime)
        .filter(Boolean)
        .sort((a, b) => new Date(b) - new Date(a))[0] || null,
    topAccountName:
      [...list].sort((a, b) => b.totalPoints - a.totalPoints)[0]?.account.nickname ||
      [...list].sort((a, b) => b.totalPoints - a.totalPoints)[0]?.account.wechat_id ||
      '',
    topDiff: [...list].sort((a, b) => b.totalDiff - a.totalDiff)[0]?.totalDiff || 0,
  }
})

const filteredItems = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  const list = normalizedItems.value.filter((item) => {
    const searchable = [item.account.nickname, item.account.wechat_id, item.account.phone, item.account.device]
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

function openDetails(item) {
  selectedAccount.value = item
  detailVisible.value = true
}

function openUnregistered(item) {
  selectedAccount.value = item
  unregisteredVisible.value = true
}

async function loadPoints() {
  const request = requestController.start()
  loading.value = true
  try {
    const { data } = await api.get('/points', { signal: request.signal })
    if (!request.isCurrent()) return
    items.value = data.items || []
  } catch (error) {
    if (!request.isCurrent() || isRequestCanceled(error)) return
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '加载积分总览失败'))
  } finally {
    if (request.isCurrent()) {
      loading.value = false
      request.finish()
    }
  }
}

const formatters = {
  formatDate,
  formatNumber,
  formatCash,
  formatSigned,
  formatSignedCash,
  formatPointsValue,
  diffClass,
}

onMounted(loadPoints)
</script>
