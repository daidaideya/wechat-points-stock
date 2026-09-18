<template>
  <div class="page-stack users-page">
    <section class="toolbar-card users-hero-card">
      <div class="users-hero-head">
        <div>
          <h2 class="section-title users-hero-title">用户管理</h2>
          <p class="section-description users-hero-description">
            统一管理微信号、昵称、设备与手机号，并快速查看积分详情。
          </p>
        </div>
        <div class="users-hero-actions">
          <el-button type="primary" :icon="Plus" class="users-primary-button" @click="openEdit(null)">
            新增用户
          </el-button>
        </div>
      </div>

      <div class="users-summary-grid">
        <div class="users-summary-card">
          <div class="users-summary-icon" aria-hidden="true">👥</div>
          <div class="users-summary-body">
            <span class="users-summary-label">用户数量</span>
            <strong class="users-summary-value">{{ items.length }}</strong>
          </div>
        </div>
        <div class="users-summary-card">
          <div class="users-summary-icon" aria-hidden="true">🎯</div>
          <div class="users-summary-body">
            <span class="users-summary-label">活跃小程序总计</span>
            <strong class="users-summary-value">{{ totalActivePrograms }}</strong>
          </div>
        </div>
        <div class="users-summary-card">
          <div class="users-summary-icon" aria-hidden="true">📦</div>
          <div class="users-summary-body">
            <span class="users-summary-label">活跃 APP 总计</span>
            <strong class="users-summary-value">{{ totalActiveApps }}</strong>
          </div>
        </div>
        <div class="users-summary-card">
          <div class="users-summary-icon" aria-hidden="true">📱</div>
          <div class="users-summary-body">
            <span class="users-summary-label">已留手机号</span>
            <strong class="users-summary-value">{{ usersWithPhone }}</strong>
          </div>
        </div>
      </div>
    </section>

    <section class="toolbar-card users-list-card">
      <div class="users-list-head">
        <div>
          <h3 class="section-title compact">用户列表</h3>
          <p class="section-description compact">按住左侧 <strong>⋮⋮</strong> 拖拽即可调整顺序，松手后自动保存。</p>
        </div>
        <div v-if="sorting" class="users-sort-saving">正在保存顺序…</div>
      </div>

      <el-skeleton v-if="loading" :rows="8" animated />

      <template v-else>
        <el-empty v-if="!items.length" description="暂无用户数据" />

        <div v-else ref="mobileListRef" class="users-mobile-list">
          <UserMobileCard
            v-for="(item, index) in items"
            :key="item.wechat_id"
            :item="item"
            :index="index"
            :deleting-wechat-id="deletingWechatId"
            @edit="openEdit"
            @view-points="viewPoints"
            @remove="removeUser"
          />
        </div>

        <div v-if="items.length" class="users-desktop-table-wrap">
          <el-table ref="desktopTableRef" :data="items" stripe row-key="wechat_id" class="users-table">
            <el-table-column label="排序" width="88" align="center">
              <template #default="scope">
                <div class="users-sort-cell">
                  <button type="button" class="users-drag-handle" title="拖拽排序" aria-label="拖拽排序" @click.stop>
                    <el-icon><Rank /></el-icon>
                  </button>
                  <span class="users-sort-index">{{ scope.$index + 1 }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="昵称" min-width="180">
              <template #default="scope">
                <div class="users-table-identity">
                  <div class="users-avatar users-avatar-sm" :style="{ background: avatarColor(scope.row) }">
                    {{ avatarChar(scope.row) }}
                  </div>
                  <span class="users-table-nickname">{{ displayName(scope.row) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="手机号" min-width="150">
              <template #default="scope">{{ displayPhone(scope.row) || '—' }}</template>
            </el-table-column>
            <el-table-column label="微信号" min-width="180">
              <template #default="scope">{{ displayWechatId(scope.row) || '—' }}</template>
            </el-table-column>
            <el-table-column prop="device" label="设备" min-width="140" />
            <el-table-column prop="active_program_count" label="活跃小程序" width="110" align="center" />
            <el-table-column prop="active_app_count" label="活跃APP" width="100" align="center" />
            <el-table-column label="操作" width="240" fixed="right">
              <template #default="scope">
                <el-button size="small" @click="openEdit(scope.row)">编辑</el-button>
                <el-button size="small" @click="viewPoints(scope.row)">积分</el-button>
                <el-button
                  size="small"
                  type="danger"
                  plain
                  :loading="deletingWechatId === scope.row.wechat_id"
                  @click="removeUser(scope.row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </template>
    </section>

    <el-dialog
      v-model="dialogVisible"
      :title="currentRow ? '编辑用户' : '新增用户'"
      width="520px"
      class="users-edit-dialog"
    >
      <el-form label-width="90px" class="users-form">
        <el-form-item label="微信号">
          <el-input v-model="form.wechat_id" :disabled="Boolean(currentRow)" />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" />
        </el-form-item>
        <el-form-item label="设备">
          <el-input v-model="form.device" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" class="users-primary-button" @click="saveUser" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <UserPointsDialog v-model="pointsVisible" :title="pointsTitle" :loading="pointsLoading" :items="pointItems" />
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Rank } from '@element-plus/icons-vue'
import Sortable from 'sortablejs'
import api from '../api'
import UserPointsDialog from '../components/UserPointsDialog.vue'
import UserMobileCard from '../components/UserMobileCard.vue'
import { getApiErrorMessage } from '../utils/apiError'
import { avatarChar, avatarColor, displayName, displayPhone, displayWechatId } from '../utils/user'

const loading = ref(false)
const saving = ref(false)
const sorting = ref(false)
const deletingWechatId = ref('')
const dialogVisible = ref(false)
const pointsVisible = ref(false)
const pointsLoading = ref(false)
const items = ref([])
const pointItems = ref([])
const currentRow = ref(null)
const pointsUser = ref(null)
const mobileListRef = ref(null)
const desktopTableRef = ref(null)

let mobileSortable = null
let desktopSortable = null
let sortSaveTimer = null

const form = reactive({
  wechat_id: '',
  nickname: '',
  device: '',
  phone: '',
})

const pointsTitle = computed(() => {
  if (!pointsUser.value) return '积分详情'
  return `${displayName(pointsUser.value)} - 积分详情`
})
const totalActivePrograms = computed(() =>
  items.value.reduce((sum, item) => sum + Number(item.active_program_count || 0), 0),
)
const totalActiveApps = computed(() => items.value.reduce((sum, item) => sum + Number(item.active_app_count || 0), 0))
const usersWithPhone = computed(() => items.value.filter((item) => Boolean(displayPhone(item))).length)

function resetForm() {
  form.wechat_id = ''
  form.nickname = ''
  form.device = ''
  form.phone = ''
}

function openEdit(row) {
  currentRow.value = row
  if (row) {
    form.wechat_id = row.wechat_id || ''
    form.nickname = row.nickname || ''
    form.device = row.device || ''
    form.phone = row.phone || ''
  } else {
    resetForm()
  }
  dialogVisible.value = true
}

async function loadUsers() {
  loading.value = true
  try {
    const { data } = await api.get('/accounts')
    items.value = data.items || []
  } catch (error) {
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '加载用户列表失败'))
  } finally {
    loading.value = false
  }
}

async function saveUser() {
  if (!form.wechat_id.trim()) {
    ElMessage.warning('微信号不能为空')
    return
  }
  saving.value = true
  try {
    await api.put(`/accounts/${encodeURIComponent(form.wechat_id)}`, {
      nickname: form.nickname,
      device: form.device,
      phone: form.phone,
    })
    dialogVisible.value = false
    ElMessage.success('保存成功')
    await loadUsersAndBindSort()
  } catch (error) {
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '保存用户失败'))
  } finally {
    saving.value = false
  }
}

async function removeUser(row) {
  const wechatId = String(row?.wechat_id || '').trim()
  if (!wechatId) {
    ElMessage.warning('微信号为空，无法删除')
    return
  }

  const displayName = row?.nickname || wechatId
  try {
    await ElMessageBox.confirm(`确认删除用户「${displayName}」吗？将同时删除该账号的积分记录。`, '删除用户', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    })
  } catch (_) {
    return
  }

  deletingWechatId.value = wechatId
  try {
    await api.delete(`/accounts/${encodeURIComponent(wechatId)}`)
    ElMessage.success('删除成功')
    await loadUsersAndBindSort()
  } catch (error) {
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '删除用户失败'))
  } finally {
    deletingWechatId.value = ''
  }
}

async function viewPoints(row) {
  pointsVisible.value = true
  pointsLoading.value = true
  pointsUser.value = row
  try {
    const { data } = await api.get(`/accounts/${encodeURIComponent(row.wechat_id)}/points_details`)
    pointItems.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '加载积分详情失败'))
  } finally {
    pointsLoading.value = false
  }
}

function destroySortables() {
  if (mobileSortable) {
    mobileSortable.destroy()
    mobileSortable = null
  }
  if (desktopSortable) {
    desktopSortable.destroy()
    desktopSortable = null
  }
  if (sortSaveTimer) {
    clearTimeout(sortSaveTimer)
    sortSaveTimer = null
  }
}

function reorderByWechatIds(orderedIds) {
  const map = new Map(items.value.map((item) => [item.wechat_id, item]))
  const next = []
  for (const id of orderedIds) {
    const row = map.get(id)
    if (row) next.push(row)
  }
  // Keep any rows missing from DOM (shouldn't happen) at the end.
  for (const item of items.value) {
    if (!orderedIds.includes(item.wechat_id)) next.push(item)
  }
  return next
}

async function persistSortOrder(nextItems, previousItems) {
  sorting.value = true
  try {
    await api.put('/accounts/sort-order', {
      wechat_ids: nextItems.map((item) => item.wechat_id),
    })
  } catch (error) {
    console.error(error)
    items.value = previousItems
    await nextTick()
    initSortables()
    ElMessage.error(getApiErrorMessage(error, '调整顺序失败，已回滚'))
  } finally {
    sorting.value = false
  }
}

function schedulePersistSort(nextItems, previousItems) {
  // Debounce rapid consecutive drags.
  if (sortSaveTimer) clearTimeout(sortSaveTimer)
  sortSaveTimer = setTimeout(() => {
    sortSaveTimer = null
    persistSortOrder(nextItems, previousItems)
  }, 120)
}

function onSortEnd(evt, mode) {
  if (!evt || evt.oldIndex == null || evt.newIndex == null) return
  if (evt.oldIndex === evt.newIndex) return
  if (sorting.value) return

  const previousItems = items.value.slice()
  let orderedIds = []

  if (mode === 'mobile') {
    const root = mobileListRef.value
    if (!root) return
    orderedIds = Array.from(root.querySelectorAll('.users-mobile-card'))
      .map((el) => el.getAttribute('data-wechat-id'))
      .filter(Boolean)
  } else {
    // Sortable mutates tbody DOM; read row-key order back out.
    const tbody = desktopTableRef.value?.$el?.querySelector?.('.el-table__body-wrapper tbody')
    if (!tbody) return
    orderedIds = Array.from(tbody.querySelectorAll('tr.el-table__row'))
      .map((tr) => {
        // Prefer data-wechat-id if present; else match by displayed order via row-key dataset
        return tr.getAttribute('data-wechat-id') || tr.dataset?.wechatId || null
      })
      .filter(Boolean)

    // Element Plus doesn't put wechat_id on tr by default — rebuild from indices.
    if (orderedIds.length !== items.value.length) {
      const next = items.value.slice()
      const [moved] = next.splice(evt.oldIndex, 1)
      next.splice(evt.newIndex, 0, moved)
      items.value = next
      schedulePersistSort(next, previousItems)
      return
    }
  }

  const next = reorderByWechatIds(orderedIds)
  items.value = next
  schedulePersistSort(next, previousItems)
}

function initMobileSortable() {
  if (mobileSortable) {
    mobileSortable.destroy()
    mobileSortable = null
  }
  const el = mobileListRef.value
  if (!el || !items.value.length) return
  mobileSortable = Sortable.create(el, {
    animation: 180,
    handle: '.users-drag-handle',
    draggable: '.users-mobile-card',
    ghostClass: 'users-sortable-ghost',
    chosenClass: 'users-sortable-chosen',
    dragClass: 'users-sortable-drag',
    forceFallback: true,
    fallbackOnBody: true,
    fallbackTolerance: 4,
    onEnd: (evt) => onSortEnd(evt, 'mobile'),
  })
}

function initDesktopSortable() {
  if (desktopSortable) {
    desktopSortable.destroy()
    desktopSortable = null
  }
  const tableVm = desktopTableRef.value
  const tbody = tableVm?.$el?.querySelector?.('.el-table__body-wrapper tbody')
  if (!tbody || !items.value.length) return

  desktopSortable = Sortable.create(tbody, {
    animation: 180,
    handle: '.users-drag-handle',
    draggable: 'tr.el-table__row',
    ghostClass: 'users-sortable-ghost',
    chosenClass: 'users-sortable-chosen',
    dragClass: 'users-sortable-drag',
    forceFallback: true,
    fallbackOnBody: true,
    fallbackTolerance: 3,
    onEnd: (evt) => onSortEnd(evt, 'desktop'),
  })
}

async function initSortables() {
  await nextTick()
  // Wait a frame so el-table finishes rendering tbody rows.
  requestAnimationFrame(() => {
    initMobileSortable()
    initDesktopSortable()
  })
}

async function loadUsersAndBindSort() {
  await loadUsers()
  await initSortables()
}

watch(
  () => items.value.length,
  async () => {
    await initSortables()
  },
)

onMounted(loadUsersAndBindSort)

onBeforeUnmount(() => {
  destroySortables()
})
</script>

<style scoped>
.users-page {
  gap: 18px;
}

.users-hero-card,
.users-list-card {
  border-radius: 24px;
}

.users-hero-head,
.users-list-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.users-hero-title {
  margin-bottom: 8px;
}

.users-hero-description {
  margin: 0;
}

.users-primary-button {
  border: none;
  background: linear-gradient(135deg, #e7b35a, #d89a3c);
  box-shadow: 0 10px 22px rgba(216, 154, 60, 0.18);
}

.users-summary-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.users-summary-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 249, 240, 0.9);
  border: 1px solid rgba(232, 211, 183, 0.86);
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease;
}

.users-summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(145, 109, 61, 0.1);
}

.users-summary-icon {
  flex: 0 0 auto;
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(231, 179, 90, 0.22), rgba(216, 154, 60, 0.16));
  font-size: 22px;
  line-height: 1;
}

.users-summary-body {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.users-summary-label {
  display: block;
  color: #8a6c4c;
  font-size: 12px;
}

.users-summary-value {
  display: block;
  margin-top: 6px;
  color: #3a2b1a;
  font-size: 26px;
  line-height: 1.1;
}

.users-list-head {
  margin-bottom: 14px;
}

.users-sort-saving {
  flex: 0 0 auto;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(96, 165, 250, 0.14);
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.users-desktop-table-wrap {
  display: block;
}

.users-mobile-list {
  display: none;
}

.users-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.users-table :deep(th.el-table__cell) {
  background: rgba(255, 248, 238, 0.9);
  color: #8a6c4c;
}

.users-table :deep(td.el-table__cell) {
  background: rgba(255, 253, 249, 0.96);
}

.users-sort-cell {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
}

.users-drag-handle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  border: 0;
  border-radius: 10px;
  background: rgba(231, 179, 90, 0.14);
  color: #a16207;
  cursor: grab;
  touch-action: none;
  -webkit-user-select: none;
  user-select: none;
  transition:
    background 0.15s ease,
    color 0.15s ease,
    transform 0.15s ease;
}

.users-drag-handle:hover {
  background: rgba(231, 179, 90, 0.28);
  color: #92400e;
}

.users-drag-handle:active {
  cursor: grabbing;
  transform: scale(0.96);
}

.users-drag-handle :deep(.el-icon) {
  font-size: 16px;
}

.users-sort-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(231, 179, 90, 0.16);
  color: #b87718;
  font-size: 12px;
  font-weight: 700;
}

.users-sortable-ghost {
  opacity: 0.45;
}

.users-sortable-chosen {
  box-shadow: 0 10px 24px rgba(145, 109, 61, 0.16);
}

.users-sortable-drag {
  opacity: 0.95;
}

/* Sortable fallback clone (forceFallback) */
:global(.sortable-fallback.users-sortable-drag),
:global(.sortable-fallback) {
  opacity: 0.95 !important;
}

.users-table-identity {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  max-width: 100%;
}

.users-table-nickname {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.users-avatar {
  flex: 0 0 auto;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  box-shadow: 0 6px 14px rgba(58, 43, 26, 0.18);
  background: linear-gradient(135deg, #e7b35a, #d89a3c);
  user-select: none;
}

.users-avatar-sm {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  font-size: 14px;
  box-shadow: 0 4px 10px rgba(58, 43, 26, 0.14);
}

.users-edit-dialog :deep(.el-dialog) {
  border-radius: 24px;
}

.users-form :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px rgba(232, 211, 183, 0.88) inset;
  background: #fffdf9;
}

.users-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #d89a3c inset;
}

@media (max-width: 900px) {
  .users-hero-head,
  .users-list-head {
    flex-direction: column;
    align-items: stretch;
  }

  .users-summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .users-desktop-table-wrap {
    display: none;
  }

  .users-mobile-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
}

@media (max-width: 640px) {
  .users-hero-card,
  .users-list-card {
    border-radius: 20px;
  }
}
</style>
