<template>
  <div class="page-stack users-page">
    <section class="toolbar-card users-hero-card">
      <div class="users-hero-head">
        <div>
          <h2 class="section-title users-hero-title">用户管理</h2>
          <p class="section-description users-hero-description">统一管理微信号、昵称、设备与手机号，并快速查看积分详情。</p>
        </div>
        <div class="users-hero-actions">
          <el-button type="primary" class="users-primary-button" @click="openEdit(null)">新增用户</el-button>
        </div>
      </div>

      <div class="users-summary-grid">
        <div class="users-summary-card">
          <span class="users-summary-label">用户数量</span>
          <strong class="users-summary-value">{{ items.length }}</strong>
        </div>
        <div class="users-summary-card">
          <span class="users-summary-label">活跃小程序总计</span>
          <strong class="users-summary-value">{{ totalActivePrograms }}</strong>
        </div>
        <div class="users-summary-card">
          <span class="users-summary-label">已留手机号</span>
          <strong class="users-summary-value">{{ usersWithPhone }}</strong>
        </div>
      </div>
    </section>

    <section class="toolbar-card users-list-card">
      <div class="users-list-head">
        <div>
          <h3 class="section-title compact">用户列表</h3>
          <p class="section-description compact">桌面端支持表格查看，手机端自动切换为卡片布局。</p>
        </div>
      </div>

      <el-skeleton v-if="loading" :rows="8" animated />

      <template v-else>
        <el-empty v-if="!items.length" description="暂无用户数据" />

        <div v-else class="users-mobile-list">
          <article v-for="item in items" :key="item.wechat_id" class="users-mobile-card">
            <div class="users-mobile-card-top">
              <div class="users-mobile-title-wrap">
                <h3 class="users-mobile-title">{{ item.nickname || '未命名用户' }}</h3>
                <div class="users-mobile-subtitle">{{ item.wechat_id || '未设置微信号' }}</div>
              </div>
              <span class="users-mobile-count-chip">{{ item.active_program_count ?? 0 }} 个活跃小程序</span>
            </div>

            <div class="users-mobile-meta-grid">
              <div class="users-mobile-meta-item">
                <span class="users-mobile-meta-label">设备</span>
                <span class="users-mobile-meta-value">{{ item.device || '未填写' }}</span>
              </div>
              <div class="users-mobile-meta-item">
                <span class="users-mobile-meta-label">手机号</span>
                <span class="users-mobile-meta-value">{{ item.phone || '未填写' }}</span>
              </div>
            </div>

            <div class="users-mobile-actions">
              <el-button size="small" @click="openEdit(item)">编辑</el-button>
              <el-button size="small" @click="viewPoints(item)">积分</el-button>
              <el-popconfirm title="确认删除该用户？" @confirm="removeUser(item)">
                <template #reference>
                  <el-button size="small" type="danger" plain>删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </article>
        </div>

        <div v-if="items.length" class="users-desktop-table-wrap">
          <el-table :data="items" stripe class="users-table">
            <el-table-column prop="nickname" label="昵称" min-width="160" />
            <el-table-column prop="wechat_id" label="微信号" min-width="200" />
            <el-table-column prop="device" label="设备" min-width="140" />
            <el-table-column prop="phone" label="手机号" min-width="140" />
            <el-table-column prop="active_program_count" label="活跃小程序" width="120" />
            <el-table-column label="操作" width="220" fixed="right">
              <template #default="scope">
                <el-button size="small" @click="openEdit(scope.row)">编辑</el-button>
                <el-button size="small" @click="viewPoints(scope.row)">积分</el-button>
                <el-popconfirm title="确认删除该用户？" @confirm="removeUser(scope.row)">
                  <template #reference>
                    <el-button size="small" type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </template>
    </section>

    <el-dialog v-model="dialogVisible" :title="currentRow ? '编辑用户' : '新增用户'" width="520px" class="users-edit-dialog">
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

    <el-dialog v-model="pointsVisible" :title="pointsTitle" width="900px" class="users-points-dialog">
      <el-skeleton v-if="pointsLoading" :rows="6" animated />
      <template v-else>
        <el-empty v-if="!pointItems.length" description="暂无积分详情" />
        <div v-else class="users-points-mobile-list">
          <article v-for="point in pointItems" :key="`${point.program_name}-${point.report_time}`" class="users-points-mobile-card">
            <div class="users-points-mobile-top">
              <strong class="users-points-mobile-title">{{ point.program_name || '未知小程序' }}</strong>
              <span class="users-points-mobile-value">{{ point.points ?? 0 }} 积分</span>
            </div>
            <div class="users-points-mobile-meta">
              <span>今日变化：{{ point.diff ?? 0 }}</span>
              <span>{{ formatDate(point.report_time) }}</span>
            </div>
          </article>
        </div>
        <div class="users-points-desktop-table-wrap">
          <el-table :data="pointItems" stripe class="users-table">
            <el-table-column prop="program_name" label="小程序" min-width="240" />
            <el-table-column prop="points" label="积分" width="120" />
            <el-table-column prop="diff" label="今日变化" width="120" />
            <el-table-column label="更新时间" min-width="180">
              <template #default="scope">{{ formatDate(scope.row.report_time) }}</template>
            </el-table-column>
          </el-table>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const pointsVisible = ref(false)
const pointsLoading = ref(false)
const items = ref([])
const pointItems = ref([])
const currentRow = ref(null)
const pointsUser = ref(null)

const form = reactive({
  wechat_id: '',
  nickname: '',
  device: '',
  phone: '',
})

const pointsTitle = computed(() => pointsUser.value ? `${pointsUser.value.nickname || pointsUser.value.wechat_id} - 积分详情` : '积分详情')
const totalActivePrograms = computed(() => items.value.reduce((sum, item) => sum + Number(item.active_program_count || 0), 0))
const usersWithPhone = computed(() => items.value.filter((item) => String(item.phone || '').trim()).length)

function formatDate(value) {
  if (!value) return '暂无'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

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
    ElMessage.error('加载用户列表失败')
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
    loadUsers()
  } catch (error) {
    console.error(error)
    ElMessage.error('保存用户失败')
  } finally {
    saving.value = false
  }
}

async function removeUser(row) {
  try {
    await api.delete(`/accounts/${encodeURIComponent(row.wechat_id)}`)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (error) {
    console.error(error)
    ElMessage.error('删除用户失败')
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
    ElMessage.error('加载积分详情失败')
  } finally {
    pointsLoading.value = false
  }
}

onMounted(loadUsers)
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
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.users-summary-card {
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 249, 240, 0.9);
  border: 1px solid rgba(232, 211, 183, 0.86);
}

.users-summary-label {
  display: block;
  color: #8a6c4c;
  font-size: 12px;
}

.users-summary-value {
  display: block;
  margin-top: 8px;
  color: #3a2b1a;
  font-size: 26px;
  line-height: 1.1;
}

.users-list-head {
  margin-bottom: 14px;
}

.users-desktop-table-wrap,
.users-points-desktop-table-wrap {
  display: block;
}

.users-mobile-list,
.users-points-mobile-list {
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

.users-edit-dialog :deep(.el-dialog),
.users-points-dialog :deep(.el-dialog) {
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
    grid-template-columns: 1fr;
  }

  .users-desktop-table-wrap,
  .users-points-desktop-table-wrap {
    display: none;
  }

  .users-mobile-list,
  .users-points-mobile-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .users-mobile-card,
  .users-points-mobile-card {
    padding: 16px;
    border-radius: 20px;
    background: #fffdf9;
    border: 1px solid rgba(232, 211, 183, 0.9);
    box-shadow: 0 10px 24px rgba(145, 109, 61, 0.06);
  }

  .users-mobile-card-top,
  .users-points-mobile-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
  }

  .users-mobile-title-wrap {
    min-width: 0;
    flex: 1;
  }

  .users-mobile-title,
  .users-points-mobile-title {
    margin: 0;
    color: #3a2b1a;
    font-size: 18px;
    line-height: 1.35;
  }

  .users-mobile-subtitle,
  .users-points-mobile-meta {
    margin-top: 6px;
    color: #8a6c4c;
    font-size: 12px;
    line-height: 1.6;
    word-break: break-all;
  }

  .users-mobile-count-chip {
    flex: 0 0 auto;
    padding: 8px 12px;
    border-radius: 999px;
    background: rgba(231, 179, 90, 0.16);
    color: #b87718;
    font-size: 12px;
    font-weight: 700;
    white-space: nowrap;
  }

  .users-mobile-meta-grid {
    margin-top: 14px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }

  .users-mobile-meta-item {
    padding: 12px;
    border-radius: 16px;
    background: rgba(255, 248, 238, 0.9);
    border: 1px solid rgba(232, 211, 183, 0.72);
  }

  .users-mobile-meta-label {
    display: block;
    color: #8a6c4c;
    font-size: 11px;
  }

  .users-mobile-meta-value {
    display: block;
    margin-top: 6px;
    color: #3a2b1a;
    font-size: 13px;
    line-height: 1.5;
    word-break: break-all;
  }

  .users-mobile-actions {
    margin-top: 14px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .users-points-mobile-value {
    color: #b87718;
    font-size: 14px;
    font-weight: 700;
    white-space: nowrap;
  }

  .users-points-mobile-meta {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
}

@media (max-width: 640px) {
  .users-hero-card,
  .users-list-card {
    border-radius: 20px;
  }

  .users-mobile-card-top,
  .users-points-mobile-top {
    flex-direction: column;
    align-items: stretch;
  }

  .users-mobile-meta-grid {
    grid-template-columns: 1fr;
  }

  .users-mobile-actions {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .users-mobile-actions :deep(.el-button),
  .users-mobile-actions :deep(.el-popconfirm__reference) {
    width: 100%;
  }
}
</style>
