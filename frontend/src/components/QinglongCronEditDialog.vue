<template>
  <el-dialog
    :model-value="modelValue"
    title="修改执行时间"
    :width="isMobile ? '92%' : '480px'"
    :top="isMobile ? '5vh' : '15vh'"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div v-if="cron" class="ql-edit-dialog">
      <div class="ql-edit-name">{{ cron.name }}</div>
      <div class="ql-edit-command">{{ cron.command }}</div>
      <el-input
        id="ql-edit-schedule"
        :model-value="schedule"
        aria-label="Cron 执行表达式"
        aria-describedby="ql-edit-schedule-help"
        placeholder="如 59 14,21 * * *"
        @update:model-value="emit('update:schedule', $event)"
      />
      <div id="ql-edit-schedule-help" class="ql-edit-preview" role="status" aria-live="polite">
        <span v-if="previewTimes.length">每日执行：{{ previewTimes.join('、') }}</span>
        <span v-else class="ql-edit-invalid">无法解析该表达式（支持 分 时 * * *）</span>
      </div>
    </div>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="applying" :disabled="!previewTimes.length" @click="emit('save')">
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  isMobile: { type: Boolean, default: false },
  cron: { type: Object, default: null },
  schedule: { type: String, default: '' },
  previewTimes: { type: Array, default: () => [] },
  applying: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'update:schedule', 'save'])
</script>

<style scoped>
.ql-edit-dialog {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ql-edit-name {
  font-weight: 600;
}

.ql-edit-command {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.ql-edit-preview {
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.ql-edit-invalid {
  color: var(--el-color-danger);
}
</style>
