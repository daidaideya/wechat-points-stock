<template>
  <div class="page-stack">
    <el-card shadow="never">
      <template #header>
        <div class="section-header">
          <span>用户管理</span>
          <el-button type="primary" plain @click="openEdit(null)">新增用户</el-button>
        </div>
      </template>

      <el-skeleton v-if="loading" :rows="8" animated />
      <el-table v-else :data="items" stripe>
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
    </el-card>

    <el-dialog v-model="dialogVisible" :title="currentRow ? '编辑用户' : '新增用户'" width="520px">
      <el-form label-width="90px">
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
        <el-button type="primary" @click="saveUser" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="pointsVisible" :title="pointsTitle" width="900px">
      <el-skeleton v-if="pointsLoading" :rows="6" animated />
      <el-table v-else :data="pointItems" stripe>
        <el-table-column prop="program_name" label="小程序" min-width="240" />
        <el-table-column prop="points" label="积分" width="120" />
        <el-table-column prop="diff" label="今日变化" width="120" />
        <el-table-column label="更新时间" min-width="180">
          <template #default="scope">{{ formatDate(scope.row.report_time) }}</template>
        </el-table-column>
      </el-table>
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
