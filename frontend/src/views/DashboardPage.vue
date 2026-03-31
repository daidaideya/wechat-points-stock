<template>
  <div class="page-stack dashboard-page">
    <section class="dashboard-metrics-grid dashboard-metrics-grid-compact">
      <el-card
        v-for="card in cards"
        :key="card.label"
        shadow="hover"
        class="dashboard-metric-card dashboard-interactive-card"
        :class="[card.tone, { clickable: card.clickable }]"
        @click="handleCardClick(card)"
      >
        <div class="dashboard-metric-top">
          <div>
            <div class="dashboard-metric-label">{{ card.label }}</div>
            <div class="dashboard-metric-value">{{ card.value }}</div>
          </div>
          <div class="dashboard-metric-icon">
            <el-icon><component :is="card.icon" /></el-icon>
          </div>
        </div>
        <div class="dashboard-metric-footer">
          <span>{{ card.description }}</span>
          <span v-if="card.emphasis" class="dashboard-metric-emphasis">{{ card.emphasis }}</span>
        </div>
      </el-card>
    </section>

    <section class="dashboard-bottom-grid aligned-dashboard-grid">
      <el-card shadow="never" class="dashboard-panel-card recent-panel-card aligned-list-card">
        <template #header>
          <div class="dashboard-panel-header aligned-panel-header">
            <div class="dashboard-panel-title-wrap">
              <span class="dashboard-panel-icon soft-blue">
                <el-icon><Clock /></el-icon>
              </span>
              <div>
                <div class="dashboard-panel-title">最新小程序更新</div>
                <div class="dashboard-panel-subtitle">快速查看最近同步的记录与时间</div>
              </div>
            </div>
            <el-button text @click="loadDashboard">刷新</el-button>
          </div>
        </template>

        <el-skeleton v-if="loading" :rows="6" animated />
        <el-empty v-else-if="!recentUpdates.length" description="暂无更新记录" />
        <div v-else class="recent-update-list aligned-panel-list">
          <div v-for="item in recentUpdates" :key="`${item.program_id}-${item.wechat_id}-${item.report_time}`" class="recent-update-item aligned-list-item">
            <div class="recent-update-main">
              <div class="recent-update-name-row">
                <span class="recent-update-name">{{ item.program_name || item.program_id || '未知小程序' }}</span>
                <el-tag size="small" round effect="plain">{{ item.points ?? 0 }} 积分</el-tag>
              </div>
              <div class="recent-update-meta">
                <span>{{ item.program_id || '未知 AppID' }}</span>
                <span>{{ item.wechat_id || '未知微信号' }}</span>
              </div>
            </div>
            <div class="recent-update-time">{{ formatDate(item.report_time) }}</div>
          </div>
        </div>
      </el-card>

      <el-card shadow="never" class="dashboard-panel-card dashboard-side-panel aligned-list-card">
        <template #header>
          <div class="dashboard-panel-header aligned-panel-header">
            <div class="dashboard-panel-title-wrap">
              <span class="dashboard-panel-icon soft-orange">
                <el-icon><Warning /></el-icon>
              </span>
              <div>
                <div class="dashboard-panel-title">今天没报的小程序</div>
                <div class="dashboard-panel-subtitle">当天尚未同步积分的小程序列表</div>
              </div>
            </div>
            <el-tag round effect="plain" type="danger">{{ unreportedPrograms.length }} 个</el-tag>
          </div>
        </template>

        <el-skeleton v-if="loading" :rows="6" animated />
        <el-empty v-else-if="!unreportedPrograms.length" description="今天全部已上报" />
        <div v-else class="recent-update-list aligned-panel-list unreported-program-list">
          <div v-for="item in unreportedPrograms" :key="item.program_id" class="recent-update-item aligned-list-item unreported-program-item">
            <div class="recent-update-main">
              <div class="recent-update-name-row">
                <span class="recent-update-name">{{ item.program_name || item.program_id || '未知小程序' }}</span>
                <el-tag size="small" round effect="plain" :type="item.is_favorite ? 'warning' : 'info'">
                  {{ item.is_favorite ? '重点关注' : '待上报' }}
                </el-tag>
              </div>
              <div class="recent-update-meta">
                <span>{{ item.program_id || '未知 AppID' }}</span>
                <span v-if="(item.tags || []).length">{{ item.tags.join(' / ') }}</span>
                <span v-else>暂无标签</span>
              </div>
            </div>
            <div class="recent-update-time">{{ formatDate(item.last_report_time || item.last_update_time) }}</div>
          </div>
        </div>
      </el-card>
    </section>

    <el-dialog v-model="unreportedDialogVisible" title="今天没报的小程序" width="960px" class="dashboard-unreported-dialog">
      <div v-if="unreportedDialogLoading" class="dashboard-dialog-loading">
        <el-skeleton :rows="8" animated />
      </div>
      <el-empty v-else-if="!allUnreportedPrograms.length" description="今天全部已上报" />
      <div v-else class="dashboard-dialog-list">
        <div v-for="item in allUnreportedPrograms" :key="`dialog-${item.program_id}`" class="dashboard-dialog-item">
          <div class="dashboard-dialog-main">
            <div class="dashboard-dialog-name-row">
              <span class="dashboard-dialog-name">{{ item.program_name || item.program_id || '未知小程序' }}</span>
              <el-tag size="small" round effect="plain" :type="item.is_favorite ? 'warning' : 'info'">
                {{ item.is_favorite ? '重点关注' : '待上报' }}
              </el-tag>
            </div>
            <div class="dashboard-dialog-meta">
              <span>{{ item.program_id || '未知 AppID' }}</span>
              <span v-if="(item.tags || []).length">{{ item.tags.join(' / ') }}</span>
              <span v-else>暂无标签</span>
              <span v-if="item.note">备注：{{ item.note }}</span>
            </div>
          </div>
          <div class="dashboard-dialog-time">{{ formatDate(item.last_report_time || item.last_update_time) }}</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Box,
  Clock,
  DataLine,
  Grid,
  Star,
  User,
  Warning,
} from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const loading = ref(false)
const summary = ref({})
const recentUpdates = ref([])
const unreportedPrograms = ref([])
const allUnreportedPrograms = ref([])
const unreportedDialogVisible = ref(false)
const unreportedDialogLoading = ref(false)

const cards = computed(() => [
  {
    label: '微信号',
    value: summary.value.account_count ?? 0,
    description: '系统内已管理账号总数',
    emphasis: `今日活跃 ${summary.value.active_accounts_today ?? 0}`,
    icon: User,
    tone: 'tone-wheat',
    action: 'route',
    route: '/points',
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

function formatDate(value) {
  if (!value) return '暂无'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

async function fetchUnreportedPrograms() {
  const { data } = await api.get('/programs/unreported')
  return data?.items || []
}

async function openUnreportedDialog() {
  unreportedDialogVisible.value = true
  unreportedDialogLoading.value = true
  try {
    const items = await fetchUnreportedPrograms()
    allUnreportedPrograms.value = items
  } catch (error) {
    console.error(error)
    ElMessage.error('加载今日未报列表失败')
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
  loading.value = true
  try {
    const [{ data }, unreportedItems] = await Promise.all([
      api.get('/dashboard'),
      fetchUnreportedPrograms(),
    ])
    summary.value = data || {}
    recentUpdates.value = data?.recent_program_updates || []
    allUnreportedPrograms.value = unreportedItems
    unreportedPrograms.value = unreportedItems.slice(0, 5)
  } catch (error) {
    console.error(error)
    ElMessage.error('加载仪表盘失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>
