<template>
  <div v-if="hasAnyMetric(program)" class="showcase-card-stock-row">
    <button
      v-if="hasStockMetric(program)"
      type="button"
      class="stock-count-display stock-count-button"
      :title="'查看库存'"
      @click="handleOpenStock"
    >
      <span class="stock-count-icon">
        <el-icon><PriceTag /></el-icon>
      </span>
      <span class="stock-count-value">{{ formatProductCount(program) }}</span>
    </button>
    <span
      v-if="hasStockMetric(program) && (hasPointsMetric(program) || hasCashMetric(program))"
      class="stock-row-divider"
      aria-hidden="true"
    ></span>
    <div
      v-if="hasPointsMetric(program)"
      class="points-count-display"
      :title="`当前账号最高积分：${program.max_user_points}`"
    >
      <span class="points-count-icon">
        <el-icon><Coin /></el-icon>
      </span>
      <span class="points-count-value">{{ formatMaxPoints(program) }}</span>
    </div>
    <span v-if="hasPointsMetric(program) && hasCashMetric(program)" class="stock-row-divider" aria-hidden="true"></span>
    <div
      v-if="hasCashMetric(program)"
      class="points-count-display cash-count-display"
      :title="`当前账号最高现金：¥${program.max_user_cash}`"
    >
      <span class="points-count-icon cash-count-icon">
        <el-icon><Wallet /></el-icon>
      </span>
      <span class="points-count-value">{{ formatMaxCash(program) }}</span>
    </div>
    <div v-if="hasStockChange(program)" class="showcase-card-change-row inline-change-row">
      <span v-if="program.stock_change?.added_count" class="metric-change-chip metric-chip-success">
        +{{ program.stock_change.added_count }}
      </span>
      <span v-if="program.stock_change?.removed_count" class="metric-change-chip metric-chip-warning">
        -{{ program.stock_change.removed_count }}
      </span>
    </div>
    <span
      v-if="hasIncompleteStockSnapshot(program)"
      class="stock-snapshot-warning"
      role="status"
      aria-label="库存快照需复核"
      :title="getStockSnapshotWarning(program)"
    >
      库存快照需复核
    </span>
  </div>
</template>

<script setup>
import { toRef } from 'vue'
import { Coin, PriceTag, Wallet } from '@element-plus/icons-vue'

const props = defineProps({
  program: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['open-stock'])

function handleOpenStock() {
  emit('open-stock')
}

function formatProductCount(program) {
  const count = Number(program?.product_count) || 0
  return `${count}`
}

function formatMaxPoints(program) {
  const value = Number(program?.max_user_points) || 0
  if (value <= 0) return '0'
  if (value >= 10000) return `${(value / 10000).toFixed(value % 10000 === 0 ? 0 : 1)}w`
  if (value >= 1000) return `${(value / 1000).toFixed(value % 1000 === 0 ? 0 : 1)}k`
  return `${value}`
}

function formatMaxCash(program) {
  if (program?.max_user_cash == null || program.max_user_cash === '') return '—'
  const value = Number(program.max_user_cash)
  if (Number.isNaN(value)) return '—'
  if (value === 0) return '¥0'
  return `¥${value.toLocaleString('zh-CN', { maximumFractionDigits: 4 })}`
}

function hasStockMetric(program) {
  return Boolean(program?.has_stock) || Number(program?.product_count) > 0
}

function hasPointsMetric(program) {
  const value = Number(program?.max_user_points)
  return Number.isFinite(value) && value > 0
}

function hasCashMetric(program) {
  if (program?.max_user_cash == null || program.max_user_cash === '') return false
  const value = Number(program.max_user_cash)
  return Number.isFinite(value)
}

function hasAnyMetric(program) {
  return (
    hasStockMetric(program) ||
    hasPointsMetric(program) ||
    hasCashMetric(program) ||
    hasStockChange(program) ||
    hasIncompleteStockSnapshot(program)
  )
}

function hasStockChange(program) {
  return Boolean(
    (Number(program?.stock_change?.added_count) || 0) > 0 || (Number(program?.stock_change?.removed_count) || 0) > 0,
  )
}

function hasIncompleteStockSnapshot(program) {
  return Boolean(program?.stock_snapshot && program.stock_snapshot.is_complete === false)
}

function getStockSnapshotWarning(program) {
  const snapshot = program?.stock_snapshot
  if (snapshot?.status === 'partial') return '本次库存上报标记为不完整，未自动下架缺失商品'
  if (snapshot?.status === 'count_mismatch') {
    return `本次库存上报数量异常（${snapshot.reported_product_count ?? 0}/${snapshot.expected_product_count ?? 0}），未自动下架缺失商品`
  }
  if (snapshot?.status === 'empty') return '本次库存上报为空，未自动下架缺失商品'
  return '本次库存快照未通过完整性检查，未自动下架缺失商品'
}

const program = toRef(props, 'program')
</script>

<style scoped>
.showcase-card-stock-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.showcase-card-change-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}

.inline-change-row {
  margin-top: 0;
}

.stock-count-display {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  color: #7c5833;
}

.stock-count-button {
  border: 0;
  padding: 0;
  background: transparent;
  cursor: pointer;
  transition:
    transform 0.18s ease,
    opacity 0.18s ease;
}

.stock-count-button:hover {
  transform: translateY(-1px);
}

.stock-count-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.stock-count-button:focus-visible {
  outline: 2px solid rgba(223, 159, 80, 0.45);
  outline-offset: 4px;
  border-radius: 12px;
}

.stock-count-icon,
.points-count-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 999px;
}

.stock-count-icon {
  background: linear-gradient(135deg, rgba(255, 244, 221, 0.96), rgba(255, 237, 213, 0.9));
  color: #b7791f;
  box-shadow: inset 0 0 0 1px rgba(231, 202, 163, 0.72);
}

.stock-count-value,
.points-count-value {
  font-size: 22px;
  line-height: 1;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.stock-count-value {
  color: #a16207;
}

.cash-count-icon {
  background: linear-gradient(135deg, rgba(236, 253, 245, 0.96), rgba(209, 250, 229, 0.9));
  color: #047857;
  box-shadow: inset 0 0 0 1px rgba(110, 231, 183, 0.72);
}

.cash-count-display .points-count-value {
  color: #047857;
}

/* 最高积分指标，紧挨商品数量按钮，配色用蓝绿调与橙色商品块区分 */
.points-count-display {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  color: #1d6f6c;
}

.points-count-icon {
  background: linear-gradient(135deg, rgba(214, 240, 230, 0.96), rgba(189, 226, 220, 0.9));
  color: #0f766e;
  box-shadow: inset 0 0 0 1px rgba(155, 209, 198, 0.78);
}

.points-count-value {
  color: #0f766e;
}

.stock-row-divider {
  width: 1px;
  height: 22px;
  background: linear-gradient(180deg, transparent, rgba(199, 169, 130, 0.45), transparent);
  margin: 0 4px;
  flex: 0 0 auto;
}

.metric-change-chip {
  display: inline-flex;
  align-items: center;
  min-width: 40px;
  justify-content: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  line-height: 1.35;
  font-weight: 700;
}

.metric-chip-success {
  color: #166534;
  background: rgba(220, 252, 231, 0.95);
  box-shadow: inset 0 0 0 1px rgba(74, 222, 128, 0.35);
}

.metric-chip-warning {
  color: #9a3412;
  background: rgba(255, 237, 213, 0.95);
  box-shadow: inset 0 0 0 1px rgba(251, 146, 60, 0.35);
}

.stock-snapshot-warning {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 2px 8px;
  border-radius: 999px;
  color: #9a3412;
  background: rgba(255, 237, 213, 0.95);
  box-shadow: inset 0 0 0 1px rgba(251, 146, 60, 0.35);
  font-size: 12px;
  font-weight: 700;
}
</style>
