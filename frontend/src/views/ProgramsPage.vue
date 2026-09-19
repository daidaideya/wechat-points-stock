<template>
  <div class="page-stack programs-page programs-showcase-page">
    <ProgramFilterBar
      :search-keyword="searchKeyword"
      :status-filter="statusFilter"
      :favorite-filter="favoriteFilter"
      :ql-status-filter="qlStatusFilter"
      :sort-filter="sortFilter"
      :current-tag="currentTag"
      :available-tags="availableTags"
      :active-filter-chips="activeFilterChips"
      :has-active-filters="hasActiveFilters"
      :loaded-count="programs.length"
      @update:search-keyword="searchKeyword = $event"
      @search="applyFilters"
      @reset="resetFilters"
      @status="setStatusFilter"
      @favorite="setFavoriteFilter"
      @ql-status="setQlStatusFilter"
      @sort="setSortFilter"
      @tag="selectTag"
      @clear-chip="clearFilterChip"
    />

    <section v-if="loading && programs.length === 0" class="showcase-grid skeleton-grid compact">
      <el-card
        v-for="item in 6"
        :key="item"
        shadow="hover"
        class="program-card showcase-program-card skeleton-card compact"
      >
        <el-skeleton animated>
          <template #template>
            <el-skeleton-item variant="circle" style="width: 52px; height: 52px; margin-bottom: 18px" />
            <el-skeleton-item variant="h3" style="width: 52%; height: 26px; margin-bottom: 12px" />
            <el-skeleton-item variant="text" style="width: 70%; margin-bottom: 10px" />
            <el-skeleton-item variant="text" style="width: 92%; margin-bottom: 8px" />
            <el-skeleton-item variant="text" style="width: 80%; margin-bottom: 18px" />
            <el-skeleton-item variant="text" style="width: 100%; height: 34px; margin-bottom: 10px" />
            <el-skeleton-item variant="text" style="width: 48%" />
          </template>
        </el-skeleton>
      </el-card>
    </section>

    <section v-else class="showcase-grid compact">
      <div v-if="loadError" class="program-state-card compact full-span">
        <el-result icon="error" title="列表加载失败" sub-title="请检查网络或接口状态后重试。">
          <template #extra>
            <el-button type="primary" @click="applyFilters">重新加载</el-button>
          </template>
        </el-result>
      </div>

      <div v-else-if="!programs.length" class="program-state-card compact full-span">
        <el-empty :description="isAppList ? '没有符合条件的 APP' : '没有符合条件的小程序'">
          <template #description>
            <p>可尝试清空关键词、标签或收藏筛选后重新查看。</p>
          </template>
          <div class="empty-state-actions">
            <el-button type="primary" plain @click="resetFilters">清空筛选</el-button>
          </div>
        </el-empty>
      </div>

      <ProgramCard
        v-for="(program, index) in programs"
        v-else
        :key="program.program_id"
        :program="program"
        :index="index"
        :is-touch-layout="isTouchLayout"
        :updating-program-id="updatingProgramId"
        :archiving-program-id="archivingProgramId"
        :deleting-program-id="deletingProgramId"
        :title-size-class="titleSizeClass"
        :is-updated-today="isUpdatedToday"
        :format-date="formatDate"
        :format-ql-schedule-tooltip="formatQlScheduleTooltip"
        @copy-name="copyProgramName"
        @copy-id="copyProgramId"
        @open-tags="openTagsDialog"
        @open-stock="openStockDialog"
        @open-detail="openDetailDialog"
        @open-note="openNoteDialog"
        @toggle-favorite="toggleFavorite"
        @command="handleProgramCommand"
      />
    </section>

    <div v-if="programs.length && !loadError" ref="loadMoreSentinel" class="infinite-sentinel" aria-hidden="true"></div>

    <div v-if="programs.length && !loadError" class="infinite-status-bar showcase-status-bar">
      <span v-if="loadingMore" class="infinite-status-text">正在加载更多...</span>
      <span v-else-if="!hasMore" class="infinite-status-text done">已加载全部数据</span>
      <span v-else class="infinite-status-text">继续下滑可自动加载更多</span>
    </div>

    <ProgramMaintenanceDialogs
      v-model:note-visible="noteDialogVisible"
      v-model:tags-visible="tagsDialogVisible"
      :viewport-width="viewportWidth"
      :current-program="currentProgram"
      :available-tags="availableTags"
      :saving-note="savingNote"
      :saving-tags="savingTags"
      :normalize-tags="normalizeTags"
      @save-note="saveNote"
      @save-tags="saveTags"
    />

    <ProgramDetailDialog
      v-model="detailDialogVisible"
      :dialog-width="dialogWidth"
      :dialog-top="dialogTop"
      :fullscreen="isCompactDialog"
      :is-app-list="isAppList"
      :loading="detailLoading"
      :detail-data="detailData"
      :format-date="formatDate"
      @open-stock="openStockDialog"
    />

    <ProgramStockDialog
      v-model="stockDialogVisible"
      :dialog-width="dialogWidth"
      :dialog-top="dialogTop"
      :fullscreen="isCompactDialog"
      :loading="stockLoading"
      :stock-data="stockData"
      :change-expanded="stockChangeExpanded"
      :redeemable-product-count="redeemableProductCount"
      :stock-max-user-points="stockMaxUserPoints"
      :stock-max-user-cash="stockMaxUserCash"
      :sorted-stock-products="sortedStockProducts"
      :format-money="formatMoney"
      :format-product-price="formatProductPrice"
      :is-product-redeemable="isProductRedeemable"
      :get-redeem-blocked-label="getRedeemBlockedLabel"
      :format-points-gap="formatPointsGap"
      :stock-row-class-name="stockRowClassName"
      @update:change-expanded="stockChangeExpanded = $event"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'
import ProgramFilterBar from '../components/ProgramFilterBar.vue'
import ProgramDetailDialog from '../components/ProgramDetailDialog.vue'
import ProgramMaintenanceDialogs from '../components/ProgramMaintenanceDialogs.vue'
import ProgramCard from '../components/ProgramCard.vue'
import ProgramStockDialog from '../components/ProgramStockDialog.vue'
import {
  formatMoney,
  formatProductPrice,
  getRedeemBlockedLabel as getProductRedeemBlockedLabel,
  isRedeemable,
} from '../utils/product'
import { useInfiniteScroll } from '../composables/useInfiniteScroll'
import { useAbortableRequest } from '../composables/useAbortableRequest'
import { useProgramFilters } from '../composables/useProgramFilters'
import { usePageStateCache } from '../composables/usePageStateCache'
import { useViewport } from '../composables/useViewport'
import { getApiErrorMessage, isRequestCanceled } from '../utils/apiError'
import { formatApiDate as formatDate } from '../utils/date'

const route = useRoute()
const pageSize = 20
const loadMoreSentinel = ref(null)
const programsPageStateCache = usePageStateCache({ version: 2, ttlMs: 15 * 60 * 1000 })
const { width: viewportWidthRef } = useViewport({ mobileMax: 900 })
const viewportWidth = computed(() => viewportWidthRef.value || 1200)

// Reuse this page for both 小程序列表 (kind=mini) and APP列表 (kind=app).
const listKind = computed(() => (route.meta?.listKind === 'app' ? 'app' : 'mini'))
const isAppList = computed(() => listKind.value === 'app')
const entityLabel = computed(() => (isAppList.value ? 'APP' : '小程序'))
const PROGRAMS_PAGE_STATE_KEY = computed(() => (isAppList.value ? 'apps-page-state' : 'programs-page-state'))

const loading = ref(false)
const loadingMore = ref(false)
const savingNote = ref(false)
const savingTags = ref(false)
const stockLoading = ref(false)
const stockChangeExpanded = ref(false)
const detailDialogVisible = ref(false)
const detailLoading = ref(false)
const detailData = ref(null)
const loadError = ref(false)
const total = ref(0)
const page = ref(1)
const hasMore = ref(false)
const programs = ref([])
const availableTags = ref([])
const {
  currentTag,
  searchKeyword,
  favoriteFilter,
  statusFilter,
  qlStatusFilter,
  sortFilter,
  hasActiveFilters,
  activeFilterChips,
  buildProgramParams,
  setStatusFilter: updateStatusFilter,
  setFavoriteFilter: updateFavoriteFilter,
  setQlStatusFilter: updateQlStatusFilter,
  setSortFilter: updateSortFilter,
  toggleTag,
  clearFilterChip: clearProgramFilterChip,
  resetFilters: resetProgramFilters,
} = useProgramFilters({ listKind, pageSize })
const updatingProgramId = ref('')
const deletingProgramId = ref('')
const archivingProgramId = ref('')
const noteDialogVisible = ref(false)
const tagsDialogVisible = ref(false)
const stockDialogVisible = ref(false)
const currentProgram = ref(null)
const stockData = ref(null)

let restoringState = false
const programsRequest = useAbortableRequest()
const detailRequest = useAbortableRequest()
const stockRequest = useAbortableRequest()

const isTouchLayout = computed(() => viewportWidth.value <= 768)
const isCompactDialog = computed(() => viewportWidth.value <= 640)
const dialogWidth = computed(() => {
  if (viewportWidth.value <= 640) return '100%'
  if (viewportWidth.value <= 900) return '94%'
  return '1040px'
})
const dialogTop = computed(() => (viewportWidth.value <= 900 ? '2vh' : '5vh'))

const stockMaxUserPoints = computed(() => Number(stockData.value?.max_user_points) || 0)
const stockMaxUserCash = computed(() => {
  const value = stockData.value?.max_user_cash
  if (value == null || value === '') return null
  const num = Number(value)
  return Number.isNaN(num) ? null : num
})

function isProductRedeemable(product, maxPoints = stockMaxUserPoints.value, maxCash = stockMaxUserCash.value) {
  return isRedeemable(product, maxPoints, maxCash)
}

function getRedeemBlockedLabel(product, maxPoints = stockMaxUserPoints.value, maxCash = stockMaxUserCash.value) {
  return getProductRedeemBlockedLabel(product, maxPoints, maxCash)
}

const sortedStockProducts = computed(() => {
  const products = Array.isArray(stockData.value?.products) ? [...stockData.value.products] : []
  const maxPoints = stockMaxUserPoints.value
  const maxCash = stockMaxUserCash.value

  return products.sort((a, b) => {
    const aPoints = Number(a?.points) || 0
    const bPoints = Number(b?.points) || 0
    const aCash = Number(a?.cash) || 0
    const bCash = Number(b?.cash) || 0
    const aStock = Number(a?.stock) || 0
    const bStock = Number(b?.stock) || 0
    const aRedeemable = isProductRedeemable(a, maxPoints, maxCash)
    const bRedeemable = isProductRedeemable(b, maxPoints, maxCash)

    // 可兑换优先
    if (aRedeemable !== bRedeemable) return aRedeemable ? -1 : 1
    // 有货优先于无货
    if (aStock > 0 !== bStock > 0) return aStock > 0 ? -1 : 1
    // 可兑换：积分高的更“值钱”靠前；同积分时现金高的靠前
    if (aRedeemable && bRedeemable) {
      if (bPoints !== aPoints) return bPoints - aPoints
      if (bCash !== aCash) return bCash - aCash
    } else {
      const aGap = Math.max(0, aPoints - maxPoints)
      const bGap = Math.max(0, bPoints - maxPoints)
      if (aGap !== bGap) return aGap - bGap
      if (aPoints !== bPoints) return aPoints - bPoints
      const aCashGap = maxCash == null ? aCash : Math.max(0, aCash - maxCash)
      const bCashGap = maxCash == null ? bCash : Math.max(0, bCash - maxCash)
      if (aCashGap !== bCashGap) return aCashGap - bCashGap
    }
    return String(a?.product_name || '').localeCompare(String(b?.product_name || ''), 'zh-CN')
  })
})

const redeemableProductCount = computed(() => {
  return sortedStockProducts.value.filter((item) => isProductRedeemable(item)).length
})

function normalizeTags(input) {
  const source = Array.isArray(input) ? input : String(input || '').split(',')
  const seen = new Set()
  return source
    .map((item) => String(item || '').trim())
    .filter((item) => {
      if (!item || seen.has(item)) return false
      seen.add(item)
      return true
    })
    .slice(0, 20)
}

function mergeTagsByUsage(...tagGroups) {
  const counts = new Map()

  tagGroups.flat().forEach((tag) => {
    const normalized = String(tag || '').trim()
    if (!normalized) return
    counts.set(normalized, (counts.get(normalized) || 0) + 1)
  })

  return Array.from(counts.entries())
    .sort((a, b) => {
      if (b[1] !== a[1]) return b[1] - a[1]
      return a[0].localeCompare(b[0], 'zh-CN')
    })
    .map(([tag]) => tag)
}

function savePageState() {
  const state = {
    searchKeyword: searchKeyword.value,
    favoriteFilter: favoriteFilter.value,
    statusFilter: statusFilter.value,
    qlStatusFilter: qlStatusFilter.value,
    sortFilter: sortFilter.value,
    currentTag: currentTag.value,
    scrollY: window.scrollY || window.pageYOffset || 0,
  }
  programsPageStateCache.save(PROGRAMS_PAGE_STATE_KEY.value, state)
}

function readPageState() {
  return programsPageStateCache.read(PROGRAMS_PAGE_STATE_KEY.value)
}

async function restorePageState() {
  const state = readPageState()
  if (!state) return false

  restoringState = true
  searchKeyword.value = state.searchKeyword || ''
  favoriteFilter.value = state.favoriteFilter || 'all'
  statusFilter.value = state.statusFilter || 'active'
  qlStatusFilter.value = state.qlStatusFilter || 'all'
  sortFilter.value = state.sortFilter || 'default'
  currentTag.value = state.currentTag || ''
  programs.value = []
  availableTags.value = []
  total.value = 0
  page.value = 1
  hasMore.value = false
  await fetchPrograms(1, false)
  await nextTick()
  window.scrollTo({ top: Number(state.scrollY) || 0, behavior: 'auto' })
  restoringState = false
  return true
}

async function openDetailDialog(program) {
  if (!program?.program_id) return
  const request = detailRequest.start()
  detailDialogVisible.value = true
  detailLoading.value = true
  detailData.value = {
    program_id: program.program_id,
    program_name: program.program_name,
    is_favorite: program.is_favorite,
    tags: program.tags || [],
    note: program.note || '',
    last_update_time: program.last_update_time,
    max_user_points: program.max_user_points,
    has_stock: program.has_stock,
    ranking: [],
  }
  try {
    const { data } = await api.get(`/programs/${program.program_id}`, { signal: request.signal })
    if (!request.isCurrent()) return
    detailData.value = {
      ...detailData.value,
      ...data,
      has_stock: data?.has_stock ?? program.has_stock,
    }
  } catch (error) {
    if (!request.isCurrent() || isRequestCanceled(error)) return
    console.error(error)
    ElMessage.error(isAppList.value ? '加载 APP 详情失败' : '加载小程序详情失败')
  } finally {
    if (request.isCurrent()) {
      detailLoading.value = false
      request.finish()
    }
  }
}

function formatQlScheduleTooltip(program) {
  const schedule = program?.ql_schedule || ''
  const name = program?.ql_cron_name
  const statusText =
    program?.ql_status === 'disabled' ? '已禁用' : program?.ql_status === 'enabled' ? '已启用' : '未关联'
  if (name) return `青龙定时（${statusText}）${name}：${schedule}`
  return `青龙定时（${statusText}）：${schedule}`
}

/** Shrink title font by length so long names stay on one line in the grid card. */
function titleSizeClass(name) {
  const len = Array.from(String(name || '')).length
  if (len >= 22) return 'is-title-xs'
  if (len >= 16) return 'is-title-sm'
  if (len >= 12) return 'is-title-md'
  return ''
}

async function copyText(text, successMessage) {
  const value = String(text || '').trim()
  if (!value) {
    ElMessage.warning('没有可复制的内容')
    return
  }

  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(value)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = value
      textarea.setAttribute('readonly', 'readonly')
      textarea.style.position = 'fixed'
      textarea.style.left = '-9999px'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    ElMessage.success(successMessage || `已复制：${value}`)
  } catch (error) {
    console.error(error)
    ElMessage.error('复制失败，请手动选择文本')
  }
}

function copyProgramName(program) {
  const name = program?.program_name || program?.program_id
  return copyText(name, `已复制名称：${name}`)
}

function copyProgramId(program) {
  return copyText(program?.program_id, `已复制 program_id：${program?.program_id}`)
}

function isUpdatedToday(value) {
  if (!value) return false
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return false

  const now = new Date()
  return (
    date.getFullYear() === now.getFullYear() && date.getMonth() === now.getMonth() && date.getDate() === now.getDate()
  )
}

async function fetchPrograms(nextPage = 1, append = false) {
  if (append) {
    if (loadingMore.value || loading.value || !hasMore.value) return
    loadingMore.value = true
  } else {
    loading.value = true
  }

  const request = programsRequest.start()

  try {
    loadError.value = false
    const { data } = await api.get('/programs', {
      params: buildProgramParams(nextPage),
      signal: request.signal,
    })
    if (!request.isCurrent()) return
    total.value = data.total || 0
    hasMore.value = Boolean(data.has_more)
    page.value = data.page || nextPage
    availableTags.value = data.available_tags || []
    const items = Array.isArray(data.items) ? data.items : []
    programs.value = append ? [...programs.value, ...items] : items
    await nextTick()
    initInfiniteScroll()
  } catch (error) {
    if (!request.isCurrent() || isRequestCanceled(error)) return
    console.error(error)
    loadError.value = true
    if (!append) programs.value = []
    ElMessage.error(isAppList.value ? '加载 APP 列表失败' : '加载小程序列表失败')
  } finally {
    if (request.isCurrent()) {
      loading.value = false
      loadingMore.value = false
      request.finish()
    }
  }
}

function applyFilters() {
  page.value = 1
  hasMore.value = false
  destroyInfiniteScroll()
  fetchPrograms(1, false)
}

function resetFilters() {
  resetProgramFilters()
  applyFilters()
}

function setStatusFilter(value) {
  if (statusFilter.value === value) return
  updateStatusFilter(value)
  applyFilters()
}

function setFavoriteFilter(value) {
  if (favoriteFilter.value === value) return
  updateFavoriteFilter(value)
  applyFilters()
}

function setQlStatusFilter(value) {
  if (qlStatusFilter.value === value) return
  updateQlStatusFilter(value)
  applyFilters()
}

function setSortFilter(value) {
  if (sortFilter.value === value) return
  updateSortFilter(value)
  applyFilters()
}

function selectTag(tag) {
  toggleTag(tag)
  applyFilters()
}

function clearFilterChip(key) {
  clearProgramFilterChip(key)
  applyFilters()
}

async function loadMore() {
  if (!hasMore.value || loadingMore.value || loading.value || loadError.value) return
  await fetchPrograms(page.value + 1, true)
}

const { observe: initInfiniteScroll, disconnect: destroyInfiniteScroll } = useInfiniteScroll({
  target: loadMoreSentinel,
  canLoadMore: () => hasMore.value && !loadError.value,
  onLoadMore: loadMore,
  rootMargin: '0px 0px 320px 0px',
})

function openNoteDialog(program) {
  currentProgram.value = program
  noteDialogVisible.value = true
}

async function saveNote(note) {
  if (!currentProgram.value) return
  savingNote.value = true
  try {
    await api.put(`/programs/${currentProgram.value.program_id}`, { note })
    currentProgram.value.note = note
    noteDialogVisible.value = false
    ElMessage.success('备注已保存')
  } catch (error) {
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '保存备注失败'))
  } finally {
    savingNote.value = false
  }
}

function openTagsDialog(program) {
  currentProgram.value = program
  tagsDialogVisible.value = true
}

async function saveTags(tags) {
  if (!currentProgram.value) return
  savingTags.value = true
  try {
    const { data } = await api.put(`/programs/${currentProgram.value.program_id}`, { tags })
    currentProgram.value.tags = data.tags || [...tags]
    tagsDialogVisible.value = false
    availableTags.value = mergeTagsByUsage(
      programs.value.flatMap((item) => normalizeTags(item.tags || [])),
      availableTags.value,
      currentProgram.value.tags,
    )
    ElMessage.success('标签已保存')
  } catch (error) {
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '保存标签失败'))
  } finally {
    savingTags.value = false
  }
}

async function toggleFavorite(program) {
  if (updatingProgramId.value) return
  updatingProgramId.value = program.program_id
  try {
    await api.put(`/programs/${program.program_id}`, { is_favorite: !program.is_favorite })
    program.is_favorite = !program.is_favorite
    ElMessage.success(program.is_favorite ? '已加入收藏' : '已取消收藏')
  } catch (error) {
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '更新收藏状态失败'))
  } finally {
    updatingProgramId.value = ''
  }
}

function formatPointsGap(product) {
  const maxPoints = stockMaxUserPoints.value
  const maxCash = stockMaxUserCash.value
  const needPoints = Number(product?.points) || 0
  const needCash = Number(product?.cash) || 0
  const stock = Number(product?.stock) || 0
  if (stock <= 0) return '无货'
  if (isProductRedeemable(product, maxPoints, maxCash)) return '可兑'

  const parts = []
  if (needPoints > maxPoints) parts.push(`积分差 ${needPoints - maxPoints}`)
  if (needCash > 0) {
    if (maxCash == null) parts.push(`需现金 ¥${formatMoney(needCash)}`)
    else if (needCash > maxCash) parts.push(`现金差 ¥${formatMoney(needCash - maxCash)}`)
  }
  return parts.length ? parts.join(' / ') : '不可兑'
}

function stockRowClassName({ row }) {
  if (isProductRedeemable(row)) return 'stock-row-redeemable'
  if ((Number(row?.stock) || 0) <= 0) return 'stock-row-out'
  return 'stock-row-locked'
}

async function openStockDialog(program) {
  if (!program?.program_id) return
  const request = stockRequest.start()
  stockDialogVisible.value = true
  stockLoading.value = true
  stockData.value = null
  stockChangeExpanded.value = false
  try {
    const { data } = await api.get(`/programs/${program.program_id}/stock`, { signal: request.signal })
    if (!request.isCurrent()) return
    stockData.value = data
  } catch (error) {
    if (!request.isCurrent() || isRequestCanceled(error)) return
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '加载库存详情失败'))
  } finally {
    if (request.isCurrent()) {
      stockLoading.value = false
      request.finish()
    }
  }
}

async function deleteProgram(program) {
  if (deletingProgramId.value) return

  try {
    await ElMessageBox.confirm(
      `确定删除${entityLabel.value}“${program.program_name || program.program_id}”吗？该操作会同时删除相关库存和积分记录。`,
      '删除确认',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      },
    )
  } catch {
    return
  }

  deletingProgramId.value = program.program_id
  try {
    await api.delete(`/programs/${program.program_id}`)
    programs.value = programs.value.filter((item) => item.program_id !== program.program_id)
    total.value = Math.max(0, total.value - 1)
    availableTags.value = mergeTagsByUsage(
      programs.value.flatMap((item) => normalizeTags(item.tags || [])),
      availableTags.value,
    )
    ElMessage.success(isAppList.value ? 'APP 已删除' : '小程序已删除')
  } catch (error) {
    console.error(error)
    ElMessage.error(isAppList.value ? '删除 APP 失败' : '删除小程序失败')
  } finally {
    deletingProgramId.value = ''
  }
}

async function archiveProgram(program) {
  if (archivingProgramId.value) return
  const willArchive = !program.is_archived
  archivingProgramId.value = program.program_id
  try {
    const { data } = await api.put(`/programs/${program.program_id}`, { is_archived: willArchive })
    program.is_archived = Boolean(data?.is_archived ?? willArchive)
    program.archived_at = data?.archived_at ?? (willArchive ? new Date().toISOString() : null)
    if (willArchive) {
      // backend auto-clears favorite when archiving
      program.is_favorite = Boolean(data?.is_favorite ?? false)
    }

    // If current view filters out this program after the change, drop it from the list
    const dropFromList =
      (statusFilter.value === 'active' && willArchive) ||
      (statusFilter.value === 'archived' && !willArchive) ||
      (favoriteFilter.value === 'favorite' && willArchive && !program.is_favorite)

    if (dropFromList) {
      programs.value = programs.value.filter((item) => item.program_id !== program.program_id)
      total.value = Math.max(0, total.value - 1)
    }

    ElMessage.success(willArchive ? '已归档' : '已取消归档')
  } catch (error) {
    console.error(error)
    ElMessage.error(willArchive ? '归档失败' : '取消归档失败')
  } finally {
    archivingProgramId.value = ''
  }
}

function handleProgramCommand(command, program) {
  if (command === 'archive') {
    archiveProgram(program)
  } else if (command === 'delete') {
    deleteProgram(program)
  }
}

watch(
  () => programs.value.length,
  async (value) => {
    if (!value || loadError.value) return
    await nextTick()
    initInfiniteScroll()
  },
)

watch(detailDialogVisible, (visible) => {
  if (!visible) {
    detailRequest.cancel()
    detailLoading.value = false
  }
})

watch(stockDialogVisible, (visible) => {
  if (!visible) {
    stockRequest.cancel()
    stockLoading.value = false
  }
})

// Same component for /programs and /apps — reload when kind switches.
watch(
  () => listKind.value,
  async () => {
    resetProgramFilters()
    programs.value = []
    page.value = 1
    hasMore.value = false
    total.value = 0
    await fetchPrograms(1, false)
  },
)

onMounted(async () => {
  const validStatus = new Set(['active', 'archived', 'all'])
  const queryStatus = typeof route.query.status === 'string' ? route.query.status : ''
  const hasExplicitStatusQuery = validStatus.has(queryStatus)
  const hasSavedState = Boolean(readPageState())
  const shouldRestore =
    !hasExplicitStatusQuery && (route.query.restore === '1' || route.query.fromDetail === '1' || hasSavedState)
  if (shouldRestore && (await restorePageState())) {
    return
  }
  if (hasExplicitStatusQuery) {
    statusFilter.value = queryStatus
  }
  fetchPrograms(1, false)
})

onBeforeUnmount(() => {
  if (!restoringState) savePageState()
})
</script>

<style scoped>
.programs-showcase-page {
  position: relative;
  gap: 22px;
  padding: 6px 2px 18px;
}

.programs-showcase-page::before {
  content: '';
  position: fixed;
  inset: 0 0 0 260px;
  pointer-events: none;
  z-index: -1;
  background:
    linear-gradient(rgba(229, 209, 176, 0.16) 1px, transparent 1px),
    linear-gradient(90deg, rgba(229, 209, 176, 0.16) 1px, transparent 1px),
    linear-gradient(180deg, #fffaf0 0%, #fff7eb 100%);
  background-size:
    24px 24px,
    24px 24px,
    100% 100%;
  background-position:
    0 0,
    0 0,
    0 0;
}

/* Row-first grid so infinite-scroll order stays left→right, top→bottom
   (CSS multi-column fills top→bottom per column and breaks reading order on page 2+). */
.showcase-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 22px;
  align-items: start;
}

.full-span {
  grid-column: 1 / -1;
}

.showcase-card {
  position: relative;
  display: flex;
  width: 100%;
  flex-direction: column;
  min-height: 0;
  margin: 0;
  padding: 22px;
  border-radius: 24px;
  background: #fffdf9;
  border: 1px solid rgba(239, 226, 208, 0.95);
  box-shadow: 0 8px 18px rgba(126, 98, 63, 0.05);
  overflow: hidden;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.masonry-card:nth-child(3n) {
  background: #fffdf9;
}

.masonry-card:nth-child(4n) {
  background: #fffdf9;
}

.showcase-card::before {
  display: none;
}

.showcase-card:hover {
  transform: translateY(-2px);
  border-color: rgba(230, 196, 154, 0.98);
  box-shadow: 0 10px 24px rgba(126, 98, 63, 0.07);
}

.showcase-card.is-favorite {
  border-color: rgba(240, 196, 113, 0.72);
}

.showcase-card.is-archived {
  opacity: 0.62;
  filter: grayscale(0.55);
  background: rgba(248, 244, 235, 0.92);
}

.showcase-card.is-archived:hover {
  opacity: 0.85;
  filter: grayscale(0.2);
}

.archived-badge {
  position: absolute;
  top: 14px;
  right: 14px;
  z-index: 1;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(120, 113, 108, 0.92);
  color: #f5f5f4;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  box-shadow: 0 4px 10px rgba(68, 64, 60, 0.18);
  pointer-events: none;
}

.dropdown-danger-text {
  color: #c2410c;
  font-weight: 600;
}

.showcase-card.has-stock {
  box-shadow: 0 8px 18px rgba(126, 98, 63, 0.05);
}

.showcase-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.showcase-card-brand {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  min-width: 0;
  flex: 1;
}

.no-avatar-brand {
  gap: 0;
}

.full-width-brand-text,
.showcase-card-brand-text {
  min-width: 0;
  width: 100%;
}

.showcase-card-title-line {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 8px;
  min-width: 0;
  width: 100%;
}

.showcase-card-title {
  margin: 0;
  flex: 1 1 auto;
  min-width: 0;
  color: #2f2418;
  font-size: 18px;
  line-height: 1.25;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.showcase-card-title.is-title-md {
  font-size: 16px;
}

.showcase-card-title.is-title-sm {
  font-size: 14px;
}

.showcase-card-title.is-title-xs {
  font-size: 12px;
  letter-spacing: -0.02em;
}

.showcase-card-title.is-copyable,
.showcase-card-id.is-copyable {
  cursor: pointer;
}

.showcase-card-title.is-copyable:hover {
  color: #a16207;
}

.showcase-card-id.is-copyable:hover {
  color: #b7791f;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.showcase-card-title.is-copyable:focus-visible,
.showcase-card-id.is-copyable:focus-visible {
  outline: 2px solid rgba(214, 169, 107, 0.55);
  outline-offset: 2px;
  border-radius: 6px;
}

/* 序号角标：横向排列在标题行最前，便于跟踪浏览进度 */
.showcase-card-index {
  flex: 0 0 auto;
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 24px;
  padding: 0 8px;
  margin-top: 3px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(255, 244, 221, 0.96), rgba(255, 237, 213, 0.9));
  color: #8b5e34;
  font-size: 12px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: 0.02em;
  font-variant-numeric: tabular-nums;
  box-shadow: inset 0 0 0 1px rgba(231, 202, 163, 0.72);
}

.showcase-card-meta-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
  color: #9b7e5c;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.01em;
  min-width: 0;
  width: 100%;
}

.compact-meta-row {
  margin-right: 0;
}

.showcase-card-id {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.showcase-card-tag-row {
  display: flex;
  justify-content: flex-start;
  margin-top: 6px;
  min-width: 0;
  cursor: pointer;
}

.ql-status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  flex: 0 0 auto;
  flex-shrink: 0;
  font-size: 14px;
}

.ql-status-badge.is-enabled {
  color: #15803d;
  background: rgba(220, 252, 231, 0.95);
  box-shadow: inset 0 0 0 1px rgba(34, 197, 94, 0.35);
}

.ql-status-badge.is-disabled {
  color: #b91c1c;
  background: rgba(254, 226, 226, 0.95);
  box-shadow: inset 0 0 0 1px rgba(248, 113, 113, 0.4);
}

.ql-schedule-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  min-width: 0;
  margin-left: 4px;
  padding: 2px 8px 2px 6px;
  border-radius: 999px;
  background: rgba(241, 245, 249, 0.95);
  color: #475569;
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.35);
  cursor: default;
}

.ql-schedule-chip.is-enabled {
  background: rgba(236, 253, 245, 0.95);
  color: #047857;
  box-shadow: inset 0 0 0 1px rgba(52, 211, 153, 0.35);
}

.ql-schedule-chip.is-disabled {
  background: rgba(254, 242, 242, 0.95);
  color: #b91c1c;
  box-shadow: inset 0 0 0 1px rgba(248, 113, 113, 0.35);
}

.ql-schedule-label {
  flex: 0 0 auto;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  opacity: 0.85;
}

.ql-schedule-code {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.2;
  background: transparent;
  color: inherit;
}

.showcase-card-tag-inline {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  flex: 1 1 auto;
  min-width: 0;
  cursor: pointer;
}

.meta-tag-inline {
  margin-left: auto;
  max-width: calc(100% - 118px);
}

.inline-tag-chip {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 2px 8px;
  font-size: 12px;
  line-height: 1.35;
  font-weight: 600;
}

.showcase-card-id {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 0 1 auto;
  min-width: 0;
}

.showcase-card-dot {
  width: 4px;
  height: 4px;
  border-radius: 999px;
  background: rgba(172, 133, 83, 0.45);
}

.stock-dot {
  width: 10px;
  height: 10px;
  flex: 0 0 10px;
  background: #cfd5dd;
  box-shadow: 0 0 0 2px rgba(207, 213, 221, 0.18);
}

.stock-dot.active {
  background: #22c55e;
  box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.16);
}

.showcase-card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
  flex: 0 0 auto;
}

.danger-action-button {
  color: #c2410c;
}

.danger-action-button:hover,
.danger-action-button:focus-visible {
  color: #dc2626;
  background: rgba(254, 226, 226, 0.92);
}

.danger-action-button:disabled {
  color: #caa27a;
  cursor: not-allowed;
}

.clickable-chip-group {
  display: flex;
  width: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.clickable-chip-group:focus-visible {
  outline: 2px solid rgba(214, 169, 107, 0.5);
  outline-offset: 4px;
  border-radius: 16px;
}

.clickable-chip-group:hover .showcase-chip {
  filter: brightness(0.98);
  box-shadow: 0 8px 18px rgba(126, 98, 63, 0.08);
}

.footer-actions {
  padding: 4px;
  border-radius: 14px;
  background: rgba(255, 248, 236, 0.88);
  box-shadow: inset 0 0 0 1px rgba(232, 210, 184, 0.72);
}

.ref-action-group {
  gap: 6px;
}

/* Mobile labeled stock/detail buttons — hidden on desktop */
.mobile-primary-actions {
  display: none;
}

.mobile-text-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 40px;
  min-width: 0;
  padding: 0 14px;
  border: 0;
  border-radius: 12px;
  background: linear-gradient(135deg, #fff8ef, #fff1df);
  color: #8b5e34;
  font-size: 13px;
  font-weight: 700;
  box-shadow: inset 0 0 0 1px rgba(232, 210, 184, 0.85);
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
}

.mobile-text-action :deep(.el-icon) {
  font-size: 16px;
}

.mobile-text-action.detail-action {
  background: linear-gradient(135deg, #f0c37c, #d9a25f);
  color: #fff;
  box-shadow: 0 8px 16px rgba(219, 162, 88, 0.22);
}

.mobile-text-action.is-disabled-action,
.mobile-text-action:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  box-shadow: none;
  background: rgba(245, 240, 232, 0.95);
  color: #b7a28a;
}

.showcase-icon-button {
  width: 36px;
  height: 36px;
  min-width: 36px;
  min-height: 36px;
  border: 0;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: #8a6c4c;
  box-shadow: none;
  cursor: pointer;
  transition:
    color 0.18s ease,
    transform 0.18s ease,
    background 0.18s ease,
    box-shadow 0.18s ease;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
}

.ref-action-button {
  padding: 0;
  background: transparent;
  color: #6f7783;
  box-shadow: none;
}

.icon-plain-button {
  min-width: 36px;
  line-height: 1;
  opacity: 1;
}

.icon-plain-button :deep(.el-icon) {
  font-size: 18px;
}

.ref-action-button:hover {
  color: #4b5563;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 6px 14px rgba(126, 98, 63, 0.08);
  transform: translateY(-1px);
}

.action-tooltip-wrap {
  display: inline-flex;
}

.ref-action-button:disabled,
.ref-action-button.is-disabled-action,
.ref-action-button:disabled:hover,
.ref-action-button.is-disabled-action:hover {
  color: #c4b5a0;
  background: rgba(245, 240, 232, 0.9);
  box-shadow: none;
  transform: none;
  cursor: not-allowed;
  opacity: 0.72;
}

.ref-action-button-favorite.active {
  color: #e5a22d;
  background: rgba(255, 248, 230, 0.98);
  opacity: 1;
}

.ref-action-button-favorite.active:hover {
  color: #d99623;
  background: rgba(255, 244, 214, 0.98);
}

.showcase-button-loading {
  font-size: 12px;
  letter-spacing: 0.2em;
}

.showcase-card-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.compact-card-chips {
  margin-top: 14px;
}

.showcase-chip {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.showcase-chip.muted {
  background: rgba(255, 242, 225, 0.92);
  color: #966537;
}

.showcase-chip.success {
  background: rgba(211, 239, 227, 0.92);
  color: #21684f;
}

.showcase-chip.warning {
  background: rgba(252, 237, 214, 0.92);
  color: #a16207;
}

.showcase-card-note {
  margin: 12px 0 0;
  color: #6f5a44;
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  overflow: hidden;
  max-height: calc(1.8em * 6);
}

.masonry-note.empty {
  min-height: 56px;
}

.showcase-card-note.empty {
  color: #a0896e;
}

.showcase-endpoint-block {
  margin-top: 16px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: inset 0 0 0 1px rgba(236, 221, 199, 0.92);
}

.compact-endpoint-block {
  padding: 12px 14px;
}

.showcase-block-label {
  color: #b08a5b;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.showcase-endpoint-value {
  margin-top: 8px;
  color: #3e2f22;
  font-size: 14px;
  font-weight: 600;
  word-break: break-all;
}

.showcase-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.compact-tag-row {
  gap: 7px;
}

.showcase-tag {
  display: inline-flex;
  align-items: center;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(255, 249, 239, 0.94);
  color: #7a6143;
  font-size: 12px;
  font-weight: 600;
  box-shadow: inset 0 0 0 1px rgba(233, 215, 191, 0.92);
}

.showcase-tag.empty {
  color: #a0896e;
}

.showcase-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid rgba(236, 220, 196, 0.75);
}

.compact-footer {
  align-items: center;
  flex-wrap: wrap;
}

.showcase-footer-meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex-wrap: nowrap;
  white-space: nowrap;
  color: #8e7454;
  font-size: 12px;
}

.showcase-footer-time {
  white-space: nowrap;
}

.showcase-footer-icon {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 243, 225, 0.92);
  color: #a16207;
  font-size: 12px;
}

.showcase-footer-actions {
  display: flex;
  align-items: center;
}

.compact-footer-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.showcase-mini-action {
  border: 0;
  height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 249, 240, 0.98);
  color: #7b5d3d;
  font-size: 12px;
  font-weight: 700;
  box-shadow: inset 0 0 0 1px rgba(232, 211, 183, 0.96);
  cursor: pointer;
  transition: all 0.2s ease;
}

.showcase-mini-action:hover {
  transform: translateY(-1px);
  background: #fff3df;
}

.stock-mini-action.active {
  background: linear-gradient(135deg, #def7e7, #c3f0d1);
  color: #166534;
  box-shadow: inset 0 0 0 1px rgba(134, 239, 172, 0.9);
}

.tag-mini-action:hover {
  color: #7c3aed;
  box-shadow: inset 0 0 0 1px rgba(196, 181, 253, 0.92);
}

.favorite-mini-action.active {
  background: linear-gradient(135deg, #f7d88f, #f0bc65);
  color: #6b430d;
  box-shadow: inset 0 0 0 1px rgba(239, 186, 89, 0.94);
}

.showcase-action-pill {
  border: 0;
  padding: 10px 16px;
  border-radius: 999px;
  background: linear-gradient(135deg, #f4d39e, #ebb96f);
  color: #5d3a11;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 12px 24px rgba(233, 183, 99, 0.22);
}

.showcase-action-pill.muted {
  background: #fff6ea;
  color: #8a6c4c;
  box-shadow: inset 0 0 0 1px rgba(230, 204, 167, 0.92);
}

.showcase-status-bar {
  padding-bottom: 10px;
}

@media (max-width: 1280px) {
  .showcase-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1024px) {
  .programs-showcase-page::before {
    inset: 0;
  }

  .showcase-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .showcase-card {
    border-radius: 22px;
  }

  .showcase-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .showcase-card-top,
  .showcase-card-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .showcase-card-footer.compact-footer {
    gap: 10px;
  }

  .showcase-footer-meta {
    width: 100%;
  }

  /* Primary labeled actions for stock / detail */
  .mobile-primary-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    width: 100%;
  }

  .mobile-text-action {
    width: 100%;
    min-height: 44px; /* comfortable touch target */
  }

  .showcase-card-actions {
    justify-content: space-between;
    flex-wrap: nowrap;
    width: 100%;
  }

  .ref-action-group {
    gap: 4px;
    width: 100%;
    justify-content: space-between;
  }

  .desktop-only-action {
    display: none !important;
  }

  .showcase-icon-button,
  .icon-plain-button {
    width: 44px;
    height: 44px;
    min-width: 44px;
    min-height: 44px;
    border-radius: 14px;
  }

  .icon-plain-button :deep(.el-icon) {
    font-size: 20px;
  }

  .compact-footer,
  .compact-footer-actions {
    align-items: stretch;
    justify-content: flex-start;
  }

  .footer-actions {
    justify-content: space-between;
    width: 100%;
    padding: 6px;
  }
}

@media (max-width: 480px) {
  .mobile-primary-actions {
    grid-template-columns: 1fr 1fr;
  }

  .showcase-footer-time {
    font-size: 11px;
  }

  .ref-action-group {
    gap: 2px;
  }
}
</style>
