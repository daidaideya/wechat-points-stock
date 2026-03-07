<template>
  <div class="page-stack programs-page">
    <section class="toolbar-card programs-toolbar-card">
      <div class="programs-toolbar-head compact">
        <div>
          <h2 class="section-title compact">快速检索小程序</h2>
          <p class="section-description compact">支持名称、program_id、拼音、收藏状态和标签组合筛选。</p>
        </div>
        <div class="toolbar-status-chip compact">
          <span class="toolbar-status-value">{{ total }}</span>
          <span class="toolbar-status-label">当前结果</span>
        </div>
      </div>

      <div class="toolbar-row programs-toolbar-row compact">
        <el-input
          v-model="searchKeyword"
          clearable
          size="large"
          placeholder="搜索小程序名称 / program_id / 拼音"
          @keyup.enter="applyFilters"
          @clear="applyFilters"
        >
          <template #append>
            <el-button @click="applyFilters">搜索</el-button>
          </template>
        </el-input>

        <el-select v-model="favoriteFilter" size="large" class="toolbar-select" @change="applyFilters">
          <el-option label="全部" value="all" />
          <el-option label="仅收藏" value="favorite" />
          <el-option label="仅未收藏" value="unfavorite" />
        </el-select>

        <el-button size="large" plain :disabled="!hasActiveFilters" @click="resetFilters">重置</el-button>
      </div>

      <div class="tag-toolbar programs-tag-toolbar compact">
        <div class="tag-toolbar-top compact">
          <span class="tag-toolbar-label">标签筛选</span>
          <span class="tag-toolbar-tip">点击切换，重复点击取消</span>
        </div>
        <div class="tag-list content filter-tag-list compact">
          <el-check-tag :checked="currentTag === ''" @change="selectTag('')">全部</el-check-tag>
          <el-check-tag
            v-for="tag in availableTags"
            :key="tag"
            :checked="currentTag === tag"
            @change="selectTag(tag)"
          >
            {{ tag }}
          </el-check-tag>
          <span v-if="!availableTags.length" class="empty-text">暂无可筛选标签</span>
        </div>
      </div>
    </section>

    <section v-if="loading && programs.length === 0" class="skeleton-grid compact">
      <el-card v-for="item in 6" :key="item" shadow="hover" class="program-card skeleton-card compact">
        <el-skeleton animated>
          <template #template>
            <el-skeleton-item variant="h3" style="width: 54%; height: 26px; margin-bottom: 14px" />
            <el-skeleton-item variant="text" style="width: 82%; margin-bottom: 10px" />
            <el-skeleton-item variant="text" style="width: 58%; margin-bottom: 14px" />
            <el-skeleton-item variant="text" style="width: 100%; height: 28px; margin-bottom: 10px" />
            <el-skeleton-item variant="text" style="width: 40%" />
          </template>
        </el-skeleton>
      </el-card>
    </section>

    <section v-else class="program-grid compact">
      <div v-if="loadError" class="program-state-card compact">
        <el-result icon="error" title="列表加载失败" sub-title="请检查网络或接口状态后重试。">
          <template #extra>
            <el-button type="primary" @click="applyFilters">重新加载</el-button>
          </template>
        </el-result>
      </div>

      <div v-else-if="!programs.length" class="program-state-card compact">
        <el-empty description="没有符合条件的小程序">
          <template #description>
            <p>可尝试清空关键词、标签或收藏筛选后重新查看。</p>
          </template>
          <div class="empty-state-actions">
            <el-button type="primary" plain @click="resetFilters">清空筛选</el-button>
          </div>
        </el-empty>
      </div>

      <el-card v-for="program in programs" v-else :key="program.program_id" shadow="hover" class="program-card program-entry-card compact">
        <template #header>
          <div class="program-card-header compact stacked-card-header">
            <div class="title-wrap program-title-wrap compact full-width-title">
              <div class="program-title-row compact">
                <h3>{{ program.program_name || program.program_id }}</h3>
              </div>
              <div class="program-subline stacked-subline">
                <span class="program-id inline">{{ program.program_id }}</span>
              </div>
              <div class="card-actions program-card-actions compact icon-action-group under-id-actions">
                <el-tooltip v-if="program.has_stock" content="查看库存" placement="top">
                  <el-button
                    circle
                    size="small"
                    type="success"
                    plain
                    class="icon-action-button round-icon-button"
                    @click="openStockDialog(program)"
                  >
                    <el-icon><Box /></el-icon>
                  </el-button>
                </el-tooltip>

                <el-tooltip content="编辑备注" placement="top">
                  <el-button circle size="small" plain class="icon-action-button round-icon-button" @click="openNoteDialog(program)">
                    <el-icon><EditPen /></el-icon>
                  </el-button>
                </el-tooltip>

                <el-tooltip content="编辑标签" placement="top">
                  <el-button circle size="small" plain class="icon-action-button round-icon-button" @click="openTagsDialog(program)">
                    <el-icon><CollectionTag /></el-icon>
                  </el-button>
                </el-tooltip>

                <el-tooltip content="查看详情" placement="top">
                  <el-button circle size="small" plain class="icon-action-button round-icon-button" @click="router.push(`/programs/${program.program_id}`)">
                    <el-icon><ArrowRight /></el-icon>
                  </el-button>
                </el-tooltip>

                <el-tooltip :content="program.is_favorite ? '取消收藏' : '加入收藏'" placement="top">
                  <el-button
                    circle
                    size="small"
                    :type="program.is_favorite ? 'warning' : 'default'"
                    :plain="!program.is_favorite"
                    class="icon-action-button round-icon-button favorite-action-button"
                    @click="toggleFavorite(program)"
                    :loading="updatingProgramId === program.program_id"
                  >
                    <el-icon><Star /></el-icon>
                  </el-button>
                </el-tooltip>

              </div>
            </div>
          </div>
        </template>

        <div class="program-card-body compact">
          <div v-if="program.note" class="program-inline-section compact note-inline-section moved-up">
            <span class="inline-section-label">备注</span>
            <p class="note-text compact">{{ program.note }}</p>
          </div>

          <div v-if="(program.tags || []).length" class="program-inline-section compact">
            <span class="inline-section-label">标签</span>
            <div class="tag-list compact mini-tag-list">
              <el-tag v-for="tag in program.tags || []" :key="`${program.program_id}-${tag}`" size="small" round>
                {{ tag }}
              </el-tag>
            </div>
          </div>

          <div class="program-footer-line compact aligned-footer-line">
            <div class="program-time-inline aligned-time-inline">
              <el-icon class="program-time-icon"><Clock /></el-icon>
              <span class="program-time-text">{{ formatDate(program.last_update_time) }}</span>
            </div>
          </div>
        </div>
      </el-card>
    </section>

    <div v-if="programs.length && !loadError" ref="loadMoreSentinel" class="infinite-sentinel" aria-hidden="true"></div>

    <div v-if="programs.length && !loadError" class="infinite-status-bar">
      <span v-if="loadingMore" class="infinite-status-text">正在加载更多...</span>
      <span v-else-if="!hasMore" class="infinite-status-text done">已加载全部数据</span>
      <span v-else class="infinite-status-text">继续下滑可自动加载更多</span>
    </div>

    <el-dialog v-model="noteDialogVisible" title="编辑备注" width="520px">
      <el-input v-model="editingNote" type="textarea" :rows="5" maxlength="200" show-word-limit placeholder="请输入备注" />
      <template #footer>
        <el-button @click="noteDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveNote" :loading="savingNote">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="tagsDialogVisible" title="编辑标签" width="560px">
      <div class="dialog-section">
        <div class="block-label">快捷标签</div>
        <div class="tag-list content">
          <el-tag v-for="tag in quickTags" :key="tag" class="clickable-tag" @click="appendTag(tag)">{{ tag }}</el-tag>
          <el-tag class="clickable-tag add-tag" @click="promptCustomTag">+ 自定义</el-tag>
        </div>
      </div>

      <div class="dialog-section">
        <div class="block-label">已选标签</div>
        <div class="tag-list content">
          <el-tag v-for="tag in editingTags" :key="tag" closable @close="removeEditingTag(tag)">{{ tag }}</el-tag>
          <span v-if="!editingTags.length" class="empty-text">暂无标签</span>
        </div>
      </div>

      <el-input v-model="customTagInput" maxlength="20" placeholder="输入自定义标签后点击添加" @keyup.enter="addCustomTagFromInput">
        <template #append>
          <el-button @click="addCustomTagFromInput">添加</el-button>
        </template>
      </el-input>

      <template #footer>
        <el-button @click="tagsDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTags" :loading="savingTags">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="stockDialogVisible" :title="stockDialogTitle" width="960px" top="5vh">
      <div v-if="stockLoading" class="stock-loading">
        <el-skeleton :rows="6" animated />
      </div>
      <template v-else>
        <div class="stock-summary">当前最高用户积分：<strong>{{ stockData?.max_user_points ?? 0 }}</strong></div>
        <el-table :data="stockData?.products || []" stripe>
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
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowRight, Box, Clock, CollectionTag, EditPen, Star } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const pageSize = 21
const quickTags = ['现金类', '全品类', '母婴类', '快消类']
const loadMoreSentinel = ref(null)

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
const updatingProgramId = ref('')
const noteDialogVisible = ref(false)
const tagsDialogVisible = ref(false)
const stockDialogVisible = ref(false)
const currentProgram = ref(null)
const editingNote = ref('')
const editingTags = ref([])
const customTagInput = ref('')
const stockData = ref(null)

let observer = null

const stockDialogTitle = computed(() => {
  if (!stockData.value?.program_name) return '库存详情'
  return `${stockData.value.program_name} - 库存详情`
})

const hasActiveFilters = computed(() => {
  return Boolean(searchKeyword.value.trim()) || favoriteFilter.value !== 'all' || Boolean(currentTag.value)
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

function formatDate(value) {
  if (!value) return '暂无数据'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

function getRequestParams(nextPage = 1) {
  const params = { page: nextPage, size: pageSize }
  const keyword = searchKeyword.value.trim()
  if (keyword) params.q = keyword
  if (favoriteFilter.value === 'favorite') params.is_favorite = true
  else if (favoriteFilter.value === 'unfavorite') params.is_favorite = false
  if (currentTag.value) params.tag = currentTag.value
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
    availableTags.value = Array.from(new Set([...availableTags.value, ...currentProgram.value.tags])).sort((a, b) => a.localeCompare(b, 'zh-CN'))
    ElMessage.success('标签已保存')
  } catch (error) {
    console.error(error)
    ElMessage.error('保存标签失败')
  } finally {
    savingTags.value = false
  }
}

async function toggleFavorite(program) {
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

watch(() => programs.value.length, async (value) => {
  if (!value || loadError.value) return
  await nextTick()
  initInfiniteScroll()
})

onMounted(() => {
  fetchPrograms(1, false)
})

onBeforeUnmount(() => {
  destroyInfiniteScroll()
})
</script>
