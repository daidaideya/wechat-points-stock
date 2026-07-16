<template>
  <div class="page-stack settings-page">
    <section class="toolbar-card settings-shell">
      <div class="settings-shell-head">
        <div>
          <h2 class="section-title">系统设置</h2>
          <p class="section-description">基础配置、青龙联动、Bark 推送与数据备份分栏管理。</p>
        </div>
        <el-button text @click="refreshCurrentSection">刷新当前页</el-button>
      </div>

      <div class="settings-layout">
        <aside class="settings-nav-panel">
          <div class="settings-nav-title">设置导航</div>
          <button
            v-for="item in navItems"
            :key="item.key"
            type="button"
            class="settings-nav-item"
            :class="{ active: activeSection === item.key }"
            @click="activeSection = item.key"
          >
            <span class="settings-nav-icon" aria-hidden="true">{{ item.icon }}</span>
            <span class="settings-nav-copy">
              <strong>{{ item.label }}</strong>
              <small>{{ item.desc }}</small>
            </span>
          </button>
        </aside>

        <div class="settings-content-panel">
          <el-skeleton v-if="loading" :rows="8" animated />

          <template v-else>
            <section v-if="activeSection === 'general'" class="settings-section-card">
              <div class="settings-section-header">
                <div>
                  <h3 class="settings-section-title">基础设置</h3>
                  <p class="settings-section-desc">日志清理策略与访问保护。</p>
                </div>
              </div>

              <el-form label-width="140px" class="settings-form">
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
            </section>

            <section v-else-if="activeSection === 'qinglong'" class="settings-section-card">
              <div class="settings-section-header">
                <div>
                  <h3 class="settings-section-title">青龙面板联动</h3>
                  <p class="settings-section-desc">只读同步定时任务启用/禁用状态与 crontab 规则；配置后后台自动刷新。</p>
                </div>
              </div>

              <el-form label-width="140px" class="settings-form">
                <p class="settings-help-block">
                  使用青龙「应用设置」里的 Client ID / Client Secret。
                  匹配规则：优先按任务名称与小程序名称对齐。
                  配置完整后会按下方「自动同步间隔」后台刷新；打开小程序列表过期时也会异步刷新。一般无需点「立即同步」。
                </p>

                <el-form-item label="青龙地址">
                  <el-input
                    v-model="qlForm.ql_base_url"
                    placeholder="例如 http://192.168.1.10:5700（Docker 访问宿主机用 http://host.docker.internal:5700）"
                    clearable
                  />
                </el-form-item>
                <el-form-item label="Client ID">
                  <el-input v-model="qlForm.ql_client_id" placeholder="应用 Client ID" clearable />
                </el-form-item>
                <el-form-item label="Client Secret">
                  <el-input
                    v-model="qlForm.ql_client_secret"
                    type="password"
                    show-password
                    :placeholder="qlSecretConfigured ? '已配置，留空表示不修改' : '应用 Client Secret'"
                  />
                </el-form-item>
                <el-form-item label="Secret 状态">
                  <el-tag :type="qlSecretConfigured ? 'success' : 'info'" round effect="plain">
                    {{ qlSecretConfigured ? '已配置' : '未配置' }}
                  </el-tag>
                </el-form-item>
                <el-form-item label="自动同步间隔">
                  <div class="settings-inline-field">
                    <el-input-number
                      v-model="qlForm.ql_auto_sync_minutes"
                      :min="1"
                      :max="1440"
                      :step="1"
                      controls-position="right"
                    />
                    <span class="settings-help-text">分钟（1–1440，默认 5）</span>
                  </div>
                </el-form-item>
                <el-form-item label="最近同步">
                  <div class="settings-sync-meta">
                    <span>{{ qlLastSyncAtLocal || formatDate(qlLastSyncAt) }}</span>
                    <span class="settings-help-text">{{ qlLastSyncStatus || '尚未同步' }}</span>
                  </div>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveQinglong" :loading="qlSaving">保存青龙配置</el-button>
                  <el-button type="success" plain @click="syncQinglong" :loading="qlSyncing">立即同步</el-button>
                </el-form-item>
              </el-form>
            </section>

            <section v-else-if="activeSection === 'bark'" class="settings-section-card">
              <div class="settings-section-header">
                <div>
                  <h3 class="settings-section-title">Bark 推送</h3>
                  <p class="settings-section-desc">按设定时间推送今日未上报的小程序列表到 iPhone。</p>
                </div>
              </div>

              <el-form label-width="140px" class="settings-form">
                <p class="settings-help-block">
                  填写 Bark 的 Device Key 后启用。服务会在每天设定时间检查活跃小程序是否已上报，
                  并把未报名单推送到你的手机。可随时关闭。
                </p>

                <el-form-item label="启用推送">
                  <div class="settings-inline-row">
                    <el-switch v-model="barkForm.bark_enabled" />
                    <span class="settings-help-text">关闭后不会自动推送，仍可手动测试</span>
                  </div>
                </el-form-item>
                <el-form-item label="Bark 服务器">
                  <el-input
                    v-model="barkForm.bark_server"
                    placeholder="默认 https://api.day.app，也可填自建地址"
                    clearable
                  />
                </el-form-item>
                <el-form-item label="Device Key">
                  <el-input
                    v-model="barkForm.bark_device_key"
                    type="password"
                    show-password
                    :placeholder="barkKeyConfigured ? '已配置，留空表示不修改' : 'Bark App 里的设备 Key'"
                  />
                </el-form-item>
                <el-form-item label="Key 状态">
                  <el-tag :type="barkKeyConfigured ? 'success' : 'info'" round effect="plain">
                    {{ barkKeyConfigured ? '已配置' : '未配置' }}
                  </el-tag>
                </el-form-item>
                <el-form-item label="推送时间">
                  <el-time-select
                    v-model="barkForm.bark_push_time"
                    start="00:00"
                    step="00:05"
                    end="23:55"
                    placeholder="选择时间"
                    style="width: 180px"
                  />
                  <span class="settings-help-text" style="margin-left: 10px">本地时间，每天一次</span>
                </el-form-item>
                <el-form-item label="最近推送">
                  <div class="settings-sync-meta">
                    <span>{{ barkLastPushAtLocal || formatDate(barkLastPushAt) }}</span>
                    <span class="settings-help-text">{{ barkLastPushStatus || '尚未推送' }}</span>
                  </div>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveBark" :loading="barkSaving">保存 Bark 配置</el-button>
                  <el-button type="success" plain @click="testBark" :loading="barkTesting">立即推送测试</el-button>
                </el-form-item>
              </el-form>
            </section>

            <section v-else class="settings-section-card">
              <div class="settings-section-header">
                <div>
                  <h3 class="settings-section-title">数据库备份 / 恢复</h3>
                  <p class="settings-section-desc">导出备份，或从备份文件恢复当前 SQLite 数据库。</p>
                </div>
              </div>

              <el-form label-width="140px" class="settings-form">
                <p class="settings-help-block">
                  导出当前 SQLite 数据库作为备份；导入会完整替换现有数据。导入前请先导出一份备份。
                  导入成功后会在数据库旁保留 <code>.pre_restore</code> 回滚副本。
                </p>
                <el-form-item label="备份导出">
                  <el-button type="primary" plain :loading="exporting" @click="exportDatabase">导出数据库</el-button>
                </el-form-item>
                <el-form-item label="备份恢复">
                  <div class="settings-inline-row">
                    <input
                      ref="importInputRef"
                      type="file"
                      accept=".db,application/x-sqlite3,application/octet-stream"
                      class="settings-file-input"
                      @change="onImportFileChange"
                    />
                    <el-button type="danger" plain :loading="importing" @click="triggerImport">选择文件并导入</el-button>
                  </div>
                </el-form-item>
              </el-form>
            </section>
          </template>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api, { setAccessSession } from '../api'

const route = useRoute()
const router = useRouter()

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
const importInputRef = ref(null)
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
  const key = String(value || '').trim().toLowerCase()
  if (navItems.some((item) => item.key === key)) return key
  return 'general'
}

function syncSectionFromRoute() {
  activeSection.value = normalizeSection(route.query.section)
}

async function loadSettings() {
  const { data } = await api.get('/settings/logs')
  form.max_log_entries = data.max_log_entries ?? 10000
  form.max_retention_days = data.max_retention_days ?? 30
  form.access_protection_enabled = Boolean(data.access_protection_enabled)
  form.access_key = ''
  accessKeyConfigured.value = Boolean(data.access_key_configured)
  updatedAt.value = data.updated_at || ''
}

async function loadQinglong() {
  const { data } = await api.get('/settings/qinglong')
  qlForm.ql_base_url = data.ql_base_url || ''
  qlForm.ql_client_id = data.ql_client_id || ''
  qlForm.ql_client_secret = ''
  const minutes = Number(data.ql_auto_sync_minutes)
  qlForm.ql_auto_sync_minutes = Number.isFinite(minutes) && minutes > 0 ? minutes : 5
  qlSecretConfigured.value = Boolean(data.ql_client_secret_configured)
  qlLastSyncAt.value = data.ql_last_sync_at || ''
  qlLastSyncAtLocal.value = data.ql_last_sync_at_local || formatDate(data.ql_last_sync_at) || ''
  qlLastSyncStatus.value = data.ql_last_sync_status || ''
}

async function loadBark() {
  const { data } = await api.get('/settings/bark')
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
  loading.value = true
  try {
    await Promise.all([loadSettings(), loadQinglong(), loadBark()])
  } catch (error) {
    console.error(error)
    ElMessage.error('加载设置失败')
  } finally {
    loading.value = false
  }
}

async function refreshCurrentSection() {
  loading.value = true
  try {
    if (activeSection.value === 'qinglong') {
      await loadQinglong()
    } else if (activeSection.value === 'bark') {
      await loadBark()
    } else if (activeSection.value === 'general') {
      await loadSettings()
    } else {
      // database section has no remote config to load
      await Promise.resolve()
    }
    ElMessage.success('已刷新')
  } catch (error) {
    console.error(error)
    ElMessage.error('刷新失败')
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

async function saveQinglong() {
  qlSaving.value = true
  try {
    const minutes = Number(qlForm.ql_auto_sync_minutes)
    if (!Number.isFinite(minutes) || minutes < 1 || minutes > 1440) {
      ElMessage.warning('自动同步间隔请填 1–1440 分钟')
      return
    }
    const payload = {
      ql_base_url: qlForm.ql_base_url,
      ql_client_id: qlForm.ql_client_id,
      ql_auto_sync_minutes: Math.round(minutes),
    }
    if (qlForm.ql_client_secret.trim()) {
      payload.ql_client_secret = qlForm.ql_client_secret.trim()
    }
    await api.post('/settings/qinglong', payload)
    ElMessage.success('青龙配置已保存')
    await loadQinglong()
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.detail || '保存青龙配置失败')
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
    const detail = error?.response?.data?.message || error?.response?.data?.detail || '同步青龙失败'
    ElMessage.error(detail)
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
    ElMessage.error(error?.response?.data?.detail || '保存 Bark 配置失败')
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
    const detail = error?.response?.data?.message || error?.response?.data?.detail || '推送失败'
    ElMessage.error(detail)
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

function triggerImport() {
  importInputRef.value?.click()
}

async function onImportFileChange(event) {
  const file = event?.target?.files?.[0]
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
    if (importInputRef.value) importInputRef.value.value = ''
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
    ElMessage.error(error?.response?.data?.detail || '导入数据库失败')
  } finally {
    importing.value = false
    if (importInputRef.value) importInputRef.value.value = ''
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

.settings-nav-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255, 250, 242, 0.98), rgba(255, 246, 234, 0.92));
  border: 1px solid rgba(232, 210, 184, 0.9);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.settings-nav-title {
  margin-bottom: 4px;
  padding: 0 6px;
  color: #8b5e34;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.settings-nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px;
  border: 0;
  border-radius: 14px;
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: background 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.settings-nav-item:hover {
  background: rgba(255, 255, 255, 0.72);
}

.settings-nav-item.active {
  background: #fff;
  box-shadow: 0 10px 20px rgba(180, 132, 72, 0.12);
  transform: translateY(-1px);
}

.settings-nav-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  background: rgba(255, 244, 221, 0.95);
  flex: 0 0 auto;
}

.settings-nav-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.settings-nav-copy strong {
  color: #3f2a18;
  font-size: 14px;
  font-weight: 700;
}

.settings-nav-copy small {
  color: #9b7e5c;
  font-size: 12px;
  line-height: 1.35;
}

.settings-content-panel {
  min-width: 0;
}

.settings-section-card {
  padding: 18px 18px 8px;
  border-radius: 18px;
  background: rgba(255, 253, 249, 0.96);
  border: 1px solid rgba(236, 220, 196, 0.95);
  box-shadow: 0 8px 18px rgba(126, 98, 63, 0.05);
}

.settings-section-header {
  margin-bottom: 8px;
}

.settings-section-title {
  margin: 0;
  color: #2f2418;
  font-size: 18px;
  font-weight: 700;
}

.settings-section-desc {
  margin: 6px 0 0;
  color: #8a6c4c;
  font-size: 13px;
  line-height: 1.5;
}

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

.settings-help-block {
  margin: 0 0 16px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.settings-sync-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.settings-inline-field {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.settings-file-input {
  display: none;
}

@media (max-width: 960px) {
  .settings-layout {
    grid-template-columns: 1fr;
  }

  .settings-nav-panel {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }

  .settings-nav-title {
    grid-column: 1 / -1;
  }

  .settings-nav-item {
    flex-direction: column;
    align-items: flex-start;
    min-height: 88px;
  }
}

@media (max-width: 640px) {
  .settings-shell-head {
    flex-direction: column;
  }

  .settings-nav-panel {
    grid-template-columns: 1fr;
  }

  .settings-nav-item {
    flex-direction: row;
    min-height: auto;
  }
}
</style>
