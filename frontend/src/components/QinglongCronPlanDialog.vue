<template>
  <el-dialog
    v-model="dialogVisible"
    title="整理预览"
    :width="isMobile ? '96%' : '860px'"
    :top="isMobile ? '2vh' : '8vh'"
    class="ql-plan-dialog"
  >
    <div class="ql-plan-summary" role="status" aria-live="polite">
      <span>
        上午 {{ planForm.startTime }} / 下午 {{ planForm.afternoonStartTime }}，间隔
        {{ planForm.intervalMinutes }} 分钟，共 {{ planItems.length }} 个{{
          planForm.codeOnly ? ' code 版' : '启用'
        }}脚本（每日 2 次）
      </span>
      <span v-if="planWindow">时间窗 {{ planWindow }}</span>
    </div>
    <el-table :data="planItems" max-height="480" size="small" class="ql-plan-table">
      <el-table-column label="脚本" min-width="220">
        <template #default="{ row }">
          <div class="ql-plan-name">{{ row.name }}</div>
          <div class="ql-plan-command">{{ row.command }}</div>
        </template>
      </el-table-column>
      <el-table-column label="当前" width="170">
        <template #default="{ row }">
          <div>{{ row.oldTime }}</div>
          <div class="ql-plan-raw">{{ row.oldSchedule }}</div>
        </template>
      </el-table-column>
      <el-table-column label="整理后" width="200">
        <template #default="{ row }">
          <div class="ql-plan-new">{{ row.newTime }}</div>
          <div class="ql-plan-raw">{{ row.newSchedule }}</div>
        </template>
      </el-table-column>
      <el-table-column label="变化" width="80" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.changed" size="small" type="warning" effect="plain">调整</el-tag>
          <el-tag v-else-if="row.applied" size="small" type="success" effect="plain">已应用</el-tag>
          <el-tag v-else size="small" type="info" effect="plain">不变</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="90" align="center">
        <template #default="{ row }">
          <el-button
            v-if="row.changed"
            size="small"
            text
            type="primary"
            :aria-label="`应用 ${row.name || '该脚本'}`"
            :loading="row.applying"
            @click="emitApplyItem(row)"
          >
            应用
          </el-button>
          <span v-else-if="row.applied" class="ql-plan-applied">已应用</span>
        </template>
      </el-table-column>
    </el-table>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="applying" @click="emitApply">应用到青龙</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  isMobile: { type: Boolean, default: false },
  planForm: { type: Object, required: true },
  planItems: { type: Array, default: () => [] },
  applying: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'apply', 'apply-item'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const planWindow = computed(() => {
  if (!props.planItems.length) return ''
  const first = props.planItems[0]?.newTime?.split(' / ')[0]
  const last = props.planItems[props.planItems.length - 1]?.newTime?.split(' / ')[0]
  return first && last ? `${first} ~ ${last}` : ''
})

function emitApply() {
  emit('apply')
}

function emitApplyItem(row) {
  emit('apply-item', row)
}
</script>

<style scoped>
.ql-plan-summary {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
  color: var(--el-text-color-regular);
  font-size: 13px;
}

.ql-plan-name {
  font-weight: 600;
}

.ql-plan-command,
.ql-plan-raw {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.ql-plan-new {
  color: var(--el-color-primary);
  font-weight: 600;
}

.ql-plan-applied {
  font-size: 12px;
  color: var(--el-color-success);
}

@media (max-width: 900px) {
  .ql-plan-table :deep(.el-table__cell) {
    padding: 8px 4px;
  }

  .ql-plan-summary {
    flex-direction: column;
    gap: 6px;
  }
}
</style>
