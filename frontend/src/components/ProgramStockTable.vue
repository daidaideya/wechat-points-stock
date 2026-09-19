<template>
  <div class="dialog-panel stock-table-panel">
    <div class="stock-section-title-row">
      <div class="stock-section-title">当前在架商品</div>
      <div class="stock-section-hint">
        按最高积分 {{ props.stockMaxUserPoints
        }}{{
          props.stockMaxUserCash != null ? ` / 现金 ¥${props.formatMoney(props.stockMaxUserCash)}` : ''
        }}判断：可兑换优先，不可兑换靠后
      </div>
    </div>
    <el-table
      :data="props.sortedStockProducts"
      stripe
      class="showcase-dialog-table stock-product-table"
      :row-class-name="props.stockRowClassName"
    >
      <el-table-column label="图片" width="96">
        <template #default="scope">
          <el-image
            v-if="scope.row.image_url"
            :src="scope.row.image_url"
            :alt="scope.row.product_name || '商品图片'"
            fit="cover"
            class="product-thumb"
            :preview-src-list="[scope.row.image_url]"
            preview-teleported
          />
          <span v-else class="empty-text">无图</span>
        </template>
      </el-table-column>
      <el-table-column prop="product_name" label="商品名称" min-width="280">
        <template #default="scope">
          <div class="stock-product-name-cell">
            <span>{{ scope.row.product_name || '未命名商品' }}</span>
            <el-tag v-if="props.isProductRedeemable(scope.row)" size="small" type="success" effect="light" round>
              可兑换
            </el-tag>
            <el-tag v-else size="small" type="info" effect="plain" round>
              {{ props.getRedeemBlockedLabel(scope.row) }}
            </el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="兑换价格" min-width="150">
        <template #default="scope">
          {{ props.formatProductPrice(scope.row) }}
        </template>
      </el-table-column>
      <el-table-column prop="stock" label="库存" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.stock > 0 ? 'success' : 'danger'">{{ scope.row.stock }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="差额" width="140">
        <template #default="scope">
          <span class="stock-points-gap" :class="props.isProductRedeemable(scope.row) ? 'is-ok' : 'is-short'">
            {{ props.formatPointsGap(scope.row) }}
          </span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
const props = defineProps({
  stockMaxUserPoints: { type: Number, default: 0 },
  stockMaxUserCash: { type: Number, default: null },
  sortedStockProducts: { type: Array, default: () => [] },
  formatMoney: { type: Function, required: true },
  formatProductPrice: { type: Function, required: true },
  isProductRedeemable: { type: Function, required: true },
  getRedeemBlockedLabel: { type: Function, required: true },
  formatPointsGap: { type: Function, required: true },
  stockRowClassName: { type: Function, required: true },
})
</script>

<style scoped>
.dialog-panel {
  padding: 16px 16px 14px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255, 251, 245, 0.96), rgba(255, 247, 235, 0.94));
  box-shadow: inset 0 0 0 1px rgba(235, 220, 194, 0.88);
}

.stock-section-title {
  margin-bottom: 12px;
  color: #7b5a37;
  font-size: 14px;
  font-weight: 700;
}

.stock-section-title-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.stock-section-title-row .stock-section-title {
  margin-bottom: 0;
}

.stock-section-hint {
  color: #9b7e5c;
  font-size: 12px;
  line-height: 1.4;
  text-align: right;
}

.stock-product-name-cell {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.stock-points-gap {
  font-size: 12px;
  font-weight: 700;
}

.stock-points-gap.is-ok {
  color: #15803d;
}

.stock-points-gap.is-short {
  color: #b45309;
}

.stock-product-table :deep(.stock-row-redeemable > td.el-table__cell) {
  background: rgba(220, 252, 231, 0.55) !important;
}

.stock-product-table :deep(.stock-row-locked > td.el-table__cell) {
  background: rgba(255, 247, 237, 0.5) !important;
}

.stock-product-table :deep(.stock-row-out > td.el-table__cell) {
  background: rgba(248, 250, 252, 0.85) !important;
  color: #94a3b8;
}

.stock-product-table :deep(.stock-row-redeemable:hover > td.el-table__cell) {
  background: rgba(187, 247, 208, 0.72) !important;
}

.stock-product-table :deep(.stock-row-locked:hover > td.el-table__cell) {
  background: rgba(254, 243, 199, 0.7) !important;
}

.stock-table-panel {
  padding-top: 12px;
}

.showcase-dialog-table :deep(.el-table) {
  --el-table-border-color: rgba(236, 221, 199, 0.92);
  --el-table-header-bg-color: rgba(255, 248, 238, 0.96);
  --el-table-tr-bg-color: rgba(255, 253, 249, 0.96);
  --el-table-row-hover-bg-color: rgba(255, 245, 229, 0.92);
  --el-table-text-color: #57412d;
  --el-table-header-text-color: #8b5e34;
}

.showcase-dialog-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.showcase-dialog-table :deep(th.el-table__cell) {
  font-weight: 700;
}

.showcase-dialog-table :deep(.el-table__cell) {
  padding: 14px 0;
}

.product-thumb {
  width: 62px;
  height: 62px;
  border-radius: 16px;
  box-shadow: 0 6px 16px rgba(126, 98, 63, 0.12);
}

@media (max-width: 768px) {
  .stock-section-title-row {
    flex-direction: column;
  }

  .stock-section-hint {
    text-align: left;
  }

  .showcase-dialog-table {
    width: 100%;
  }

  .showcase-dialog-table :deep(.el-table) {
    width: 100% !important;
  }

  .showcase-dialog-table :deep(.el-table__body-wrapper) {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
}
</style>
