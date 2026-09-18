<template>
  <section class="settings-section-card">
    <div class="settings-section-header">
      <div>
        <h3 class="settings-section-title">青龙面板联动</h3>
        <p class="settings-section-desc">只读同步定时任务启用/禁用与 crontab；可自选自动或阻塞同步。</p>
      </div>
    </div>

    <el-form label-width="140px" class="settings-form" :disabled="props.disabled">
      <p class="settings-help-block">
        使用青龙「应用设置」里的 Client ID / Client Secret。 匹配规则：优先按任务名称与小程序名称对齐。
        推荐「自动同步」：后台定时刷新，打开小程序列表不会等待青龙接口。
      </p>

      <el-form-item label="青龙地址">
        <el-input
          :model-value="props.form.ql_base_url"
          placeholder="例如 http://192.168.1.10:5700（Docker 访问宿主机用 http://host.docker.internal:5700）"
          clearable
          @update:model-value="updateField('ql_base_url', $event)"
        />
      </el-form-item>
      <el-form-item label="Client ID">
        <el-input
          :model-value="props.form.ql_client_id"
          placeholder="应用 Client ID"
          clearable
          @update:model-value="updateField('ql_client_id', $event)"
        />
      </el-form-item>
      <el-form-item label="Client Secret">
        <el-input
          :model-value="props.form.ql_client_secret"
          type="password"
          show-password
          :placeholder="props.secretConfigured ? '已配置，留空表示不修改' : '应用 Client Secret'"
          @update:model-value="updateField('ql_client_secret', $event)"
        />
      </el-form-item>
      <el-form-item label="Secret 状态">
        <el-tag :type="props.secretConfigured ? 'success' : 'info'" round effect="plain">
          {{ props.secretConfigured ? '已配置' : '未配置' }}
        </el-tag>
      </el-form-item>
      <el-form-item label="同步方式">
        <div class="settings-sync-mode">
          <el-radio-group
            :model-value="props.form.ql_sync_mode"
            @update:model-value="updateField('ql_sync_mode', $event)"
          >
            <el-radio-button value="auto">自动同步</el-radio-button>
            <el-radio-button value="blocking">阻塞同步</el-radio-button>
            <el-radio-button value="manual">仅手动</el-radio-button>
          </el-radio-group>
          <p class="settings-help-text settings-sync-mode-hint">
            <template v-if="props.form.ql_sync_mode === 'auto'">
              后台按间隔刷新，打开小程序列表不阻塞（推荐）。
            </template>
            <template v-else-if="props.form.ql_sync_mode === 'blocking'">
              打开小程序列表且数据过期时，会等待青龙同步完成再返回（可能数秒）。
            </template>
            <template v-else>不自动刷新，只在点击「立即同步」时拉取。</template>
          </p>
        </div>
      </el-form-item>
      <el-form-item v-if="props.form.ql_sync_mode !== 'manual'" label="同步间隔">
        <div class="settings-inline-field">
          <el-input-number
            :model-value="props.form.ql_auto_sync_minutes"
            :min="1"
            :max="1440"
            :step="1"
            controls-position="right"
            @update:model-value="updateField('ql_auto_sync_minutes', $event)"
          />
          <span class="settings-help-text">分钟（1–1440，默认 5）</span>
        </div>
      </el-form-item>
      <el-form-item label="最近同步">
        <div class="settings-sync-meta">
          <span>{{ props.lastSyncAt || '暂无' }}</span>
          <span class="settings-help-text">{{ props.lastSyncStatus || '尚未同步' }}</span>
        </div>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="props.saving" :disabled="props.disabled" @click="emit('save')">
          保存青龙配置
        </el-button>
        <el-button type="success" plain :loading="props.syncing" :disabled="props.disabled" @click="emit('sync')">
          立即同步
        </el-button>
      </el-form-item>
    </el-form>
  </section>
</template>

<script setup>
const props = defineProps({
  form: {
    type: Object,
    default: () => ({}),
  },
  secretConfigured: {
    type: Boolean,
    default: false,
  },
  lastSyncAt: {
    type: String,
    default: '',
  },
  lastSyncStatus: {
    type: String,
    default: '',
  },
  saving: {
    type: Boolean,
    default: false,
  },
  syncing: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update-field', 'save', 'sync'])

function updateField(field, value) {
  emit('update-field', field, value)
}
</script>

<style scoped>
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

.settings-help-block {
  margin: 0 0 16px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.settings-help-text {
  color: var(--el-text-color-secondary);
  font-size: 13px;
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

.settings-sync-mode {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.settings-sync-mode-hint {
  margin: 0;
  line-height: 1.5;
}
</style>
