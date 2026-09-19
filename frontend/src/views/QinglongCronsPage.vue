<template>
  <div class="page-stack ql-crons-page">
    <section class="toolbar-card ql-hero">
      <div class="ql-hero-head">
        <div>
          <div class="section-title">青龙定时</div>
          <p class="section-description">查看青龙脚本每日执行时间线，识别间隔过密的任务，并一键重排执行间隔。</p>
        </div>
        <div class="ql-hero-actions">
          <el-button :loading="loading" @click="loadCrons">
            <el-icon><RefreshRight /></el-icon>
            刷新数据
          </el-button>
        </div>
      </div>

      <div class="points-metrics-grid">
        <article class="points-metric-card tone-blue">
          <div class="points-metric-top">
            <div>
              <div class="points-metric-label">脚本任务</div>
              <div class="points-metric-value">{{ scriptCrons.length }}</div>
            </div>
            <span class="points-metric-icon">
              <el-icon><Document /></el-icon>
            </span>
          </div>
          <div class="points-metric-foot">青龙面板中的全部脚本任务</div>
        </article>

        <article class="points-metric-card tone-green">
          <div class="points-metric-top">
            <div>
              <div class="points-metric-label">启用</div>
              <div class="points-metric-value">{{ enabledCrons.length }}</div>
            </div>
            <span class="points-metric-icon">
              <el-icon><CircleCheck /></el-icon>
            </span>
          </div>
          <div class="points-metric-foot">参与时间线整理的任务数量</div>
        </article>

        <article class="points-metric-card tone-red">
          <div class="points-metric-top">
            <div>
              <div class="points-metric-label">已禁用</div>
              <div class="points-metric-value">{{ disabledCrons.length }}</div>
            </div>
            <span class="points-metric-icon">
              <el-icon><CircleClose /></el-icon>
            </span>
          </div>
          <div class="points-metric-foot">已停用，不参与整理</div>
        </article>

        <article class="points-metric-card tone-amber ql-next-slot-card">
          <div class="points-metric-top">
            <div>
              <div class="points-metric-label">新脚本时间</div>
              <div class="points-metric-value ql-coverage-value">{{ nextSlotTime || '-' }}</div>
            </div>
            <span class="points-metric-icon">
              <el-icon><CopyDocument /></el-icon>
            </span>
          </div>
          <div class="points-metric-foot ql-next-slot-foot">
            <code class="ql-next-slot-code">{{ nextSlotSchedule || '暂无可复制的表达式' }}</code>
            <el-button size="small" type="primary" plain :disabled="!nextSlotSchedule" @click="copyNextSlot">
              复制
            </el-button>
          </div>
          <div v-if="nextSlotLastSchedule" class="ql-next-slot-hint">
            基于最新脚本「{{ nextSlotLastName }}」{{ nextSlotLastSchedule }} +{{ planForm.intervalMinutes || 2 }} 分钟
          </div>
        </article>
      </div>

      <div class="points-hero-meta">
        <span class="points-meta-chip">
          <el-icon><Search /></el-icon>
          <input v-model="keyword" class="ql-meta-search" type="text" placeholder="搜索名称 / 命令" />
        </span>
        <span v-if="crowdedCount" class="points-meta-chip warning">
          <el-icon><Warning /></el-icon>
          {{ crowdedCount }} 个任务间隔小于 {{ planForm.intervalMinutes }} 分钟
        </span>
        <span v-if="excludedCronNames.size" class="points-meta-chip ql-excluded-meta-chip">
          <el-icon><Remove /></el-icon>
          黑名单 {{ excludedCronNames.size }} 个脚本
          <el-button link size="small" type="primary" class="ql-clear-excluded-btn" @click="clearAllExcluded">
            清空
          </el-button>
        </span>
      </div>

      <div class="ql-filter-row">
        <div class="ql-filter-label">
          <el-icon><Files /></el-icon>
          <span>脚本类型</span>
        </div>
        <div class="ql-filter-chips">
          <button
            type="button"
            class="ql-filter-chip"
            :class="{ active: commandTypeFilter === 'all' }"
            @click="commandTypeFilter = 'all'"
          >
            <span class="ql-filter-chip-dot"></span>
            全部脚本 {{ scriptCrons.length }}
          </button>
          <button
            type="button"
            class="ql-filter-chip"
            :class="{ active: commandTypeFilter === 'code' }"
            @click="commandTypeFilter = 'code'"
          >
            <span class="ql-filter-chip-dot"></span>
            code 版 {{ codeCronsCount }}
          </button>
          <button
            type="button"
            class="ql-filter-chip"
            :class="{ active: commandTypeFilter === 'other' }"
            @click="commandTypeFilter = 'other'"
          >
            <span class="ql-filter-chip-dot"></span>
            其他命令 {{ otherCronsCount }}
          </button>
        </div>
      </div>
    </section>

    <el-card shadow="never" class="ql-card">
      <template #header>
        <div class="ql-card-header">
          <div>
            <div class="ql-card-title">一键整理</div>
            <div class="ql-card-subtitle">按固定间隔为脚本分配上午和下午两个执行时间点（每日执行 2 次，早晚对应）</div>
          </div>
        </div>
      </template>
      <div class="ql-organize-form">
        <div class="ql-form-item">
          <div class="ql-form-label">上午起始时间</div>
          <el-time-picker
            v-model="planForm.startTime"
            format="HH:mm"
            value-format="HH:mm"
            :clearable="false"
            placeholder="如 07:00"
          />
        </div>
        <div class="ql-form-item">
          <div class="ql-form-label">下午起始时间</div>
          <el-time-picker
            v-model="planForm.afternoonStartTime"
            format="HH:mm"
            value-format="HH:mm"
            :clearable="false"
            placeholder="如 14:00"
          />
        </div>
        <div class="ql-form-item">
          <div class="ql-form-label">间隔（分钟）</div>
          <el-input-number v-model="planForm.intervalMinutes" :min="1" :max="120" :step="1" />
        </div>
        <div class="ql-form-item">
          <div class="ql-form-label">整理范围</div>
          <el-switch v-model="planForm.codeOnly" active-text="仅 code 版" />
        </div>
        <div class="ql-form-actions">
          <el-button type="primary" :disabled="!organizeTargetCrons.length" @click="buildPlan">生成预览</el-button>
          <span class="ql-form-hint">
            <el-icon class="ql-form-hint-icon"><Files /></el-icon>
            共 {{ organizeTargetCrons.length }} 个{{ planForm.codeOnly ? ' code 版' : '启用' }}脚本将参与重排，每日执行
            2 次
          </span>
        </div>
      </div>
      <el-alert
        v-if="!organizeTargetCrons.length && enabledCrons.length"
        type="info"
        :closable="false"
        show-icon
        :title="planForm.codeOnly ? '没有可整理的 code 版脚本' : '没有可整理的启用脚本'"
        description="当前启用脚本中没有匹配条件的任务，一键整理不会修改其他命令。"
        class="ql-plan-alert"
      />
      <el-alert
        v-else-if="planOverflow"
        type="error"
        :closable="false"
        show-icon
        title="时间窗放不下所有脚本"
        description="从起始时间到当天 24:00 的容量不足，请提前起始时间或增大间隔。"
        class="ql-plan-alert"
      />
    </el-card>

    <QinglongCronTimeline
      v-model:show-disabled="showDisabled"
      :loading="loading"
      :filtered-groups="filteredGroups"
      :interval-minutes="planForm.intervalMinutes"
      :cron-key="cronKey"
      :is-excluded="isExcluded"
      :is-crowded="isCrowded"
      :is-sparse="isSparse"
      :minute-gap="minuteGap"
      @edit="openEditDialog"
      @toggle-exclude="toggleExclude"
    />

    <QinglongCronEditDialog
      v-model="editDialogVisible"
      v-model:schedule="editScheduleText"
      :is-mobile="isMobile"
      :cron="editingCron"
      :preview-times="editPreviewTimes"
      :applying="applying"
      @save="applySingleEdit"
    />

    <QinglongCronPlanDialog
      v-model="planDialogVisible"
      :is-mobile="isMobile"
      :plan-form="planForm"
      :plan-items="planItems"
      :applying="applying"
      @apply="applyPlan"
      @apply-item="applySinglePlanItem"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  CircleCheck,
  CircleClose,
  CopyDocument,
  Document,
  Files,
  RefreshRight,
  Remove,
  Search,
  Warning,
} from '@element-plus/icons-vue'
import api from '../api'
import QinglongCronEditDialog from '../components/QinglongCronEditDialog.vue'
import QinglongCronPlanDialog from '../components/QinglongCronPlanDialog.vue'
import QinglongCronTimeline from '../components/QinglongCronTimeline.vue'
import { cronKey, formatMinute, getNextCronSlot, isCodeCron, parseDailyMinutes, parseTimeToMinute } from '../utils/cron'
import { getApiErrorMessage, isRequestCanceled } from '../utils/apiError'
import { useAbortableRequest } from '../composables/useAbortableRequest'
import { useViewport } from '../composables/useViewport'

const { isMobile } = useViewport({ mobileMax: 900 })

const loading = ref(false)
const applying = ref(false)
const crons = ref([])
const keyword = ref('')
const showDisabled = ref(false)
const commandTypeFilter = ref('code') // all | code | other

// 黑名单（不参与时间整理），持久化到 localStorage；优先使用青龙任务 ID，避免改名后失效。
const EXCLUDED_KEY = 'ql_crons_excluded_names'
const excludedCronNames = ref(loadExcludedNames())

function cronExcludeKey(cron) {
  const id = cron?.id
  if (id !== undefined && id !== null && String(id).trim()) return `id:${id}`
  const name = String(cron?.name || '').trim()
  return name ? `name:${name}` : ''
}

function cronExcludeKeys(cron) {
  const keys = []
  const primaryKey = cronExcludeKey(cron)
  if (primaryKey) keys.push(primaryKey)
  const name = String(cron?.name || '').trim()
  if (name) {
    const nameKey = `name:${name}`
    if (!keys.includes(nameKey)) keys.push(nameKey)
  }
  return keys
}

function loadExcludedNames() {
  try {
    const raw = localStorage.getItem(EXCLUDED_KEY)
    const values = raw ? JSON.parse(raw) : []
    if (!Array.isArray(values)) return new Set()
    return new Set(
      values
        .map((value) => String(value).trim())
        .filter(Boolean)
        .map((value) => (value.startsWith('id:') || value.startsWith('name:') ? value : `name:${value}`)),
    )
  } catch {
    return new Set()
  }
}

function saveExcludedNames() {
  localStorage.setItem(EXCLUDED_KEY, JSON.stringify([...excludedCronNames.value]))
}

const planForm = reactive({
  startTime: '07:00',
  intervalMinutes: 2,
  afternoonStartTime: '14:00',
  codeOnly: true,
})

const editDialogVisible = ref(false)
const editingCron = ref(null)
const editScheduleText = ref('')

const planDialogVisible = ref(false)
const planItems = ref([])
const planOverflow = ref(false)
const cronsRequestController = useAbortableRequest()

function isExcluded(cron) {
  return cronExcludeKeys(cron).some((key) => excludedCronNames.value.has(key))
}

function toggleExclude(cron) {
  const keys = cronExcludeKeys(cron)
  if (!keys.length) return
  const label = cron.name || cron.id || '未命名任务'
  if (keys.some((key) => excludedCronNames.value.has(key))) {
    keys.forEach((key) => excludedCronNames.value.delete(key))
    ElMessage.success(`已将「${label}」移出黑名单，将参与整理`)
  } else {
    excludedCronNames.value.add(keys[0])
    ElMessage.info(`已将「${label}」加入黑名单，今后不参与时间整理`)
  }
  // 触发响应式并持久化，刷新页面或重新拉取青龙任务后仍然有效。
  excludedCronNames.value = new Set(excludedCronNames.value)
  saveExcludedNames()
}

function clearAllExcluded() {
  excludedCronNames.value = new Set()
  saveExcludedNames()
  ElMessage.success('已清空全部黑名单')
}

const codeCronsCount = computed(() => scriptCrons.value.filter(isCodeCron).length)

const otherCronsCount = computed(() => scriptCrons.value.filter((cron) => !isCodeCron(cron)).length)

const scriptCrons = computed(() => crons.value.filter((cron) => cron.is_system !== 1))

const enabledCrons = computed(() =>
  scriptCrons.value.filter((cron) => cron.is_disabled !== 1 && cron.earliest_minute !== null && !isExcluded(cron)),
)

const disabledCrons = computed(() => scriptCrons.value.filter((cron) => cron.is_disabled === 1))

const visibleCrons = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  return scriptCrons.value
    .filter((cron) => showDisabled.value || cron.is_disabled !== 1)
    .filter((cron) => {
      if (commandTypeFilter.value === 'code') return isCodeCron(cron)
      if (commandTypeFilter.value === 'other') return !isCodeCron(cron)
      return true
    })
    .filter((cron) => {
      if (!text) return true
      return (cron.name || '').toLowerCase().includes(text) || (cron.command || '').toLowerCase().includes(text)
    })
    .map((cron) => {
      const daily = parseDailyMinutes(cron.schedule)
      const dailyTimes = daily.map(formatMinute)
      const displayTimes = dailyTimes.slice(0, 6)
      const hasMoreTimes = dailyTimes.length > 6
      const moreTimesCount = hasMoreTimes ? dailyTimes.length - 6 : 0
      return {
        ...cron,
        dailyMinutes: daily,
        dailyTimes,
        displayTimes,
        hasMoreTimes,
        moreTimesCount,
        sortMinute: daily.length ? daily[0] : 24 * 60 + 1,
      }
    })
    .sort((a, b) => a.sortMinute - b.sortMinute || a.name.localeCompare(b.name, 'zh'))
})

const filteredGroups = computed(() => {
  const groups = []
  let current = null
  for (const cron of visibleCrons.value) {
    const hour = cron.sortMinute >= 24 * 60 ? -1 : Math.floor(cron.sortMinute / 60)
    if (!current || current.hour !== hour) {
      current = { hour, crons: [] }
      groups.push(current)
    }
    current.crons.push(cron)
  }
  return groups
})

const nextSlotInfo = computed(() =>
  getNextCronSlot(scriptCrons.value, {
    commandType: commandTypeFilter.value,
    intervalMinutes: planForm.intervalMinutes,
    isExcluded,
  }),
)

const nextSlotLastName = computed(() => nextSlotInfo.value.lastName)
const nextSlotLastSchedule = computed(() => nextSlotInfo.value.lastSchedule)

const nextSlotSchedule = computed(() => nextSlotInfo.value.schedule)
const nextSlotTime = computed(() => nextSlotInfo.value.time)

async function copyNextSlot() {
  const text = nextSlotSchedule.value
  if (!text) return
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    ElMessage.success(`已复制：${text}`)
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

// 一键整理的目标脚本（受「仅 code 版」开关控制）
const organizeTargetCrons = computed(() =>
  planForm.codeOnly ? enabledCrons.value.filter(isCodeCron) : enabledCrons.value,
)

// Crowding detection: 严格基于当前时间线上「可见列表的相邻位置」计算与上一项的分钟差
const crowdMap = computed(() => {
  const list = visibleCrons.value.filter((cron) => cron.is_disabled !== 1 && !isExcluded(cron))
  const map = new Map()
  const threshold = planForm.intervalMinutes || 2
  for (let index = 0; index < list.length; index += 1) {
    const current = list[index]
    const prev = list[index - 1]
    let prevGap = null
    if (prev && current.sortMinute < 24 * 60 && prev.sortMinute < 24 * 60) {
      const diff = current.sortMinute - prev.sortMinute
      if (diff > 0) prevGap = diff
    }
    map.set(cronKey(current), {
      crowded: prevGap !== null && prevGap < threshold,
      prevGap,
    })
  }
  return map
})

function isCrowded(cron) {
  if (cron.is_disabled === 1 || isExcluded(cron)) return false
  return crowdMap.value.get(cronKey(cron))?.crowded || false
}

// 间隔大于阈值（严格大于 intervalMinutes 分钟）时为「宽松」状态
function isSparse(cron) {
  if (cron.is_disabled === 1 || isExcluded(cron)) return false
  const info = crowdMap.value.get(cronKey(cron))
  if (!info || info.crowded) return false
  const gap = info.prevGap
  if (gap === null || gap === undefined) return false
  return gap > (planForm.intervalMinutes || 2)
}

function minuteGap(cron) {
  if (cron.is_disabled === 1 || isExcluded(cron)) return '-'
  const info = crowdMap.value.get(cronKey(cron))
  if (!info) return '-'
  return info.prevGap === null || info.prevGap === undefined ? '-' : info.prevGap
}

const crowdedCount = computed(() => {
  let count = 0
  for (const item of crowdMap.value.values()) {
    if (item.crowded) count += 1
  }
  return count
})

const editPreviewTimes = computed(() => parseDailyMinutes(editScheduleText.value).map(formatMinute))

async function loadCrons() {
  const request = cronsRequestController.start()
  loading.value = true
  try {
    const { data } = await api.get('/qinglong/crons', { signal: request.signal })
    if (!request.isCurrent()) return
    crons.value = data.items || []
  } catch (error) {
    if (!request.isCurrent() || isRequestCanceled(error)) return
    ElMessage.error(getApiErrorMessage(error, '拉取青龙任务失败'))
  } finally {
    if (request.isCurrent()) {
      loading.value = false
      request.finish()
    }
  }
}

function openEditDialog(cron) {
  editingCron.value = cron
  editScheduleText.value = cron.schedule
  editDialogVisible.value = true
}

async function applyBatch(items, successText) {
  applying.value = true
  try {
    const { data } = await api.post('/qinglong/crons/schedules', { items }, { timeout: 300000 })
    const failed = data.failed || []
    if (failed.length) {
      ElMessage.warning(`成功 ${data.updated} 个，失败 ${failed.length} 个：${failed[0].error}`)
    } else {
      ElMessage.success(successText || `已更新 ${data.updated} 个任务`)
    }
    await loadCrons()
    return failed.length === 0
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '更新失败'))
    return false
  } finally {
    applying.value = false
  }
}

async function applySingleEdit() {
  if (!editingCron.value) return
  const ok = await applyBatch([{ id: editingCron.value.id, schedule: editScheduleText.value.trim() }], '执行时间已更新')
  if (ok) {
    editDialogVisible.value = false
  }
}

function buildPlan() {
  const startMinute = parseTimeToMinute(planForm.startTime)
  const afternoonStartMinute = parseTimeToMinute(planForm.afternoonStartTime)
  if (startMinute === null || afternoonStartMinute === null) {
    ElMessage.error('请选择上午和下午起始时间')
    return
  }
  if (afternoonStartMinute <= startMinute) {
    ElMessage.error('下午起始时间必须晚于上午起始时间')
    return
  }
  const interval = Math.max(1, planForm.intervalMinutes || 2)

  const targets = organizeTargetCrons.value
    .slice()
    .sort((a, b) => a.earliest_minute - b.earliest_minute || a.name.localeCompare(b.name, 'zh'))

  const items = []
  let cursor = startMinute
  let overflow = false
  for (const cron of targets) {
    if (cursor >= 24 * 60) {
      overflow = true
      break
    }
    const morningHour = Math.floor(cursor / 60)
    const morningMinute = cursor % 60
    const afternoonCursor = afternoonStartMinute + (cursor - startMinute)
    const afternoonHour = Math.floor(afternoonCursor / 60)
    if (afternoonHour > 23) {
      overflow = true
      break
    }
    const newSchedule = `${morningMinute} ${morningHour},${afternoonHour} * * *`
    items.push({
      id: cron.id,
      name: cron.name,
      command: cron.command,
      oldTime: formatMinute(cron.earliest_minute),
      oldSchedule: cron.schedule,
      newTime: `${formatMinute(cursor)} / ${formatMinute(afternoonCursor)}`,
      newSchedule,
      changed: newSchedule !== cron.schedule,
      applied: false,
      applying: false,
    })
    cursor += interval
  }
  planOverflow.value = overflow
  if (overflow) {
    ElMessage.error('时间窗容量不足，请调整起始时间或间隔')
    return
  }
  planItems.value = items
  planDialogVisible.value = true
}

async function applySinglePlanItem(row) {
  if (!row || row.applying || row.applied) return
  try {
    await ElMessageBox.confirm(`将把「${row.name}」的执行时间更新为 ${row.newTime}，确认继续？`, '单个应用', {
      type: 'warning',
      confirmButtonText: '应用',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  row.applying = true
  try {
    const { data } = await api.post(
      '/qinglong/crons/schedules',
      {
        items: [{ id: row.id, schedule: row.newSchedule }],
      },
      { timeout: 60000 },
    )
    if (data.failed && data.failed.length) {
      ElMessage.error(`应用失败：${data.failed[0].error}`)
      return
    }
    ElMessage.success(`已更新「${row.name}」`)
    row.applied = true
    row.changed = false
    row.oldSchedule = row.newSchedule
    await loadCrons()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '应用失败'))
  } finally {
    row.applying = false
  }
}

async function applyPlan() {
  const changed = planItems.value.filter((item) => item.changed)
  if (!changed.length) {
    ElMessage.info('所有脚本时间与目标一致，无需修改')
    planDialogVisible.value = false
    return
  }
  try {
    await ElMessageBox.confirm(
      `将把 ${changed.length} 个 code 版脚本的执行时间写入青龙面板，确认继续？`,
      '应用整理结果',
      { type: 'warning', confirmButtonText: '应用', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  const ok = await applyBatch(
    changed.map((item) => ({ id: item.id, schedule: item.newSchedule })),
    `已整理 ${changed.length} 个脚本`,
  )
  if (ok) {
    planDialogVisible.value = false
  }
}

onMounted(() => {
  loadCrons()
})
</script>

<style scoped>
.ql-crons-page {
  gap: 20px;
}

/* 顶部驾驶舱：沿用积分总览的 hero 结构 */
.ql-hero-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.ql-hero-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ql-coverage-value {
  font-size: 24px;
  line-height: 1.35;
  padding-top: 6px;
}

.ql-next-slot-foot {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.ql-next-slot-code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  padding: 4px 8px;
  color: var(--el-text-color-regular);
  word-break: break-all;
}

.ql-next-slot-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 6px;
}

/* 搜索框放进 meta chip 里，保持胶囊形态 */
.ql-meta-search {
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  color: inherit;
  width: 180px;
  font-family: inherit;
}

.ql-meta-search::placeholder {
  color: var(--el-text-color-secondary);
}

/* 脚本类型筛选 */
.ql-filter-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.ql-filter-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  flex: 0 0 auto;
}

.ql-filter-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.ql-filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid rgba(226, 207, 181, 0.95);
  border-radius: 999px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.78);
  color: #7c6143;
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
  transition: all 0.22s ease;
  box-shadow: 0 6px 14px rgba(130, 100, 64, 0.05);
}

.ql-filter-chip:hover {
  transform: translateY(-1px);
  border-color: rgba(226, 175, 102, 0.95);
  background: rgba(255, 249, 241, 0.96);
  color: #9a6224;
  box-shadow: 0 10px 22px rgba(198, 146, 72, 0.14);
}

.ql-filter-chip-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(233, 184, 110, 0.95), rgba(216, 145, 58, 0.95));
  box-shadow: 0 0 0 4px rgba(244, 207, 157, 0.3);
}

.ql-filter-chip.active {
  border-color: transparent;
  background: linear-gradient(135deg, #f1c983, #df9f50);
  color: #fff;
}

.ql-filter-chip.active .ql-filter-chip-dot {
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.25);
}

/* 卡片对齐全站暖色风格 */
.ql-card {
  border-radius: 22px;
  border: 1px solid var(--warm-border);
  background: var(--warm-card);
  box-shadow: var(--warm-shadow);
}

.ql-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.ql-card-title {
  font-size: 15px;
  font-weight: 600;
}

.ql-card-subtitle {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

.ql-hour-group {
  display: flex;
  gap: 16px;
  padding: 10px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.ql-hour-group:last-child {
  border-bottom: none;
}

.ql-hour-label {
  flex: 0 0 56px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  padding-top: 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.ql-hour-rows {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ql-organize-form {
  display: flex;
  align-items: flex-end;
  gap: 20px;
  flex-wrap: wrap;
}

.ql-form-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 6px;
}

.ql-hours-input {
  width: 180px;
}

.ql-form-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ql-form-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.ql-excluded-meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.ql-clear-excluded-btn {
  margin-left: 4px;
  padding: 0 4px;
  height: auto;
  font-size: 12px;
}

.ql-plan-alert {
  margin-top: 16px;
}

@media (max-width: 900px) {
  .ql-hero-head {
    flex-direction: column;
  }

  .ql-hero-actions {
    width: 100%;
  }

  .ql-hero-actions .el-button {
    flex: 1;
  }

  .ql-meta-search {
    flex: 1;
    width: auto;
  }

  /* 筛选行：标签和 chips 垂直排列 */
  .ql-filter-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .ql-filter-chips {
    width: 100%;
  }

  .ql-filter-chip {
    flex: 1;
    min-width: 100px;
    justify-content: center;
    padding: 8px 10px;
    font-size: 12px;
  }

  /* 小时分组：标签和行垂直排列 */
  .ql-hour-group {
    flex-direction: column;
    gap: 8px;
    padding: 12px 0;
  }

  .ql-hour-label {
    flex: none;
    padding-top: 0;
    padding-bottom: 4px;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }

  /* 一键整理表单：垂直排列 */
  .ql-organize-form {
    flex-direction: column;
    align-items: stretch;
    gap: 14px;
  }

  .ql-form-item {
    width: 100%;
  }

  .ql-form-item :deep(.el-time-picker),
  .ql-form-item :deep(.el-input-number),
  .ql-form-item :deep(.el-input) {
    width: 100%;
  }

  .ql-form-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .ql-form-actions .el-button {
    width: 100%;
    margin-left: 0;
  }

  .ql-form-hint {
    text-align: center;
  }

  /* 指标卡：2 列布局 */
  .points-metrics-grid {
    grid-template-columns: repeat(2, 1fr) !important;
    gap: 10px !important;
  }

  .points-metric-card {
    padding: 12px !important;
  }

  .points-metric-value {
    font-size: 22px !important;
    margin-top: 4px !important;
  }

  .points-metric-icon {
    width: 40px !important;
    height: 40px !important;
    font-size: 18px !important;
    flex-basis: 40px !important;
  }

  .points-metric-foot {
    font-size: 11px !important;
    margin-top: 8px !important;
  }

  /* 顶部 hero meta chips 可换行 */
  .points-hero-meta {
    flex-wrap: wrap;
  }

  .points-meta-chip {
    flex: 1;
    min-width: 140px;
  }

  .ql-excluded-meta-chip {
    min-width: 160px;
  }
}

@media (max-width: 480px) {
  /* 更小屏幕：进一步压缩 */
  .points-metrics-grid {
    grid-template-columns: 1fr 1fr !important;
  }

  .ql-filter-chip {
    min-width: 80px;
    padding: 6px 8px;
    font-size: 11px;
  }
}
</style>
