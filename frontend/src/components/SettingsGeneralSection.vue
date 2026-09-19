<template>
  <SettingsSectionCard title="基础设置" description="日志清理策略与访问保护。">
    <el-form label-width="140px" class="settings-form" :disabled="props.disabled">
      <div class="settings-block-title">日志清理设置</div>
      <el-form-item label="最大日志条数">
        <el-input-number
          :model-value="props.form.max_log_entries"
          :min="0"
          :step="100"
          @update:model-value="updateField('max_log_entries', $event)"
        />
      </el-form-item>
      <el-form-item label="保留天数">
        <el-input-number
          :model-value="props.form.max_retention_days"
          :min="0"
          :step="1"
          @update:model-value="updateField('max_retention_days', $event)"
        />
      </el-form-item>

      <div class="settings-block-title settings-block-spacing">访问保护设置</div>
      <el-form-item label="启用访问密钥">
        <div class="settings-inline-row">
          <el-switch
            :model-value="props.form.access_protection_enabled"
            @update:model-value="updateField('access_protection_enabled', $event)"
          />
          <span class="settings-help-text">开启后，进入系统需先输入访问密钥</span>
        </div>
      </el-form-item>

      <el-form-item label="当前状态">
        <el-tag :type="props.form.access_protection_enabled ? 'warning' : 'info'" round effect="plain">
          {{ props.form.access_protection_enabled ? '已启用保护' : '未启用保护' }}
        </el-tag>
        <el-tag v-if="props.accessKeyConfigured" type="success" round effect="plain" class="status-tag-gap">
          已设置访问密钥
        </el-tag>
        <el-tag v-else type="danger" round effect="plain" class="status-tag-gap">未设置访问密钥</el-tag>
      </el-form-item>

      <el-form-item label="访问密钥">
        <el-input
          :model-value="props.form.access_key"
          type="password"
          show-password
          maxlength="100"
          placeholder="留空表示不修改；首次设置可直接输入"
          @update:model-value="updateField('access_key', $event)"
        />
      </el-form-item>

      <el-form-item label="最近更新时间">
        <span>{{ props.updatedAt }}</span>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="props.saving" :disabled="props.disabled" @click="emit('save')">
          保存设置
        </el-button>
      </el-form-item>
    </el-form>
  </SettingsSectionCard>
</template>

<script setup>
import SettingsSectionCard from './SettingsSectionCard.vue'

const props = defineProps({
  form: {
    type: Object,
    default: () => ({}),
  },
  accessKeyConfigured: {
    type: Boolean,
    default: false,
  },
  updatedAt: {
    type: String,
    default: '',
  },
  saving: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update-field', 'save'])

function updateField(field, value) {
  emit('update-field', field, value)
}
</script>

<style scoped>
.settings-block-title {
  margin-bottom: 16px;
  color: var(--el-text-color-primary);
  font-size: 15px;
  font-weight: 700;
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

.status-tag-gap {
  margin-left: 8px;
}
</style>
