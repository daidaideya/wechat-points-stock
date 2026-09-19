<template>
  <div class="page-stack dashboard-page">
    <section class="dashboard-metrics-grid dashboard-metrics-grid-compact">
      <DashboardMetricCard v-for="card in cards" :key="card.label" :card="card" @activate="handleCardClick" />
    </section>

    <DashboardActivityPanels
      v-model:unreported-dialog-visible="unreportedDialogVisible"
      :loading="loading"
      :recent-updates="recentUpdates"
      :unreported-programs="unreportedPrograms"
      :all-unreported-programs="allUnreportedPrograms"
      :unreported-dialog-loading="unreportedDialogLoading"
      :format-date="formatDate"
      @refresh="loadDashboard"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Box, DataLine, Grid, Star, User, Warning } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import api from '../api'
import DashboardActivityPanels from '../components/DashboardActivityPanels.vue'
import DashboardMetricCard from '../components/DashboardMetricCard.vue'
import { useAbortableRequest } from '../composables/useAbortableRequest'
import { getApiErrorMessage, isRequestCanceled } from '../utils/apiError'
import { formatApiDate as formatDate } from '../utils/date'

const router = useRouter()
const loading = ref(false)
const summary = ref({})
const recentUpdates = ref([])
const unreportedPrograms = ref([])
const allUnreportedPrograms = ref([])
const unreportedDialogVisible = ref(false)
const unreportedDialogLoading = ref(false)
const dashboardRequestController = useAbortableRequest()
const unreportedRequestController = useAbortableRequest()

const cards = computed(() => [
  {
    label: '微信号',
    value: summary.value.account_count ?? 0,
    description: '系统内已管理账号总数',
    emphasis: `今日活跃 ${summary.value.active_accounts_today ?? 0}`,
    icon: User,
    tone: 'tone-wheat',
    action: 'route',
    route: '/users',
    clickable: true,
  },
  {
    label: '小程序',
    value: summary.value.program_count ?? 0,
    description: '当前已接入监控的小程序数量',
    emphasis: `特别关注 ${summary.value.favorite_count ?? 0}`,
    icon: Grid,
    tone: 'tone-sand',
    action: 'route',
    route: '/programs',
    clickable: true,
  },
  {
    label: '商品总数',
    value: summary.value.total_products_count ?? 0,
    description: '库存库中已录入的商品数量',
    emphasis: `缺货 ${summary.value.out_of_stock_count ?? 0}`,
    icon: Box,
    tone: 'tone-honey',
    action: 'route',
    route: '/stock',
    clickable: true,
  },
  {
    label: '今日未报',
    value: summary.value.unreported_count ?? 0,
    description: '当天尚未同步积分的小程序数量',
    emphasis: (summary.value.unreported_count ?? 0) > 0 ? '点击查看完整列表' : '当前状态正常',
    icon: Warning,
    tone: 'tone-apricot',
    action: 'dialog',
    clickable: true,
  },
  {
    label: '总记录数',
    value: summary.value.points_records_count ?? 0,
    description: '历史积分明细累计条数',
    emphasis: '支持时间维度追踪',
    icon: DataLine,
    tone: 'tone-latte',
    clickable: false,
  },
  {
    label: '收藏关注',
    value: summary.value.favorite_count ?? 0,
    description: '已收藏的小程序重点集合',
    emphasis: '便于快速筛查重点项目',
    icon: Star,
    tone: 'tone-gold',
    clickable: false,
  },
])

async function fetchUnreportedPrograms() {
  const request = unreportedRequestController.start()
  const { data } = await api.get('/programs/unreported', { signal: request.signal })
  if (!request.isCurrent()) return []
  request.finish()
  return data?.items || []
}

async function openUnreportedDialog() {
  unreportedDialogVisible.value = true
  unreportedDialogLoading.value = true
  try {
    const items = await fetchUnreportedPrograms()
    allUnreportedPrograms.value = items
  } catch (error) {
    if (isRequestCanceled(error)) return
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '加载今日未报列表失败'))
  } finally {
    unreportedDialogLoading.value = false
  }
}

function handleCardClick(card) {
  if (!card?.clickable) return
  if (card.action === 'route' && card.route) {
    router.push(card.route)
    return
  }
  if (card.action === 'dialog') {
    openUnreportedDialog()
  }
}

async function loadDashboard() {
  const request = dashboardRequestController.start()
  loading.value = true
  try {
    const { data } = await api.get('/dashboard', { signal: request.signal })
    if (!request.isCurrent()) return
    summary.value = data || {}
    recentUpdates.value = data?.recent_program_updates || []
    // 后端在 /dashboard 直接给出 unreported_top（前 5 条），首屏不再多发一次 /programs/unreported
    unreportedPrograms.value = data?.unreported_top || []
    // 列表对话框打开时再单独 fetch 全部，不阻塞首屏
    allUnreportedPrograms.value = []
  } catch (error) {
    if (!request.isCurrent() || isRequestCanceled(error)) return
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '加载仪表盘失败'))
  } finally {
    if (request.isCurrent()) {
      loading.value = false
      request.finish()
    }
  }
}

onMounted(loadDashboard)
</script>
