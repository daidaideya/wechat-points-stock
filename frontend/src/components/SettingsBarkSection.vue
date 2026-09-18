<template>
  <section class="settings-section-card">
    <div class="settings-section-header">
      <div>
        <h3 class="settings-section-title">Bark 推送</h3>
        <p class="settings-section-desc">按设定时间推送今日未上报的小程序列表到 iPhone。</p>
      </div>
    </div>

    <el-form label-width="140px" class="settings-form">
      <p class="settings-help-block">
        填写 Bark 的 Device Key 后启用。服务会在每天设定时间检查活跃小程序是否已上报，并把未报名单推送到你的手机。
        可随时关闭。
      </p>

      <el-form-item label="启用推送">
        <div class="settings-inline-row">
          <el-switch :model-value="props.form.bark_enabled" @update:model-value="updateField('bark_enabled', $event)" />
          <span class="settings-help-text">关闭后不会自动推送，仍可手动测试</span>
        </div>
      </el-form-item>
      <el-form-item label="Bark 服务器">
        <el-input
          :model-value="props.form.bark_server"
          placeholder="默认 https://api.day.app，也可填自建地址"
          clearable
          @update:model-value="updateField('bark_server', $event)"
        />
      </el-form-item>
      <el-form-item label="Device Key">
        <el-input
          :model-value="props.form.bark_device_key"
          type="password"
          show-password
          :placeholder="props.keyConfigured ? '已配置，留空表示不修改' : 'Bark App 里的设备 Key'"
          @update:model-value="updateField('bark_device_key', $event)"
        />
      </el-form-item>
      <el-form-item label="Key 状态">
        <el-tag :type="props.keyConfigured ? 'success' : 'info'" round effect="plain">
          {{ props.keyConfigured ? '已配置' : '未配置' }}
        </el-tag>
      </el-form-item>
      <el-form-item label="推送时间">
        <el-time-select
          :model-value="props.form.bark_push_time"
          start="00:00"
          step="00:05"
          end="23:55"
          placeholder="选择时间"
          style="width: 180px"
          @update:model-value="updateField('bark_push_time', $event)"
        />
        <span class="settings-help-text push-time-hint">本地时间，每天一次</span>
      </el-form-item>
      <el-form-item label="最近推送">
        <div class="settings-sync-meta">
          <span>{{ props.lastPushAt || '暂无' }}</span>
          <span class="settings-help-text">{{ props.lastPushStatus || '尚未推送' }}</span>
        </div>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="props.saving" @click="emit('save')">保存 Bark 配置</el-button>
        <el-button type="success" plain :loading="props.testing" @click="emit('test')">立即推送测试</el-button>
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
  keyConfigured: {
    type: Boolean,
    default: false,
  },
  lastPushAt: {
    type: String,
    default: '',
  },
  lastPushStatus: {
    type: String,
    default: '',
  },
  saving: {
    type: Boolean,
    default: false,
  },
  testing: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update-field', 'save', 'test'])

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

.push-time-hint {
  margin-left: 10px;
}

.settings-sync-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
</style>
