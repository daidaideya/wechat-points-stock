<template>
  <el-dialog
    v-model="dialogModel"
    :title="props.title"
    width="900px"
    class="users-points-dialog"
    @closed="emit('closed')"
  >
    <div v-if="props.loading" role="status" aria-live="polite" aria-busy="true" aria-label="正在加载积分详情">
      <el-skeleton :rows="6" animated />
    </div>
    <template v-else>
      <el-empty v-if="!props.items.length" description="暂无积分详情" />
      <div v-else class="users-points-mobile-list">
        <article
          v-for="point in props.items"
          :key="`${point.program_name}-${point.report_time}`"
          class="users-points-mobile-card"
        >
          <div class="users-points-mobile-top">
            <strong class="users-points-mobile-title">{{ point.program_name || '未知小程序' }}</strong>
            <span class="users-points-mobile-value">
              {{ formatPointsCell(point.points) }} 积分
              <template v-if="point.cash != null && point.cash !== '未注册'"> · ¥{{ point.cash }}</template>
            </span>
          </div>
          <div class="users-points-mobile-meta">
            <span>积分变化：{{ point.diff ?? 0 }}</span>
            <span>现金变化：{{ point.cash_diff ?? 0 }}</span>
            <span>{{ formatDate(point.report_time) }}</span>
          </div>
        </article>
      </div>
      <div class="users-points-desktop-table-wrap">
        <el-table :data="props.items" stripe class="users-points-table">
          <el-table-column prop="program_name" label="小程序" min-width="200" />
          <el-table-column label="积分" width="110">
            <template #default="scope">{{ formatPointsCell(scope.row.points) }}</template>
          </el-table-column>
          <el-table-column label="现金" width="110">
            <template #default="scope">{{ formatCashCell(scope.row.cash) }}</template>
          </el-table-column>
          <el-table-column prop="diff" label="积分变化" width="100" />
          <el-table-column prop="cash_diff" label="现金变化" width="100" />
          <el-table-column label="更新时间" min-width="180">
            <template #default="scope">{{ formatDate(scope.row.report_time) }}</template>
          </el-table-column>
        </el-table>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'
import { formatApiDate as formatDate } from '../utils/date'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '积分详情',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  items: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:modelValue', 'closed'])

const dialogModel = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

function formatPointsCell(value) {
  if (value === '未注册') return '未注册'
  if (value === null || value === undefined || value === '') return '—'
  return value
}

function formatCashCell(value) {
  if (value === '未注册') return '未注册'
  if (value === null || value === undefined || value === '') return '—'
  return `¥${value}`
}
</script>

<style scoped>
.users-points-desktop-table-wrap {
  display: block;
}

.users-points-mobile-list {
  display: none;
}

.users-points-dialog :deep(.el-dialog) {
  border-radius: 24px;
}

.users-points-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.users-points-table :deep(th.el-table__cell) {
  background: rgba(255, 248, 238, 0.9);
  color: #8a6c4c;
}

.users-points-table :deep(td.el-table__cell) {
  background: rgba(255, 253, 249, 0.96);
}

@media (max-width: 900px) {
  .users-points-desktop-table-wrap {
    display: none;
  }

  .users-points-mobile-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .users-points-mobile-card {
    padding: 16px;
    border-radius: 20px;
    background: #fffdf9;
    border: 1px solid rgba(232, 211, 183, 0.9);
    box-shadow: 0 10px 24px rgba(145, 109, 61, 0.06);
  }

  .users-points-mobile-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
  }

  .users-points-mobile-title {
    margin: 0;
    color: #3a2b1a;
    font-size: 18px;
    line-height: 1.35;
  }

  .users-points-mobile-value {
    color: #b87718;
    font-size: 14px;
    font-weight: 700;
    white-space: nowrap;
  }

  .users-points-mobile-meta {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-top: 6px;
    color: #8a6c4c;
    font-size: 12px;
    line-height: 1.6;
    word-break: break-all;
  }
}

@media (max-width: 640px) {
  .users-points-mobile-top {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
