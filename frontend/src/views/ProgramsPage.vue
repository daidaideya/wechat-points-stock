<template>
  <div class="page-stack programs-page programs-showcase-page">
    <section class="toolbar-card programs-toolbar-card showcase-toolbar-card">
      <div class="programs-toolbar-head showcase compact">
        <div>
          <h3 class="section-title compact">检索与筛选</h3>
          <p class="section-description compact">支持名称、program_id、拼音、收藏状态与标签组合过滤。</p>
        </div>
        <div class="toolbar-status-chip compact warm-chip">
          <span class="toolbar-status-value">{{ programs.length }}</span>
          <span class="toolbar-status-label">本页展示</span>
        </div>
      </div>

      <div class="toolbar-row programs-toolbar-row showcase compact">
        <el-input
          v-model="searchKeyword"
          clearable
          size="large"
          class="showcase-search-input"
          placeholder="搜索小程序名称 / program_id / 拼音"
          @keyup.enter="applyFilters"
          @clear="applyFilters"
        >
          <template #append>
            <el-button @click="applyFilters">搜索</el-button>
          </template>
        </el-input>

        <el-select v-model="favoriteFilter" size="large" class="toolbar-select showcase-select" @change="applyFilters">
          <el-option label="全部" value="all" />
          <el-option label="仅收藏" value="favorite" />
          <el-option label="仅未收藏" value="unfavorite" />
        </el-select>

        <el-select v-model="statusFilter" size="large" class="toolbar-select showcase-select" @change="applyFilters">
          <el-option label="活跃（默认）" value="active" />
          <el-option label="仅归档" value="archived" />
          <el-option label="全部状态" value="all" />
        </el-select>

        <el-button size="large" class="showcase-reset-button" plain :disabled="!hasActiveFilters" @click="resetFilters">重置</el-button>
      </div>

      <div class="tag-toolbar programs-tag-toolbar showcase compact">
        <div class="tag-toolbar-top compact">
          <span class="tag-toolbar-label">标签筛选</span>
          <span class="tag-toolbar-tip">点击切换，重复点击取消</span>
        </div>
        <div class="tag-list content filter-tag-list showcase compact">
          <button
            type="button"
            class="filter-chip"
            :class="{ active: currentTag === '' }"
            @click="selectTag('')"
          >
            全部
          </button>
          <button
            v-for="tag in availableTags"
            :key="tag"
            type="button"
            class="filter-chip"
            :class="{ active: currentTag === tag }"
            @click="selectTag(tag)"
          >
            {{ tag }}
          </button>
          <span v-if="!availableTags.length" class="empty-text">暂无可筛选标签</span>
        </div>
      </div>
    </section>

    <section v-if="loading && programs.length === 0" class="showcase-grid skeleton-grid compact">
      <el-card v-for="item in 6" :key="item" shadow="hover" class="program-card showcase-program-card skeleton-card compact">
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
        <el-empty description="没有符合条件的小程序">
          <template #description>
            <p>可尝试清空关键词、标签或收藏筛选后重新查看。</p>
          </template>
          <div class="empty-state-actions">
            <el-button type="primary" plain @click="resetFilters">清空筛选</el-button>
          </div>
        </el-empty>
      </div>

      <article
        v-for="program in programs"
        v-else
        :key="program.program_id"
        class="showcase-card masonry-card"
        :class="{
          'is-favorite': program.is_favorite,
          'has-stock': program.has_stock,
          'is-archived': program.is_archived,
        }"
      >
        <div v-if="program.is_archived" class="archived-badge">已归档</div>
        <div class="showcase-card-top">
          <div class="showcase-card-brand no-avatar-brand">
            <div class="showcase-card-brand-text full-width-brand-text">
              <div class="showcase-card-title-line">
                <h3 class="showcase-card-title">{{ program.program_name || program.program_id }}</h3>
              </div>
              <div class="showcase-card-meta-row compact-meta-row">
                <span class="showcase-card-dot stock-dot" :class="{ active: isUpdatedToday(program.last_update_time) }"></span>
                <span class="showcase-card-id">{{ program.program_id }}</span>
              </div>
            </div>
          </div>

          <div class="showcase-card-actions floating-actions ref-action-group">
            <el-tooltip content="编辑备注" placement="top">
              <button type="button" class="showcase-icon-button ref-action-button icon-plain-button" @click="openNoteDialog(program)">
                <el-icon><EditPen /></el-icon>
              </button>
            </el-tooltip>

            <el-tooltip :content="program.has_stock ? '查看库存' : '查看详情'" placement="top">
              <button
                type="button"
                class="showcase-icon-button ref-action-button icon-plain-button"
                @click="program.has_stock ? openStockDialog(program) : goToProgramDetail(program)"
              >
                <el-icon><Box /></el-icon>
              </button>
            </el-tooltip>

            <el-tooltip :content="program.is_favorite ? '取消收藏' : '加入收藏'" placement="top">
              <button
                type="button"
                class="showcase-icon-button ref-action-button favorite-toggle ref-action-button-favorite icon-plain-button"
                :class="{ active: program.is_favorite }"
                @click="toggleFavorite(program)"
              >
                <el-icon v-if="updatingProgramId !== program.program_id"><Star /></el-icon>
                <span v-else class="showcase-button-loading">...</span>
              </button>
            </el-tooltip>

            <el-tooltip :content="(program.tags || []).length ? '编辑标签' : '添加标签'" placement="top">
              <button type="button" class="showcase-icon-button ref-action-button icon-plain-button" @click="openTagsDialog(program)">
                <el-icon><CollectionTag /></el-icon>
              </button>
            </el-tooltip>

            <el-tooltip content="查看详情" placement="top">
              <button type="button" class="showcase-icon-button ref-action-button icon-plain-button" @click="goToProgramDetail(program)">
                <el-icon><ArrowRight /></el-icon>
              </button>
            </el-tooltip>

            <el-dropdown trigger="click" placement="bottom-end" @command="(cmd) => handleProgramCommand(cmd, program)">
              <button
                type="button"
                title="更多操作"
                class="showcase-icon-button ref-action-button icon-plain-button"
                :disabled="archivingProgramId === program.program_id || deletingProgramId === program.program_id"
                @click.stop
              >
                <el-icon v-if="archivingProgramId !== program.program_id && deletingProgramId !== program.program_id"><MoreFilled /></el-icon>
                <span v-else class="showcase-button-loading">...</span>
              </button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="archive">
                    <el-icon><Box /></el-icon>
                    <span>{{ program.is_archived ? '取消归档' : '归档' }}</span>
                  </el-dropdown-item>
                  <el-dropdown-item command="delete" divided>
                    <el-icon><Delete /></el-icon>
                    <span class="dropdown-danger-text">删除</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>

        <div
          class="showcase-card-chips compact-card-chips clickable-chip-group"
          role="button"
          tabindex="0"
          @click.stop="openTagsDialog(program)"
          @keydown.enter.prevent="openTagsDialog(program)"
          @keydown.space.prevent="openTagsDialog(program)"
        >
          <span v-if="(program.tags || []).length" class="showcase-chip success">
            标签：{{ (program.tags || []).join(' / ') }}
          </span>
          <span v-else class="showcase-chip warning">标签：未设置标签</span>
        </div>

        <p class="showcase-card-note masonry-note" :class="{ empty: !program.note }">
          {{ program.note || '暂无备注' }}
        </p>

        <div class="showcase-card-footer compact-footer">
          <div class="showcase-footer-meta">
            <span class="showcase-footer-icon">◔</span>
            <span class="showcase-footer-time">{{ formatDate(program.last_update_time) }}</span>
          </div>
        </div>
      </article>
    </section>

    <div v-if="programs.length && !loadError" ref="loadMoreSentinel" class="infinite-sentinel" aria-hidden="true"></div>

    <div v-if="programs.length && !loadError" class="infinite-status-bar showcase-status-bar">
      <span v-if="loadingMore" class="infinite-status-text">正在加载更多...</span>
      <span v-else-if="!hasMore" class="infinite-status-text done">已加载全部数据</span>
      <span v-else class="infinite-status-text">继续下滑可自动加载更多</span>
    </div>

    <el-dialog v-model="noteDialogVisible" title="编辑备注" width="560px" class="showcase-dialog">
      <div class="showcase-dialog-body">
        <div class="showcase-dialog-intro">
          <div>
            <div class="showcase-dialog-title">维护小程序备注</div>
            <div class="showcase-dialog-subtitle">为当前小程序补充说明，便于后续识别、分类和管理。</div>
          </div>
          <div class="showcase-dialog-badge">{{ currentProgram?.program_name || currentProgram?.program_id || '当前小程序' }}</div>
        </div>

        <div class="dialog-panel">
          <div class="block-label">备注内容</div>
          <el-input
            v-model="editingNote"
            class="showcase-dialog-textarea"
            type="textarea"
            :rows="6"
            maxlength="200"
            show-word-limit
            placeholder="请输入备注"
          />
        </div>
      </div>

      <template #footer>
        <el-button @click="noteDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveNote" :loading="savingNote">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="tagsDialogVisible" title="编辑标签" width="620px" class="showcase-dialog showcase-tags-dialog">
      <div class="tags-dialog-body">
        <div class="tags-dialog-intro">
          <div>
            <div class="tags-dialog-title">维护当前小程序标签</div>
            <div class="tags-dialog-subtitle">点击下方标签即可快速添加或移除，支持自定义标签。</div>
          </div>
          <div class="tags-dialog-counter">已选 {{ editingTags.length }} 个</div>
        </div>

        <div class="dialog-section dialog-panel">
          <div class="block-label">快捷标签</div>
          <div class="tag-list content tags-dialog-list">
            <button
              v-for="tag in quickTags"
              :key="tag"
              type="button"
              class="dialog-tag-chip"
              :class="{ active: editingTags.includes(tag) }"
              @click="toggleEditingTag(tag)"
            >
              {{ tag }}
            </button>
            <button type="button" class="dialog-tag-chip add-chip" @click="promptCustomTag">+ 自定义</button>
          </div>
        </div>

        <div class="dialog-section dialog-panel">
          <div class="block-label">已选标签</div>
          <div class="tag-list content tags-dialog-list selected-tags-list">
            <el-tag
              v-for="tag in editingTags"
              :key="tag"
              class="selected-dialog-tag"
              closable
              @close="removeEditingTag(tag)"
            >
              {{ tag }}
            </el-tag>
            <div v-if="!editingTags.length" class="tags-empty-state">暂无标签，可从上方快捷标签或自定义输入中添加</div>
          </div>
        </div>

        <div class="dialog-section dialog-panel compact-tip-panel">
          <div class="block-label">自定义标签</div>
          <el-input
            v-model="customTagInput"
            class="tags-custom-input"
            maxlength="20"
            placeholder="输入自定义标签后点击添加"
            @keyup.enter="addCustomTagFromInput"
          >
            <template #append>
              <el-button class="tags-add-button" @click="addCustomTagFromInput">添加</el-button>
            </template>
          </el-input>
          <div class="tags-dialog-tip">支持增删改：点击快捷标签切换，点击已选标签右侧关闭按钮删除。</div>
        </div>
      </div>

      <template #footer>
        <el-button @click="tagsDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTags" :loading="savingTags">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="stockDialogVisible" :title="stockDialogTitle" width="1040px" top="5vh" class="showcase-dialog showcase-stock-dialog">
      <div class="showcase-dialog-body stock-dialog-body">
        <div class="showcase-dialog-intro">
          <div>
            <div class="showcase-dialog-title">库存详情总览</div>
            <div class="showcase-dialog-subtitle">查看当前小程序商品库存、所需积分和最高用户积分。</div>
          </div>
          <div class="showcase-dialog-badge stock-badge">最高积分 {{ stockData?.max_user_points ?? 0 }}</div>
        </div>

        <div v-if="stockLoading" class="stock-loading dialog-panel">
          <el-skeleton :rows="6" animated />
        </div>
        <template v-else>
          <div class="stock-summary-card dialog-panel">
            <div class="stock-summary-label">当前最高用户积分</div>
            <div class="stock-summary-value">{{ stockData?.max_user_points ?? 0 }}</div>
          </div>

          <div class="dialog-panel stock-table-panel">
            <el-table :data="stockData?.products || []" stripe class="showcase-dialog-table">
              <el-table-column label="图片" width="96">
                <template #default="scope">
                  <el-image
                    v-if="scope.row.image_url"
                    :src="scope.row.image_url"
                    fit="cover"
                    class="product-thumb"
                    :preview-src-list="[scope.row.image_url]"
                    preview-teleported
                  />
                  <span v-else class="empty-text">无图</span>
                </template>
              </el-table-column>
              <el-table-column prop="product_name" label="商品名称" min-width="320" />
              <el-table-column prop="points" label="所需积分" width="120" />
              <el-table-column prop="stock" label="库存" width="100">
                <template #default="scope">
                  <el-tag :type="scope.row.stock > 0 ? 'success' : 'danger'">{{ scope.row.stock }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ArrowRight, Box, Delete, EditPen, CollectionTag, MoreFilled, Star } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const route = useRoute()
const pageSize = 21
const loadMoreSentinel = ref(null)
const PROGRAMS_PAGE_STATE_KEY = 'programs-page-state'

const loading = ref(false)
const loadingMore = ref(false)
const savingNote = ref(false)
const savingTags = ref(false)
const stockLoading = ref(false)
const loadError = ref(false)
const total = ref(0)
const page = ref(1)
const hasMore = ref(false)
const programs = ref([])
const availableTags = ref([])
const currentTag = ref('')
const searchKeyword = ref('')
const favoriteFilter = ref('all')
const statusFilter = ref('active')
const updatingProgramId = ref('')
const deletingProgramId = ref('')
const archivingProgramId = ref('')
const noteDialogVisible = ref(false)
const tagsDialogVisible = ref(false)
const stockDialogVisible = ref(false)
const currentProgram = ref(null)
const editingNote = ref('')
const editingTags = ref([])
const customTagInput = ref('')
const stockData = ref(null)

let observer = null
let restoringState = false

const stockDialogTitle = computed(() => {
  if (!stockData.value?.program_name) return '库存详情'
  return `${stockData.value.program_name} - 库存详情`
})

const quickTags = computed(() => {
  const knownSet = new Set(availableTags.value)
  return [...availableTags.value, ...editingTags.value.filter((tag) => !knownSet.has(tag))]
})

const hasActiveFilters = computed(() => {
  return Boolean(searchKeyword.value.trim()) || favoriteFilter.value !== 'all' || Boolean(currentTag.value) || statusFilter.value !== 'active'
})

function normalizeTags(input) {
  const source = Array.isArray(input) ? input : String(input || '').split(',')
  const seen = new Set()
  return source.map((item) => String(item || '').trim()).filter((item) => {
    if (!item || seen.has(item)) return false
    seen.add(item)
    return true
  }).slice(0, 20)
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
    currentTag: currentTag.value,
    programs: programs.value,
    availableTags: availableTags.value,
    total: total.value,
    page: page.value,
    hasMore: hasMore.value,
    scrollY: window.scrollY || window.pageYOffset || 0,
  }
  sessionStorage.setItem(PROGRAMS_PAGE_STATE_KEY, JSON.stringify(state))
}

function readPageState() {
  try {
    const raw = sessionStorage.getItem(PROGRAMS_PAGE_STATE_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

async function restorePageState() {
  const state = readPageState()
  if (!state) return false

  restoringState = true
  searchKeyword.value = state.searchKeyword || ''
  favoriteFilter.value = state.favoriteFilter || 'all'
  statusFilter.value = state.statusFilter || 'active'
  currentTag.value = state.currentTag || ''
  programs.value = Array.isArray(state.programs) ? state.programs : []
  availableTags.value = Array.isArray(state.availableTags) ? state.availableTags : []
  total.value = Number(state.total) || 0
  page.value = Number(state.page) || 1
  hasMore.value = Boolean(state.hasMore)
  loadError.value = false
  loading.value = false
  loadingMore.value = false
  await nextTick()
  initInfiniteScroll()
  window.scrollTo({ top: Number(state.scrollY) || 0, behavior: 'auto' })
  restoringState = false
  return true
}

function goToProgramDetail(program) {
  savePageState()
  router.push(`/programs/${program.program_id}`)
}

function formatDate(value) {
  if (!value) return '暂无数据'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

function isUpdatedToday(value) {
  if (!value) return false
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return false

  const now = new Date()
  return date.getFullYear() === now.getFullYear()
    && date.getMonth() === now.getMonth()
    && date.getDate() === now.getDate()
}

function getRequestParams(nextPage = 1) {
  const params = { page: nextPage, size: pageSize }
  const keyword = searchKeyword.value.trim()
  if (keyword) params.q = keyword
  if (favoriteFilter.value === 'favorite') params.is_favorite = true
  else if (favoriteFilter.value === 'unfavorite') params.is_favorite = false
  if (currentTag.value) params.tag = currentTag.value
  if (statusFilter.value && statusFilter.value !== 'active') params.status = statusFilter.value
  else params.status = 'active'
  return params
}

async function fetchPrograms(nextPage = 1, append = false) {
  if (append) {
    if (loadingMore.value || loading.value || !hasMore.value) return
    loadingMore.value = true
  } else {
    loading.value = true
  }

  try {
    loadError.value = false
    const { data } = await api.get('/programs', { params: getRequestParams(nextPage) })
    total.value = data.total || 0
    hasMore.value = Boolean(data.has_more)
    page.value = data.page || nextPage
    availableTags.value = data.available_tags || []
    const items = Array.isArray(data.items) ? data.items : []
    programs.value = append ? [...programs.value, ...items] : items
    await nextTick()
    initInfiniteScroll()
  } catch (error) {
    console.error(error)
    loadError.value = true
    if (!append) programs.value = []
    ElMessage.error('加载小程序列表失败')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function applyFilters() {
  page.value = 1
  hasMore.value = false
  destroyInfiniteScroll()
  fetchPrograms(1, false)
}

function resetFilters() {
  searchKeyword.value = ''
  favoriteFilter.value = 'all'
  currentTag.value = ''
  statusFilter.value = 'active'
  applyFilters()
}

function selectTag(tag) {
  currentTag.value = currentTag.value === tag ? '' : tag
  applyFilters()
}

async function loadMore() {
  if (!hasMore.value || loadingMore.value || loading.value || loadError.value) return
  await fetchPrograms(page.value + 1, true)
}

function initInfiniteScroll() {
  destroyInfiniteScroll()
  if (!loadMoreSentinel.value) return

  observer = new IntersectionObserver(
    (entries) => {
      const [entry] = entries
      if (!entry?.isIntersecting) return
      loadMore()
    },
    {
      root: null,
      rootMargin: '0px 0px 320px 0px',
      threshold: 0,
    },
  )

  observer.observe(loadMoreSentinel.value)
}

function destroyInfiniteScroll() {
  if (observer) {
    observer.disconnect()
    observer = null
  }
}

function openNoteDialog(program) {
  currentProgram.value = program
  editingNote.value = program.note || ''
  noteDialogVisible.value = true
}

async function saveNote() {
  if (!currentProgram.value) return
  savingNote.value = true
  try {
    await api.put(`/programs/${currentProgram.value.program_id}`, { note: editingNote.value })
    currentProgram.value.note = editingNote.value
    noteDialogVisible.value = false
    ElMessage.success('备注已保存')
  } catch (error) {
    console.error(error)
    ElMessage.error('保存备注失败')
  } finally {
    savingNote.value = false
  }
}

function openTagsDialog(program) {
  currentProgram.value = program
  editingTags.value = normalizeTags(program.tags || [])
  customTagInput.value = ''
  tagsDialogVisible.value = true
}

function appendTag(tag) {
  editingTags.value = normalizeTags([...editingTags.value, tag])
}

function toggleEditingTag(tag) {
  if (editingTags.value.includes(tag)) {
    removeEditingTag(tag)
    return
  }
  appendTag(tag)
}

async function promptCustomTag() {
  try {
    const { value } = await ElMessageBox.prompt('请输入自定义标签', '新增标签', {
      confirmButtonText: '添加',
      cancelButtonText: '取消',
      inputPattern: /\S+/,
      inputErrorMessage: '标签不能为空',
    })
    const normalized = String(value || '').trim().slice(0, 20)
    if (normalized) appendTag(normalized)
  } catch {
    // ignore
  }
}

function addCustomTagFromInput() {
  const normalized = String(customTagInput.value || '').trim().slice(0, 20)
  if (!normalized) return
  appendTag(normalized)
  customTagInput.value = ''
}

function removeEditingTag(tag) {
  editingTags.value = editingTags.value.filter((item) => item !== tag)
}

async function saveTags() {
  if (!currentProgram.value) return
  savingTags.value = true
  try {
    const { data } = await api.put(`/programs/${currentProgram.value.program_id}`, { tags: editingTags.value })
    currentProgram.value.tags = data.tags || [...editingTags.value]
    tagsDialogVisible.value = false
    availableTags.value = mergeTagsByUsage(
      programs.value.flatMap((item) => normalizeTags(item.tags || [])),
      availableTags.value,
      currentProgram.value.tags,
    )
    ElMessage.success('标签已保存')
  } catch (error) {
    console.error(error)
    ElMessage.error('保存标签失败')
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
    ElMessage.error('更新收藏状态失败')
  } finally {
    updatingProgramId.value = ''
  }
}

async function openStockDialog(program) {
  stockDialogVisible.value = true
  stockLoading.value = true
  stockData.value = null
  try {
    const { data } = await api.get(`/programs/${program.program_id}/stock`)
    stockData.value = data
  } catch (error) {
    console.error(error)
    ElMessage.error('加载库存详情失败')
  } finally {
    stockLoading.value = false
  }
}

async function deleteProgram(program) {
  if (deletingProgramId.value) return

  try {
    await ElMessageBox.confirm(
      `确定删除小程序“${program.program_name || program.program_id}”吗？该操作会同时删除相关库存和积分记录。`,
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
    ElMessage.success('小程序已删除')
  } catch (error) {
    console.error(error)
    ElMessage.error('删除小程序失败')
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

watch(() => programs.value.length, async (value) => {
  if (!value || loadError.value) return
  await nextTick()
  initInfiniteScroll()
})

onMounted(async () => {
  const validStatus = new Set(['active', 'archived', 'all'])
  const queryStatus = typeof route.query.status === 'string' ? route.query.status : ''
  const hasExplicitStatusQuery = validStatus.has(queryStatus)
  const hasSavedState = Boolean(readPageState())
  const shouldRestore = !hasExplicitStatusQuery && (route.query.restore === '1' || route.query.fromDetail === '1' || hasSavedState)
  if (shouldRestore && await restorePageState()) {
    return
  }
  if (hasExplicitStatusQuery) {
    statusFilter.value = queryStatus
  }
  fetchPrograms(1, false)
})

onBeforeUnmount(() => {
  destroyInfiniteScroll()
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
  background-size: 24px 24px, 24px 24px, 100% 100%;
  background-position: 0 0, 0 0, 0 0;
}

.showcase-toolbar-card {
  border-radius: 26px;
  border: 1px solid rgba(235, 220, 194, 0.88);
  background: rgba(255, 252, 247, 0.9);
  box-shadow: 0 10px 24px rgba(126, 98, 63, 0.04);
  backdrop-filter: blur(2px);
}

.programs-toolbar-head.showcase,
.programs-toolbar-row.showcase,
.programs-tag-toolbar.showcase {
  position: relative;
  z-index: 1;
}

.warm-chip {
  background: linear-gradient(135deg, rgba(255, 244, 221, 0.96), rgba(255, 237, 213, 0.9));
  color: #8b5e34;
}

.showcase-search-input :deep(.el-input__wrapper),
.showcase-search-input :deep(.el-input-group__append),
.showcase-select :deep(.el-select__wrapper) {
  background: #fffaf3;
  box-shadow: 0 0 0 1px rgba(232, 210, 184, 0.78) inset;
}

.showcase-search-input :deep(.el-input__wrapper.is-focus),
.showcase-select :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 1px #d6a96b inset;
}

.showcase-reset-button {
  border-color: rgba(219, 183, 141, 0.74);
  color: #8b5e34;
  background: #fff9f2;
}

.filter-tag-list.showcase {
  gap: 10px;
}

.filter-chip {
  border: 0;
  padding: 10px 16px;
  border-radius: 999px;
  background: #fff8ef;
  color: #8a6c4c;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: inset 0 0 0 1px rgba(231, 208, 176, 0.86);
  transition: all 0.2s ease;
}

.filter-chip:hover {
  transform: translateY(-1px);
  background: #fff3de;
}

.filter-chip.active {
  background: linear-gradient(135deg, #f5d8a8, #efc381);
  color: #5b3b14;
  box-shadow: 0 12px 24px rgba(225, 172, 88, 0.2);
}

.showcase-grid {
  column-count: 4;
  column-gap: 22px;
}

.full-span {
  column-span: all;
}

.showcase-card {
  position: relative;
  display: inline-flex;
  width: 100%;
  break-inside: avoid;
  -webkit-column-break-inside: avoid;
  flex-direction: column;
  min-height: 0;
  margin: 0 0 22px;
  padding: 22px;
  border-radius: 24px;
  background: #fffdf9;
  border: 1px solid rgba(239, 226, 208, 0.95);
  box-shadow: 0 8px 18px rgba(126, 98, 63, 0.05);
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
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
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 8px;
}

.showcase-card-title {
  margin: 0;
  color: #2f2418;
  font-size: 20px;
  line-height: 1.3;
  font-weight: 700;
  word-break: break-word;
}

.showcase-card-meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  color: #9b7e5c;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.compact-meta-row {
  margin-right: 10px;
}

.showcase-card-id {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  flex-wrap: nowrap;
  justify-content: flex-end;
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

.showcase-dialog-body,
.tags-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.showcase-dialog-intro,
.tags-dialog-intro {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 2px 2px 6px;
}

.showcase-dialog-title,
.tags-dialog-title {
  color: #3a2a1d;
  font-size: 16px;
  font-weight: 700;
}

.showcase-dialog-subtitle,
.tags-dialog-subtitle {
  margin-top: 6px;
  color: #9b7e5c;
  font-size: 13px;
  line-height: 1.6;
}

.showcase-dialog-badge,
.tags-dialog-counter {
  flex: 0 0 auto;
  padding: 8px 14px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(255, 244, 221, 0.96), rgba(255, 237, 213, 0.9));
  color: #8b5e34;
  font-size: 12px;
  font-weight: 700;
  box-shadow: inset 0 0 0 1px rgba(231, 202, 163, 0.72);
}

.stock-badge {
  color: #a16207;
}

.dialog-panel {
  padding: 16px 16px 14px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255, 251, 245, 0.96), rgba(255, 247, 235, 0.94));
  box-shadow: inset 0 0 0 1px rgba(235, 220, 194, 0.88);
}

.compact-tip-panel {
  padding-bottom: 16px;
}

.tags-dialog-list {
  gap: 10px;
}

.dialog-tag-chip {
  border: 0;
  padding: 9px 15px;
  border-radius: 999px;
  background: #fffaf3;
  color: #8a6c4c;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: inset 0 0 0 1px rgba(232, 210, 184, 0.82);
  transition: all 0.2s ease;
}

.dialog-tag-chip:hover {
  transform: translateY(-1px);
  background: #fff2df;
  color: #7a5530;
}

.dialog-tag-chip.active {
  background: linear-gradient(135deg, #d8f2e5, #c4ead6);
  color: #21684f;
  box-shadow: 0 10px 22px rgba(103, 170, 136, 0.16);
}

.dialog-tag-chip.add-chip {
  background: linear-gradient(135deg, rgba(243, 248, 255, 0.96), rgba(230, 241, 255, 0.94));
  color: #2563eb;
  box-shadow: inset 0 0 0 1px rgba(174, 205, 255, 0.86);
}

.dialog-tag-chip.add-chip:hover {
  background: linear-gradient(135deg, rgba(233, 243, 255, 0.98), rgba(219, 235, 255, 0.96));
  color: #1d4ed8;
}

.selected-tags-list {
  min-height: 44px;
}

.selected-dialog-tag {
  --el-tag-bg-color: rgba(214, 241, 230, 0.96);
  --el-tag-border-color: rgba(155, 209, 182, 0.88);
  --el-tag-hover-color: rgba(198, 233, 217, 1);
  --el-tag-text-color: #21684f;
  padding-inline: 10px;
  border-radius: 999px;
  font-weight: 600;
}

.tags-empty-state {
  width: 100%;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
  color: #9b7e5c;
  font-size: 13px;
  line-height: 1.6;
  box-shadow: inset 0 0 0 1px rgba(238, 225, 204, 0.92);
}

.showcase-dialog-textarea :deep(.el-textarea__inner),
.tags-custom-input :deep(.el-input__wrapper),
.tags-custom-input :deep(.el-input-group__append) {
  background: #fffaf3;
  box-shadow: 0 0 0 1px rgba(232, 210, 184, 0.78) inset;
}

.showcase-dialog-textarea :deep(.el-textarea__inner) {
  min-height: 148px;
  border-radius: 18px;
  color: #5f4932;
  line-height: 1.75;
}

.tags-custom-input :deep(.el-input__wrapper.is-focus),
.showcase-dialog-textarea :deep(.el-textarea__inner:focus) {
  box-shadow: 0 0 0 1px #d6a96b inset;
}

.tags-add-button {
  color: #8b5e34;
  font-weight: 700;
}

.tags-dialog-tip {
  margin-top: 10px;
  color: #a0815d;
  font-size: 12px;
  line-height: 1.7;
}

.stock-dialog-body {
  gap: 14px;
}

.stock-summary-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.stock-summary-label {
  color: #9b7e5c;
  font-size: 13px;
  font-weight: 600;
}

.stock-summary-value {
  color: #a16207;
  font-size: 30px;
  line-height: 1;
  font-weight: 800;
}

.stock-table-panel {
  padding-top: 12px;
}

.showcase-dialog-table :deep(.el-table) {
  --el-table-border-color: rgba(236, 221, 199, 0.92);
  --el-table-header-bg-color: rgba(255, 248, 238, 0.96);
  --el-table-tr-bg-color: rgba(255, 253, 249, 0.96);
  --el-table-row-hover-bg-color: rgba(255, 245, 229, 0.92);
  --el-table-text-color: #57412d;
  --el-table-header-text-color: #8b5e34;
}

.showcase-dialog-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.showcase-dialog-table :deep(th.el-table__cell) {
  font-weight: 700;
}

.showcase-dialog-table :deep(.el-table__cell) {
  padding: 14px 0;
}

.product-thumb {
  width: 62px;
  height: 62px;
  border-radius: 16px;
  box-shadow: 0 6px 16px rgba(126, 98, 63, 0.12);
}

.stock-loading {
  padding: 16px;
}

.showcase-dialog :deep(.el-dialog) {
  border-radius: 28px;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(255, 253, 249, 0.98), rgba(255, 248, 238, 0.98));
  box-shadow: 0 26px 60px rgba(97, 72, 43, 0.16);
}

.showcase-dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding: 24px 28px 10px;
}

.showcase-dialog :deep(.el-dialog__title) {
  color: #2f2418;
  font-size: 22px;
  font-weight: 800;
}

.showcase-dialog :deep(.el-dialog__body) {
  padding: 8px 28px 18px;
}

.showcase-dialog :deep(.el-dialog__footer) {
  padding: 10px 28px 26px;
}

.showcase-dialog :deep(.el-dialog__headerbtn) {
  top: 24px;
  right: 24px;
}

.showcase-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #a18461;
}

.showcase-dialog :deep(.el-dialog__footer .el-button) {
  min-width: 92px;
  height: 40px;
  border-radius: 14px;
}

.showcase-dialog :deep(.el-dialog__footer .el-button--default) {
  border-color: rgba(219, 183, 141, 0.74);
  color: #8b5e34;
  background: #fff9f2;
}

.showcase-dialog :deep(.el-dialog__footer .el-button--primary) {
  border: 0;
  background: linear-gradient(135deg, #f0c37c, #d9a25f);
  box-shadow: 0 12px 24px rgba(219, 162, 88, 0.22);
}

.floating-actions {
  padding: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.ref-action-group {
  gap: 8px;
}

.showcase-icon-button {
  width: auto;
  height: auto;
  border: 0;
  border-radius: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: #8a6c4c;
  box-shadow: none;
  cursor: pointer;
  transition: color 0.18s ease, transform 0.18s ease, opacity 0.18s ease;
}

.ref-action-button {
  padding: 0;
  background: transparent;
  color: #8e949f;
  box-shadow: none;
}

.icon-plain-button {
  min-width: 16px;
  line-height: 1;
  opacity: 0.95;
}

.icon-plain-button :deep(.el-icon) {
  font-size: 15px;
}

.ref-action-button:hover {
  color: #5f6b7a;
  background: transparent;
  box-shadow: none;
  transform: translateY(-1px);
}

.ref-action-button-favorite.active {
  color: #e5a22d;
  opacity: 1;
}

.ref-action-button-favorite.active:hover {
  color: #d99623;
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
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 4;
  overflow: hidden;
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
}

.compact-footer {
  align-items: flex-end;
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
    column-count: 3;
  }
}

@media (max-width: 1024px) {
  .programs-showcase-page::before {
    inset: 0;
  }

  .showcase-grid {
    column-count: 3;
  }
}

@media (max-width: 768px) {
  .showcase-toolbar-card,
  .showcase-card {
    border-radius: 22px;
  }

  .showcase-grid {
    column-count: 1;
  }

  .showcase-card-top,
  .showcase-card-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .showcase-card-actions {
    justify-content: flex-start;
    flex-wrap: wrap;
  }

  .ref-action-group {
    gap: 8px;
  }

  .compact-footer,
  .compact-footer-actions {
    align-items: stretch;
    justify-content: flex-start;
  }
}
</style>
