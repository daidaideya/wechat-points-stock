<template>
  <div class="page-stack settings-page">
    <el-card shadow="never">
      <template #header>
        <div class="section-header">
          <span>系统设置</span>
          <el-button text @click="loadSettings">刷新</el-button>
        </div>
      </template>

      <el-skeleton v-if="loading" :rows="8" animated />
      <el-form v-else label-width="140px" class="settings-form">
        <div class="settings-block-title">日志清理设置</div>
        <el-form-item label="最大日志条数">
          <el-input-number v-model="form.max_log_entries" :min="0" :step="100" />
        </el-form-item>
        <el-form-item label="保留天数">
          <el-input-number v-model="form.max_retention_days" :min="0" :step="1" />
        </el-form-item>

        <div class="settings-block-title settings-block-spacing">访问保护设置</div>
        <el-form-item label="启用访问密钥">
          <div class="settings-inline-row">
            <el-switch v-model="form.access_protection_enabled" />
            <span class="settings-help-text">开启后，进入系统需先输入访问密钥</span>
          </div>
        </el-form-item>

        <el-form-item label="当前状态">
          <el-tag :type="form.access_protection_enabled ? 'warning' : 'info'" round effect="plain">
            {{ form.access_protection_enabled ? '已启用保护' : '未启用保护' }}
          </el-tag>
          <el-tag
            v-if="accessKeyConfigured"
            type="success"
            round
            effect="plain"
            style="margin-left: 8px"
          >
            已设置访问密钥
          </el-tag>
          <el-tag
            v-else
            type="danger"
            round
            effect="plain"
            style="margin-left: 8px"
          >
            未设置访问密钥
          </el-tag>
        </el-form-item>

        <el-form-item label="访问密钥">
          <el-input
            v-model="form.access_key"
            type="password"
            show-password
            maxlength="100"
            placeholder="留空表示不修改；首次设置可直接输入"
          />
        </el-form-item>

        <el-form-item label="最近更新时间">
          <span>{{ formatDate(updatedAt) }}</span>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving">保存设置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import api, { setAccessSession } from '../api'

const loading = ref(false)
const saving = ref(false)
const updatedAt = ref('')
const accessKeyConfigured = ref(false)
const form = reactive({
  max_log_entries: 10000,
  max_retention_days: 30,
  access_protection_enabled: false,
  access_key: '',
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
    form.access_protection_enabled = Boolean(data.access_protection_enabled)
    form.access_key = ''
    accessKeyConfigured.value = Boolean(data.access_key_configured)
    updatedAt.value = data.updated_at || ''
  } catch (error) {
    console.error(error)
    ElMessage.error('加载设置失败')
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  const nextAccessKey = form.access_key.trim()

  if (form.access_protection_enabled && !accessKeyConfigured.value && !nextAccessKey) {
    ElMessage.warning('开启访问保护前，请先设置访问密钥')
    return
  }

  saving.value = true
  try {
    await api.post('/settings/logs', {
      max_log_entries: form.max_log_entries,
      max_retention_days: form.max_retention_days,
      access_protection_enabled: form.access_protection_enabled,
      access_key: form.access_key,
    })

    if (nextAccessKey) {
      setAccessSession(nextAccessKey)
    }

    ElMessage.success('设置已保存')
    await loadSettings()
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.detail || '保存设置失败')
  } finally {
    saving.value = false
  }
}

onMounted(loadSettings)
</script>

<style scoped>
.settings-block-title {
  margin-bottom: 16px;
  font-size: 15px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.settings-block-spacing {
  margin-top: 8px;
}

.settings-inline-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.settings-help-text {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
</style>
