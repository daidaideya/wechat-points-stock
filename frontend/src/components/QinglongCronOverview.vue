<template>
  <section class="toolbar-card ql-hero">
    <div class="ql-hero-head">
      <div>
        <div class="section-title">青龙定时</div>
        <p class="section-description">查看青龙脚本每日执行时间线，识别间隔过密的任务，并一键重排执行间隔。</p>
      </div>
      <div class="ql-hero-actions">
        <el-button :loading="props.loading" @click="emit('refresh')">
          <el-icon><RefreshRight /></el-icon>
          刷新数据
        </el-button>
      </div>
    </div>

    <div class="points-metrics-grid">
      <article class="points-metric-card tone-blue">
        <div class="points-metric-top">
          <div>
            <div class="points-metric-label">脚本任务</div>
            <div class="points-metric-value">{{ props.scriptCount }}</div>
          </div>
          <span class="points-metric-icon">
            <el-icon><Document /></el-icon>
          </span>
        </div>
        <div class="points-metric-foot">青龙面板中的全部脚本任务</div>
      </article>

      <article class="points-metric-card tone-green">
        <div class="points-metric-top">
          <div>
            <div class="points-metric-label">启用</div>
            <div class="points-metric-value">{{ props.enabledCount }}</div>
          </div>
          <span class="points-metric-icon">
            <el-icon><CircleCheck /></el-icon>
          </span>
        </div>
        <div class="points-metric-foot">参与时间线整理的任务数量</div>
      </article>

      <article class="points-metric-card tone-red">
        <div class="points-metric-top">
          <div>
            <div class="points-metric-label">已禁用</div>
            <div class="points-metric-value">{{ props.disabledCount }}</div>
          </div>
          <span class="points-metric-icon">
            <el-icon><CircleClose /></el-icon>
          </span>
        </div>
        <div class="points-metric-foot">已停用，不参与整理</div>
      </article>

      <article class="points-metric-card tone-amber ql-next-slot-card">
        <div class="points-metric-top">
          <div>
            <div class="points-metric-label">新脚本时间</div>
            <div class="points-metric-value ql-coverage-value">{{ props.nextSlotTime || '-' }}</div>
          </div>
          <span class="points-metric-icon">
            <el-icon><CopyDocument /></el-icon>
          </span>
        </div>
        <div class="points-metric-foot ql-next-slot-foot">
          <code class="ql-next-slot-code">{{ props.nextSlotSchedule || '暂无可复制的表达式' }}</code>
          <el-button
            size="small"
            type="primary"
            plain
            :disabled="!props.nextSlotSchedule"
            @click="emit('copy-next-slot')"
          >
            复制
          </el-button>
        </div>
        <div v-if="props.nextSlotLastSchedule" class="ql-next-slot-hint">
          基于最新脚本「{{ props.nextSlotLastName }}」{{ props.nextSlotLastSchedule }} +{{ props.intervalMinutes || 2 }}
          分钟
        </div>
      </article>
    </div>

    <div class="points-hero-meta">
      <span class="points-meta-chip">
        <el-icon><Search /></el-icon>
        <input
          class="ql-meta-search"
          type="text"
          placeholder="搜索名称 / 命令"
          :value="props.keyword"
          @input="emit('update:keyword', $event.target.value)"
        />
      </span>
      <span v-if="props.crowdedCount" class="points-meta-chip warning">
        <el-icon><Warning /></el-icon>
        {{ props.crowdedCount }} 个任务间隔小于 {{ props.intervalMinutes }} 分钟
      </span>
      <span v-if="props.excludedCount" class="points-meta-chip ql-excluded-meta-chip">
        <el-icon><Remove /></el-icon>
        黑名单 {{ props.excludedCount }} 个脚本
        <el-button link size="small" type="primary" class="ql-clear-excluded-btn" @click="emit('clear-excluded')">
          清空
        </el-button>
      </span>
    </div>

    <div class="ql-filter-row">
      <div class="ql-filter-label">
        <el-icon><Files /></el-icon>
        <span>脚本类型</span>
      </div>
      <div class="ql-filter-chips">
        <button
          v-for="item in filterItems"
          :key="item.value"
          type="button"
          class="ql-filter-chip"
          :class="{ active: props.commandTypeFilter === item.value }"
          @click="emit('update:command-type-filter', item.value)"
        >
          <span class="ql-filter-chip-dot"></span>
          {{ item.label }} {{ item.count }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import {
  CircleCheck,
  CircleClose,
  CopyDocument,
  Document,
  Files,
  RefreshRight,
  Remove,
  Search,
  Warning,
} from '@element-plus/icons-vue'

const props = defineProps({
  loading: { type: Boolean, default: false },
  scriptCount: { type: Number, default: 0 },
  enabledCount: { type: Number, default: 0 },
  disabledCount: { type: Number, default: 0 },
  nextSlotTime: { type: String, default: '' },
  nextSlotSchedule: { type: String, default: '' },
  nextSlotLastName: { type: String, default: '' },
  nextSlotLastSchedule: { type: String, default: '' },
  intervalMinutes: { type: Number, default: 2 },
  keyword: { type: String, default: '' },
  crowdedCount: { type: Number, default: 0 },
  excludedCount: { type: Number, default: 0 },
  commandTypeFilter: { type: String, default: 'code' },
  codeCount: { type: Number, default: 0 },
  otherCount: { type: Number, default: 0 },
})

const emit = defineEmits([
  'refresh',
  'copy-next-slot',
  'clear-excluded',
  'update:keyword',
  'update:command-type-filter',
])

const filterItems = computed(() => [
  { value: 'all', label: '全部脚本', count: props.scriptCount },
  { value: 'code', label: 'code 版', count: props.codeCount },
  { value: 'other', label: '其他命令', count: props.otherCount },
])
</script>

<style scoped>
.ql-hero-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.ql-hero-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ql-coverage-value {
  font-size: 24px;
  line-height: 1.35;
  padding-top: 6px;
}

.ql-next-slot-foot {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.ql-next-slot-code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  padding: 4px 8px;
  color: var(--el-text-color-regular);
  word-break: break-all;
}

.ql-next-slot-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 6px;
}

.ql-meta-search {
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  color: inherit;
  width: 180px;
  font-family: inherit;
}

.ql-meta-search::placeholder {
  color: var(--el-text-color-secondary);
}

.ql-filter-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.ql-filter-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  flex: 0 0 auto;
}

.ql-filter-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.ql-filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid rgba(226, 207, 181, 0.95);
  border-radius: 999px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.78);
  color: #7c6143;
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
  transition: all 0.22s ease;
  box-shadow: 0 6px 14px rgba(130, 100, 64, 0.05);
}

.ql-filter-chip:hover {
  transform: translateY(-1px);
  border-color: rgba(226, 175, 102, 0.95);
  background: rgba(255, 249, 241, 0.96);
  color: #9a6224;
  box-shadow: 0 10px 22px rgba(198, 146, 72, 0.14);
}

.ql-filter-chip-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(233, 184, 110, 0.95), rgba(216, 145, 58, 0.95));
  box-shadow: 0 0 0 4px rgba(244, 207, 157, 0.3);
}

.ql-filter-chip.active {
  border-color: transparent;
  background: linear-gradient(135deg, #f1c983, #df9f50);
  color: #fff;
}

.ql-filter-chip.active .ql-filter-chip-dot {
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.25);
}

.ql-excluded-meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.ql-clear-excluded-btn {
  margin-left: 4px;
  padding: 0 4px;
  height: auto;
  font-size: 12px;
}

@media (max-width: 900px) {
  .ql-hero-head {
    flex-direction: column;
  }

  .ql-hero-actions {
    width: 100%;
  }

  .ql-hero-actions .el-button {
    flex: 1;
  }

  .ql-meta-search {
    flex: 1;
    width: auto;
  }

  .ql-filter-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .ql-filter-chips {
    width: 100%;
  }

  .ql-filter-chip {
    flex: 1;
    min-width: 100px;
    justify-content: center;
    padding: 8px 10px;
    font-size: 12px;
  }

  .points-metrics-grid {
    grid-template-columns: repeat(2, 1fr) !important;
    gap: 10px !important;
  }

  .points-metric-card {
    padding: 12px !important;
  }

  .points-metric-value {
    font-size: 22px !important;
    margin-top: 4px !important;
  }

  .points-metric-icon {
    width: 40px !important;
    height: 40px !important;
    font-size: 18px !important;
    flex-basis: 40px !important;
  }

  .points-metric-foot {
    font-size: 11px !important;
    margin-top: 8px !important;
  }

  .points-hero-meta {
    flex-wrap: wrap;
  }

  .points-meta-chip {
    flex: 1;
    min-width: 140px;
  }

  .ql-excluded-meta-chip {
    min-width: 160px;
  }
}

@media (max-width: 480px) {
  .points-metrics-grid {
    grid-template-columns: 1fr 1fr !important;
  }

  .ql-filter-chip {
    min-width: 80px;
    padding: 6px 8px;
    font-size: 11px;
  }
}
</style>
