<template>
  <div class="page-stack settings-page">
    <el-card shadow="never">
      <template #header>
        <div class="section-header">
          <span>日志清理设置</span>
          <el-button text @click="loadSettings">刷新</el-button>
        </div>
      </template>

      <el-skeleton v-if="loading" :rows="4" animated />
      <el-form v-else label-width="120px" class="settings-form">
        <el-form-item label="最大日志条数">
          <el-input-number v-model="form.max_log_entries" :min="0" :step="100" />
        </el-form-item>
        <el-form-item label="保留天数">
          <el-input-number v-model="form.max_retention_days" :min="0" :step="1" />
        </el-form-item>
        <el-form-item label="最近更新时间">
          <span>{{ formatDate(updatedAt) }}</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving">保存并立即清理</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const loading = ref(false)
const saving = ref(false)
const updatedAt = ref('')
const form = reactive({
  max_log_entries: 10000,
  max_retention_days: 30,
})

function formatDate(value) {
  if (!value) return '暂无'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

async function loadSettings() {
  loading.value = true
  try {
    const { data } = await api.get('/settings/logs')
    form.max_log_entries = data.max_log_entries ?? 10000
    form.max_retention_days = data.max_retention_days ?? 30
    updatedAt.value = data.updated_at || ''
  } catch (error) {
    console.error(error)
    ElMessage.error('加载设置失败')
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  try {
    await api.post('/settings/logs', {
      max_log_entries: form.max_log_entries,
      max_retention_days: form.max_retention_days,
    })
    ElMessage.success('设置已保存')
    loadSettings()
  } catch (error) {
    console.error(error)
    ElMessage.error('保存设置失败')
  } finally {
    saving.value = false
  }
}

onMounted(loadSettings)
</script>
