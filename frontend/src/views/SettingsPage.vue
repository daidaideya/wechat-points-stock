<template>
  <div class="page-stack settings-page">
    <section class="toolbar-card settings-shell">
      <div class="settings-shell-head">
        <div>
          <h2 class="section-title">系统设置</h2>
          <p class="section-description">基础配置、青龙联动、Bark 推送与数据备份分栏管理。</p>
        </div>
        <el-button text :loading="loading" :disabled="settingsBusy" @click="refreshCurrentSection">
          刷新当前页
        </el-button>
      </div>

      <div class="settings-layout">
        <SettingsSectionNav v-model="activeSection" :items="navItems" :disabled="settingsBusy" />

        <div class="settings-content-panel">
          <el-skeleton v-if="loading" :rows="8" animated />

          <template v-else>
            <SettingsGeneralSection
              v-if="activeSection === 'general'"
              :form="form"
              :access-key-configured="accessKeyConfigured"
              :updated-at="formatDate(updatedAt)"
              :saving="saving"
              :disabled="settingsBusy"
              @update-field="updateGeneralField"
              @save="saveSettings"
            />

            <SettingsQinglongSection
              v-else-if="activeSection === 'qinglong'"
              :form="qlForm"
              :secret-configured="qlSecretConfigured"
              :last-sync-at="qlLastSyncAtLocal || formatDate(qlLastSyncAt)"
              :last-sync-status="qlLastSyncStatus"
              :saving="qlSaving"
              :syncing="qlSyncing"
              :disabled="settingsBusy"
              @update-field="updateQinglongField"
              @save="saveQinglong"
              @sync="syncQinglong"
            />

            <SettingsBarkSection
              v-else-if="activeSection === 'bark'"
              :form="barkForm"
              :key-configured="barkKeyConfigured"
              :last-push-at="barkLastPushAtLocal || formatDate(barkLastPushAt)"
              :last-push-status="barkLastPushStatus"
              :saving="barkSaving"
              :testing="barkTesting"
              :disabled="settingsBusy"
              @update-field="updateBarkField"
              @save="saveBark"
              @test="testBark"
            />

            <SettingsDatabaseSection
              v-else
              :exporting="exporting"
              :importing="importing"
              :disabled="settingsBusy"
              @export="exportDatabase"
              @import-file="onImportFileChange"
            />
          </template>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { useAccessSession } from '../composables/useAccessSession'
import { useAbortableRequest } from '../composables/useAbortableRequest'
import SettingsDatabaseSection from '../components/SettingsDatabaseSection.vue'
import SettingsBarkSection from '../components/SettingsBarkSection.vue'
import SettingsGeneralSection from '../components/SettingsGeneralSection.vue'
import SettingsSectionNav from '../components/SettingsSectionNav.vue'
import SettingsQinglongSection from '../components/SettingsQinglongSection.vue'
import { getApiErrorMessage, isRequestCanceled } from '../utils/apiError'

const route = useRoute()
const router = useRouter()
const { clearAccessSession } = useAccessSession()
const readRequestController = useAbortableRequest()

const navItems = [
  { key: 'general', label: '基础设置', desc: '日志清理 / 访问保护', icon: '⚙️' },
  { key: 'qinglong', label: '青龙联动', desc: '任务状态 / 定时规则', icon: '🐉' },
  { key: 'bark', label: 'Bark 推送', desc: '未报小程序提醒', icon: '🔔' },
  { key: 'database', label: '数据备份', desc: '导出 / 导入数据库', icon: '💾' },
]

const activeSection = ref('general')
const loading = ref(false)
const saving = ref(false)
const qlSaving = ref(false)
const qlSyncing = ref(false)
const barkSaving = ref(false)
const barkTesting = ref(false)
const exporting = ref(false)
const importing = ref(false)
const settingsBusy = computed(
  () =>
    loading.value ||
    saving.value ||
    qlSaving.value ||
    qlSyncing.value ||
    barkSaving.value ||
    barkTesting.value ||
    exporting.value ||
    importing.value,
)
const updatedAt = ref('')
const accessKeyConfigured = ref(false)
const qlSecretConfigured = ref(false)
const qlLastSyncAt = ref('')
const qlLastSyncAtLocal = ref('')
const qlLastSyncStatus = ref('')
const barkKeyConfigured = ref(false)
const barkLastPushAt = ref('')
const barkLastPushAtLocal = ref('')
const barkLastPushStatus = ref('')

const form = reactive({
  max_log_entries: 10000,
  max_retention_days: 30,
  access_protection_enabled: false,
  access_key: '',
})

const qlForm = reactive({
  ql_base_url: '',
  ql_client_id: '',
  ql_client_secret: '',
  ql_auto_sync_minutes: 5,
  ql_sync_mode: 'auto',
})

const barkForm = reactive({
  bark_enabled: false,
  bark_server: 'https://api.day.app',
  bark_device_key: '',
  bark_push_time: '20:00',
})

function parseApiDate(value) {
  if (!value) return null
  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value
  }
  // Backend historically stores naive utcnow(); ISO without offset must be treated as UTC.
  // e.g. "2026-07-16T16:33:45" → UTC → Asia/Shanghai 00:33
  let raw = String(value).trim()
  if (/^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?(\.\d+)?$/.test(raw)) {
    raw = raw.replace(' ', 'T')
    if (!raw.endsWith('Z')) raw = `${raw}Z`
  }
  const date = new Date(raw)
  return Number.isNaN(date.getTime()) ? null : date
}

function formatDate(value) {
  if (!value) return '暂无'
  const date = parseApiDate(value)
  if (!date) return String(value)
  // Always show China wall time — do not depend on OS/browser/Docker TZ.
  return date.toLocaleString('zh-CN', {
    hour12: false,
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function normalizeSection(value) {
  const key = String(value || '')
    .trim()
    .toLowerCase()
  if (navItems.some((item) => item.key === key)) return key
  return 'general'
}

function syncSectionFromRoute() {
  activeSection.value = normalizeSection(route.query.section)
}

async function loadSettings(signal) {
  const { data } = await api.get('/settings/logs', signal ? { signal } : undefined)
  form.max_log_entries = data.max_log_entries ?? 10000
  form.max_retention_days = data.max_retention_days ?? 30
  form.access_protection_enabled = Boolean(data.access_protection_enabled)
  form.access_key = ''
  accessKeyConfigured.value = Boolean(data.access_key_configured)
  updatedAt.value = data.updated_at || ''
}

function normalizeQlSyncMode(value) {
  const mode = String(value || '')
    .trim()
    .toLowerCase()
  if (mode === 'blocking' || mode === 'manual' || mode === 'auto') return mode
  return 'auto'
}

async function loadQinglong(signal) {
  const { data } = await api.get('/settings/qinglong', signal ? { signal } : undefined)
  qlForm.ql_base_url = data.ql_base_url || ''
  qlForm.ql_client_id = data.ql_client_id || ''
  qlForm.ql_client_secret = ''
  const minutes = Number(data.ql_auto_sync_minutes)
  qlForm.ql_auto_sync_minutes = Number.isFinite(minutes) && minutes > 0 ? minutes : 5
  qlForm.ql_sync_mode = normalizeQlSyncMode(data.ql_sync_mode)
  qlSecretConfigured.value = Boolean(data.ql_client_secret_configured)
  qlLastSyncAt.value = data.ql_last_sync_at || ''
  qlLastSyncAtLocal.value = data.ql_last_sync_at_local || formatDate(data.ql_last_sync_at) || ''
  qlLastSyncStatus.value = data.ql_last_sync_status || ''
}

async function loadBark(signal) {
  const { data } = await api.get('/settings/bark', signal ? { signal } : undefined)
  barkForm.bark_enabled = Boolean(data.bark_enabled)
  barkForm.bark_server = data.bark_server || 'https://api.day.app'
  barkForm.bark_device_key = ''
  barkForm.bark_push_time = data.bark_push_time || '20:00'
  barkKeyConfigured.value = Boolean(data.bark_device_key_configured)
  barkLastPushAt.value = data.bark_last_push_at || ''
  barkLastPushAtLocal.value = data.bark_last_push_at_local || formatDate(data.bark_last_push_at) || ''
  barkLastPushStatus.value = data.bark_last_push_status || ''
}
async function loadAll() {
  const request = readRequestController.start()
  loading.value = true
  try {
    await Promise.all([loadSettings(request.signal), loadQinglong(request.signal), loadBark(request.signal)])
    if (!request.isCurrent()) return
  } catch (error) {
    if (!request.isCurrent() || isRequestCanceled(error)) return
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '加载设置失败'))
  } finally {
    if (request.isCurrent()) {
      loading.value = false
      request.finish()
    }
  }
}

function updateGeneralField(field, value) {
  if (Object.prototype.hasOwnProperty.call(form, field)) form[field] = value
}

function updateQinglongField(field, value) {
  if (Object.prototype.hasOwnProperty.call(qlForm, field)) qlForm[field] = value
}

function updateBarkField(field, value) {
  if (Object.prototype.hasOwnProperty.call(barkForm, field)) barkForm[field] = value
}

async function refreshCurrentSection() {
  const request = readRequestController.start()
  loading.value = true
  try {
    if (activeSection.value === 'qinglong') {
      await loadQinglong(request.signal)
    } else if (activeSection.value === 'bark') {
      await loadBark(request.signal)
    } else if (activeSection.value === 'general') {
      await loadSettings(request.signal)
    } else {
      // database section has no remote config to load
      await Promise.resolve()
    }
    if (!request.isCurrent()) return
    ElMessage.success('已刷新')
  } catch (error) {
    if (!request.isCurrent() || isRequestCanceled(error)) return
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '刷新失败'))
  } finally {
    if (request.isCurrent()) {
      loading.value = false
      request.finish()
    }
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
      // Rotate the HttpOnly session when the access key changes. The key is
      // never persisted in localStorage by the new flow.
      await api.post('/access/verify', { access_key: nextAccessKey })
      clearAccessSession()
    } else {
      // This also migrates an older localStorage header to an HttpOnly cookie
      // and clears a stale cookie when protection was just disabled.
      await api.get('/access/status')
    }

    ElMessage.success('设置已保存')
    await loadSettings()
  } catch (error) {
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '保存设置失败'))
  } finally {
    saving.value = false
  }
}

async function saveQinglong() {
  qlSaving.value = true
  try {
    const mode = normalizeQlSyncMode(qlForm.ql_sync_mode)
    const minutes = Number(qlForm.ql_auto_sync_minutes)
    if (mode !== 'manual' && (!Number.isFinite(minutes) || minutes < 1 || minutes > 1440)) {
      ElMessage.warning('同步间隔请填 1–1440 分钟')
      return
    }
    const payload = {
      ql_base_url: qlForm.ql_base_url,
      ql_client_id: qlForm.ql_client_id,
      ql_sync_mode: mode,
      ql_auto_sync_minutes: Number.isFinite(minutes) && minutes > 0 ? Math.round(minutes) : 5,
    }
    if (qlForm.ql_client_secret.trim()) {
      payload.ql_client_secret = qlForm.ql_client_secret.trim()
    }
    await api.post('/settings/qinglong', payload)
    ElMessage.success('青龙配置已保存')
    await loadQinglong()
  } catch (error) {
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '保存青龙配置失败'))
  } finally {
    qlSaving.value = false
  }
}

async function syncQinglong() {
  qlSyncing.value = true
  try {
    const { data } = await api.post('/settings/qinglong/sync')
    if (data.status === 'success') {
      ElMessage.success(data.message || '同步成功')
    } else if (data.status === 'skipped') {
      ElMessage.warning(data.message || '未配置青龙，已跳过')
    } else {
      ElMessage.error(data.message || '同步失败')
    }
    await loadQinglong()
  } catch (error) {
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '同步青龙失败'))
    try {
      await loadQinglong()
    } catch (_) {
      /* ignore */
    }
  } finally {
    qlSyncing.value = false
  }
}

async function saveBark() {
  if (barkForm.bark_enabled && !barkKeyConfigured.value && !barkForm.bark_device_key.trim()) {
    ElMessage.warning('启用推送前请先填写 Device Key')
    return
  }
  barkSaving.value = true
  try {
    const payload = {
      bark_enabled: barkForm.bark_enabled,
      bark_server: barkForm.bark_server,
      bark_push_time: barkForm.bark_push_time,
    }
    if (barkForm.bark_device_key.trim()) {
      payload.bark_device_key = barkForm.bark_device_key.trim()
    }
    await api.post('/settings/bark', payload)
    ElMessage.success('Bark 配置已保存')
    await loadBark()
  } catch (error) {
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '保存 Bark 配置失败'))
  } finally {
    barkSaving.value = false
  }
}

async function testBark() {
  barkTesting.value = true
  try {
    const { data } = await api.post('/settings/bark/test')
    if (data.status === 'success') {
      ElMessage.success(data.message || '推送成功')
    } else if (data.status === 'skipped') {
      ElMessage.warning(data.message || '已跳过')
    } else {
      ElMessage.error(data.message || '推送失败')
    }
    await loadBark()
  } catch (error) {
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '推送失败'))
    try {
      await loadBark()
    } catch (_) {
      /* ignore */
    }
  } finally {
    barkTesting.value = false
  }
}

function filenameFromDisposition(headerValue) {
  if (!headerValue) return ''
  const utfMatch = /filename\*=UTF-8''([^;]+)/i.exec(headerValue)
  if (utfMatch?.[1]) {
    try {
      return decodeURIComponent(utfMatch[1])
    } catch (_) {
      return utfMatch[1]
    }
  }
  const plainMatch = /filename="?([^";]+)"?/i.exec(headerValue)
  return plainMatch?.[1] || ''
}

async function exportDatabase() {
  exporting.value = true
  try {
    const response = await api.get('/settings/database/export', {
      responseType: 'blob',
      timeout: 120000,
    })
    const blob = new Blob([response.data], { type: 'application/x-sqlite3' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')
    link.href = url
    link.download = filenameFromDisposition(response.headers?.['content-disposition']) || `database-backup-${stamp}.db`
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    ElMessage.success('数据库已导出')
  } catch (error) {
    console.error(error)
    let detail = '导出数据库失败'
    const data = error?.response?.data
    if (data instanceof Blob) {
      try {
        const text = await data.text()
        const parsed = JSON.parse(text)
        detail = parsed.detail || detail
      } catch (_) {
        /* ignore */
      }
    } else if (data?.detail) {
      detail = data.detail
    }
    ElMessage.error(detail)
  } finally {
    exporting.value = false
  }
}

async function onImportFileChange(file) {
  if (!file) return

  try {
    await ElMessageBox.confirm(
      `确定用「${file.name}」覆盖当前数据库吗？此操作不可撤销（会保留 .pre_restore 回滚副本）。建议先导出备份。`,
      '恢复数据库',
      {
        type: 'warning',
        confirmButtonText: '确认导入',
        cancelButtonText: '取消',
      },
    )
  } catch (_) {
    return
  }

  importing.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post('/settings/database/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 180000,
    })
    ElMessage.success(data?.message || '数据库已恢复，请刷新页面')
    setTimeout(() => {
      window.location.reload()
    }, 800)
  } catch (error) {
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '导入数据库失败'))
  } finally {
    importing.value = false
  }
}

watch(
  () => route.query.section,
  () => {
    syncSectionFromRoute()
  },
  { immediate: true },
)

watch(activeSection, (section) => {
  const normalized = normalizeSection(section)
  if (normalized !== section) {
    activeSection.value = normalized
    return
  }
  if (route.query.section === normalized) return
  router.replace({
    path: '/settings',
    query: { ...route.query, section: normalized },
  })
})

onMounted(loadAll)
</script>

<style scoped>
.settings-shell {
  padding: 20px;
}

.settings-shell-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.settings-layout {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.settings-content-panel {
  min-width: 0;
}

@media (max-width: 960px) {
  .settings-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .settings-shell-head {
    flex-direction: column;
  }
}
</style>
