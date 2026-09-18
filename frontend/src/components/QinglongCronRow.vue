<template>
  <div
    class="ql-cron-row"
    :class="{
      disabled: props.cron.is_disabled === 1,
      crowded: props.crowded,
      sparse: props.sparse,
      excluded: props.excluded,
    }"
  >
    <div class="ql-cron-main">
      <div class="ql-cron-name-row">
        <span class="ql-cron-name">{{ props.cron.name || '(未命名)' }}</span>
        <el-tag v-if="props.cron.is_disabled === 1" size="small" type="danger" effect="plain">已禁用</el-tag>
        <el-tag v-if="props.excluded" size="small" type="info" effect="plain">已排除</el-tag>
        <el-tag v-if="props.crowded" size="small" type="warning" effect="plain">
          间隔 {{ props.minuteGap }} 分钟
        </el-tag>
        <el-tag v-else-if="props.sparse" size="small" type="success" effect="plain">
          间隔 {{ props.minuteGap }} 分钟
        </el-tag>
      </div>
      <div class="ql-cron-command">{{ props.cron.command }}</div>
    </div>
    <div class="ql-cron-schedule">
      <div class="ql-cron-times">
        <el-tag v-for="timeText in props.cron.displayTimes" :key="timeText" size="small" round effect="plain">
          {{ timeText }}
        </el-tag>
        <el-tag v-if="props.cron.hasMoreTimes" size="small" round effect="plain" type="info">
          +{{ props.cron.moreTimesCount }}
        </el-tag>
      </div>
      <div class="ql-cron-raw">{{ props.cron.schedule }}</div>
    </div>
    <div class="ql-cron-actions">
      <el-button size="small" text type="primary" @click="handleEdit">修改时间</el-button>
      <el-button size="small" text :type="props.excluded ? 'warning' : 'info'" @click="handleToggleExclude">
        {{ props.excluded ? '取消排除' : '排除' }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  cron: {
    type: Object,
    default: () => ({}),
  },
  excluded: {
    type: Boolean,
    default: false,
  },
  crowded: {
    type: Boolean,
    default: false,
  },
  sparse: {
    type: Boolean,
    default: false,
  },
  minuteGap: {
    type: [Number, String],
    default: '-',
  },
})

const emit = defineEmits(['edit', 'toggle-exclude'])

function handleEdit() {
  emit('edit', props.cron)
}

function handleToggleExclude() {
  emit('toggle-exclude', props.cron)
}
</script>

<style scoped>
.ql-cron-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 14px;
  background: var(--el-bg-color);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.ql-cron-row:hover {
  border-color: var(--warm-accent-strong, #e7b35a);
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
}

.ql-cron-row.crowded {
  border-color: var(--el-color-warning-light-5);
  background: var(--el-color-warning-light-9);
}

.ql-cron-row.sparse {
  border-color: var(--el-color-success-light-5);
  background: var(--el-color-success-light-9);
}

.ql-cron-row.disabled {
  opacity: 0.55;
}

.ql-cron-row.excluded {
  background: var(--el-fill-color-light);
  border-style: dashed;
}

.ql-cron-row.excluded .ql-cron-name {
  color: var(--el-text-color-secondary);
  text-decoration: line-through;
  text-decoration-color: var(--el-color-info-light-5);
}

.ql-cron-main {
  flex: 1;
  min-width: 0;
}

.ql-cron-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.ql-cron-name {
  font-weight: 600;
}

.ql-cron-command {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ql-cron-schedule {
  flex: 0 0 auto;
  text-align: right;
}

.ql-cron-times {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.ql-cron-raw {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

@media (max-width: 768px) {
  .ql-cron-row {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .ql-cron-schedule {
    text-align: left;
  }

  .ql-cron-times {
    justify-content: flex-start;
  }

  .ql-cron-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
  }
}

@media (max-width: 480px) {
  .ql-cron-name-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .ql-cron-times :deep(.el-tag) {
    font-size: 10px;
    padding: 2px 6px;
  }
}
</style>
