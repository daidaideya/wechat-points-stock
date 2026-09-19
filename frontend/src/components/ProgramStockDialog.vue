<template>
  <el-dialog
    :model-value="props.modelValue"
    :title="dialogTitle"
    :width="props.dialogWidth"
    :top="props.dialogTop"
    :fullscreen="props.fullscreen"
    class="showcase-dialog showcase-stock-dialog"
    destroy-on-close
    @update:model-value="handleModelUpdate"
  >
    <div class="showcase-dialog-body stock-dialog-body">
      <div class="showcase-dialog-intro">
        <div>
          <div class="showcase-dialog-title">库存详情总览</div>
          <div class="showcase-dialog-subtitle">
            查看当前小程序商品库存、兑换价格（积分 / 积分+钱）和最高用户资产；可兑换商品会优先高亮展示。
          </div>
        </div>
        <div class="stock-dialog-badges">
          <div class="showcase-dialog-badge stock-badge">商品 {{ props.stockData?.product_count ?? 0 }}</div>
          <div class="showcase-dialog-badge stock-badge">最高积分 {{ props.stockData?.max_user_points ?? 0 }}</div>
          <div
            v-if="props.stockData?.max_user_cash != null && props.stockData?.max_user_cash !== ''"
            class="showcase-dialog-badge stock-badge"
          >
            最高现金 ¥{{ props.formatMoney(props.stockData.max_user_cash) }}
          </div>
          <div class="showcase-dialog-badge stock-badge success-badge">可兑换 {{ props.redeemableProductCount }}</div>
          <div
            v-if="props.stockData?.stock_change?.added_count"
            class="showcase-dialog-badge stock-badge success-badge"
          >
            +{{ props.stockData.stock_change.added_count }}
          </div>
          <div
            v-if="props.stockData?.stock_change?.removed_count"
            class="showcase-dialog-badge stock-badge warning-badge"
          >
            -{{ props.stockData.stock_change.removed_count }}
          </div>
        </div>
      </div>

      <div
        v-if="props.loading"
        class="stock-loading dialog-panel"
        role="status"
        aria-live="polite"
        aria-busy="true"
        aria-label="正在加载库存详情"
      >
        <el-skeleton :rows="6" animated />
      </div>
      <template v-else>
        <div class="stock-summary-grid">
          <div class="stock-summary-card dialog-panel">
            <div class="stock-summary-label">当前商品数量</div>
            <div class="stock-summary-value">{{ props.stockData?.product_count ?? 0 }}</div>
          </div>
          <div class="stock-summary-card dialog-panel">
            <div class="stock-summary-label">当前最高用户积分</div>
            <div class="stock-summary-value">{{ props.stockData?.max_user_points ?? 0 }}</div>
          </div>
          <div class="stock-summary-card dialog-panel">
            <div class="stock-summary-label">当前最高用户现金</div>
            <div class="stock-summary-value">
              {{
                props.stockData?.max_user_cash == null || props.stockData?.max_user_cash === ''
                  ? '—'
                  : `¥${props.formatMoney(props.stockData.max_user_cash)}`
              }}
            </div>
          </div>
          <div class="stock-summary-card dialog-panel">
            <div class="stock-summary-label">较昨日新增商品</div>
            <div class="stock-summary-value success-text">{{ props.stockData?.stock_change?.added_count ?? 0 }}</div>
          </div>
          <div class="stock-summary-card dialog-panel">
            <div class="stock-summary-label">较昨日下架商品</div>
            <div class="stock-summary-value warning-text">{{ props.stockData?.stock_change?.removed_count ?? 0 }}</div>
          </div>
        </div>

        <div v-if="props.stockData?.changed_products?.length" class="dialog-panel stock-change-panel">
          <button
            type="button"
            class="stock-change-toggle"
            :aria-expanded="props.changeExpanded ? 'true' : 'false'"
            aria-controls="stock-change-list"
            @click="toggleChangeExpanded"
          >
            <div class="stock-change-toggle-main">
              <div class="stock-section-title">今日库存变动</div>
              <div class="stock-change-toggle-meta">
                <el-tag size="small" type="success" effect="plain" round>
                  +{{ props.stockData?.stock_change?.added_count ?? 0 }}
                </el-tag>
                <el-tag size="small" type="warning" effect="plain" round>
                  -{{ props.stockData?.stock_change?.removed_count ?? 0 }}
                </el-tag>
                <span class="stock-change-toggle-tip">
                  {{ props.changeExpanded ? '点击收起' : '点击展开明细' }}
                </span>
              </div>
            </div>
            <span class="stock-change-toggle-arrow" :class="{ open: props.changeExpanded }">▾</span>
          </button>

          <div
            id="stock-change-list"
            v-show="props.changeExpanded"
            class="stock-change-list"
            role="region"
            aria-label="今日库存变动明细"
            :aria-hidden="props.changeExpanded ? 'false' : 'true'"
          >
            <div
              v-for="item in props.stockData.changed_products"
              :key="`${item.change_type}-${item.product_id}`"
              class="stock-change-item"
            >
              <div class="stock-change-main">
                <span class="stock-change-name">{{ item.product_name }}</span>
                <span class="stock-change-meta">{{ props.formatProductPrice(item) }}</span>
              </div>
              <div class="stock-change-side">
                <el-tag :type="item.change_type === 'added' ? 'success' : 'warning'">
                  {{ item.change_type === 'added' ? '新增' : '下架' }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>

        <ProgramStockTable
          :stock-max-user-points="props.stockMaxUserPoints"
          :stock-max-user-cash="props.stockMaxUserCash"
          :sorted-stock-products="props.sortedStockProducts"
          :format-money="props.formatMoney"
          :format-product-price="props.formatProductPrice"
          :is-product-redeemable="props.isProductRedeemable"
          :get-redeem-blocked-label="props.getRedeemBlockedLabel"
          :format-points-gap="props.formatPointsGap"
          :stock-row-class-name="props.stockRowClassName"
        />
      </template>
    </div>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'
import ProgramStockTable from './ProgramStockTable.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  dialogWidth: {
    type: String,
    default: '1040px',
  },
  dialogTop: {
    type: String,
    default: '5vh',
  },
  fullscreen: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  stockData: {
    type: Object,
    default: null,
  },
  changeExpanded: {
    type: Boolean,
    default: false,
  },
  redeemableProductCount: {
    type: Number,
    default: 0,
  },
  stockMaxUserPoints: {
    type: Number,
    default: 0,
  },
  stockMaxUserCash: {
    type: Number,
    default: null,
  },
  sortedStockProducts: {
    type: Array,
    default: () => [],
  },
  formatMoney: {
    type: Function,
    required: true,
  },
  formatProductPrice: {
    type: Function,
    required: true,
  },
  isProductRedeemable: {
    type: Function,
    required: true,
  },
  getRedeemBlockedLabel: {
    type: Function,
    required: true,
  },
  formatPointsGap: {
    type: Function,
    required: true,
  },
  stockRowClassName: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits(['update:modelValue', 'update:change-expanded'])

const dialogTitle = computed(() => {
  if (!props.stockData?.program_name) return '库存详情'
  return `${props.stockData.program_name} - 库存详情`
})

function handleModelUpdate(value) {
  emit('update:modelValue', value)
}

function toggleChangeExpanded() {
  emit('update:change-expanded', !props.changeExpanded)
}
</script>

<style scoped>
.showcase-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.showcase-dialog-intro {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 2px 2px 6px;
}

.showcase-dialog-title {
  color: #3a2a1d;
  font-size: 16px;
  font-weight: 700;
}

.showcase-dialog-subtitle {
  margin-top: 6px;
  color: #9b7e5c;
  font-size: 13px;
  line-height: 1.6;
}

.showcase-dialog-badge {
  flex: 0 0 auto;
  padding: 8px 14px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(255, 244, 221, 0.96), rgba(255, 237, 213, 0.9));
  color: #8b5e34;
  font-size: 12px;
  font-weight: 700;
  box-shadow: inset 0 0 0 1px rgba(231, 202, 163, 0.72);
}

.stock-badge {
  color: #a16207;
}

.stock-dialog-badges {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.success-badge {
  color: #15803d;
}

.warning-badge {
  color: #b45309;
}

.dialog-panel {
  padding: 16px 16px 14px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255, 251, 245, 0.96), rgba(255, 247, 235, 0.94));
  box-shadow: inset 0 0 0 1px rgba(235, 220, 194, 0.88);
}

.stock-summary-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.stock-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.stock-section-title {
  margin-bottom: 12px;
  color: #7b5a37;
  font-size: 14px;
  font-weight: 700;
}

.stock-change-panel {
  padding-top: 14px;
}

.stock-change-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.stock-change-toggle-main {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.stock-change-toggle .stock-section-title {
  margin-bottom: 0;
}

.stock-change-toggle-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.stock-change-toggle-tip {
  color: #9b7e5c;
  font-size: 12px;
}

.stock-change-toggle-arrow {
  flex: 0 0 auto;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 248, 236, 0.95);
  color: #8b5e34;
  font-size: 14px;
  transition: transform 0.18s ease;
}

.stock-change-toggle-arrow.open {
  transform: rotate(180deg);
}

.stock-change-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
}

.stock-change-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: inset 0 0 0 1px rgba(236, 221, 199, 0.92);
}

.stock-change-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stock-change-name {
  color: #4a3623;
  font-size: 14px;
  font-weight: 700;
}

.stock-change-meta {
  color: #9b7e5c;
  font-size: 12px;
}

.stock-change-side {
  flex: 0 0 auto;
}

.stock-summary-label {
  color: #9b7e5c;
  font-size: 13px;
  font-weight: 600;
}

.stock-summary-value {
  color: #a16207;
  font-size: 30px;
  line-height: 1;
  font-weight: 800;
}

.success-text {
  color: #15803d;
}

.warning-text {
  color: #b45309;
}

.stock-loading {
  padding: 16px;
}

.showcase-dialog :deep(.el-dialog) {
  border-radius: 28px;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(255, 253, 249, 0.98), rgba(255, 248, 238, 0.98));
  box-shadow: 0 26px 60px rgba(97, 72, 43, 0.16);
}

.showcase-dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding: 24px 28px 10px;
}

.showcase-dialog :deep(.el-dialog__title) {
  color: #2f2418;
  font-size: 22px;
  font-weight: 800;
}

.showcase-dialog :deep(.el-dialog__body) {
  padding: 8px 28px 18px;
}

.showcase-dialog :deep(.el-dialog__footer) {
  padding: 10px 28px 26px;
}

.showcase-dialog :deep(.el-dialog__headerbtn) {
  top: 24px;
  right: 24px;
}

.showcase-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #a18461;
}

.showcase-dialog :deep(.el-dialog__footer .el-button) {
  min-width: 92px;
  height: 40px;
  border-radius: 14px;
}

.showcase-dialog :deep(.el-dialog__footer .el-button--default) {
  border-color: rgba(219, 183, 141, 0.74);
  color: #8b5e34;
  background: #fff9f2;
}

.showcase-dialog :deep(.el-dialog__footer .el-button--primary) {
  border: 0;
  background: linear-gradient(135deg, #f0c37c, #d9a25f);
  box-shadow: 0 12px 24px rgba(219, 162, 88, 0.22);
}

@media (max-width: 768px) {
  .stock-summary-grid {
    grid-template-columns: 1fr;
  }

  .showcase-dialog :deep(.el-dialog) {
    margin: 0 auto;
    max-width: 100vw;
  }

  .showcase-dialog :deep(.el-dialog__body) {
    max-height: min(78vh, 720px);
    overflow: auto;
    -webkit-overflow-scrolling: touch;
  }

  .showcase-dialog.is-fullscreen :deep(.el-dialog__body) {
    max-height: none;
  }
}
</style>
