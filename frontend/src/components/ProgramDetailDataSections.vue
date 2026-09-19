<template>
  <section class="detail-section-card">
    <div class="detail-section-head">
      <div>
        <div class="detail-section-overline">积分数据</div>
        <h3 class="detail-section-title">积分排行榜</h3>
        <p class="detail-section-description">展示当前小程序下用户积分明细和最近一次上报时间。</p>
      </div>
    </div>

    <el-table :data="props.detail?.ranking || []" stripe class="showcase-table">
      <el-table-column prop="nickname" label="昵称" min-width="160" />
      <el-table-column prop="wechat_id" label="微信号" min-width="180" />
      <el-table-column prop="device" label="设备" min-width="140" />
      <el-table-column prop="points" label="积分" width="120" />
      <el-table-column label="更新时间" min-width="180">
        <template #default="scope">{{ props.formatDate(scope.row.report_time) }}</template>
      </el-table-column>
    </el-table>
  </section>

  <section class="detail-section-card">
    <div class="detail-section-head stock-head">
      <div>
        <div class="detail-section-overline">库存数据</div>
        <h3 class="detail-section-title">库存详情</h3>
        <p class="detail-section-description">当前最高用户资产与商品兑换价格（积分 / 积分+钱）一览。</p>
      </div>
      <div class="stock-highlight-card">
        <span class="stock-highlight-label">当前最高用户积分</span>
        <strong class="stock-highlight-value">{{ props.stock?.max_user_points ?? 0 }}</strong>
      </div>
      <div v-if="props.stock?.max_user_cash != null && props.stock?.max_user_cash !== ''" class="stock-highlight-card">
        <span class="stock-highlight-label">当前最高用户现金</span>
        <strong class="stock-highlight-value">¥{{ formatMoney(props.stock.max_user_cash) }}</strong>
      </div>
    </div>

    <el-table :data="props.stock?.products || []" stripe class="showcase-table">
      <el-table-column prop="product_name" label="商品名称" min-width="260" />
      <el-table-column label="兑换价格" min-width="160">
        <template #default="scope">
          {{ formatProductPrice(scope.row) }}
        </template>
      </el-table-column>
      <el-table-column prop="stock" label="库存" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.stock > 0 ? 'success' : 'danger'">{{ scope.row.stock }}</el-tag>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>

<script setup>
import { formatMoney, formatProductPrice } from '../utils/product'

const props = defineProps({
  detail: {
    type: Object,
    default: null,
  },
  stock: {
    type: Object,
    default: null,
  },
  formatDate: {
    type: Function,
    required: true,
  },
})
</script>

<style scoped>
.detail-section-card {
  padding: 24px;
  border-radius: 26px;
  border: 1px solid rgba(235, 220, 194, 0.88);
  background: rgba(255, 252, 247, 0.92);
  box-shadow: 0 10px 24px rgba(126, 98, 63, 0.04);
  backdrop-filter: blur(2px);
}

.detail-section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 18px;
}

.detail-section-overline {
  color: #b08a5b;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.detail-section-title {
  margin: 8px 0 0;
  color: #2f2418;
  font-size: 22px;
  line-height: 1.3;
  font-weight: 700;
}

.detail-section-description {
  margin: 8px 0 0;
  color: #9b7e5c;
  font-size: 13px;
  line-height: 1.7;
}

.stock-head {
  align-items: stretch;
  gap: 12px;
  flex-wrap: wrap;
}

.stock-highlight-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 180px;
  padding: 16px 18px;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(255, 244, 221, 0.96), rgba(255, 237, 213, 0.9));
  color: #8b5e34;
  box-shadow: inset 0 0 0 1px rgba(231, 202, 163, 0.72);
}

.stock-highlight-label {
  font-size: 12px;
  font-weight: 700;
}

.stock-highlight-value {
  margin-top: 8px;
  color: #a16207;
  font-size: 28px;
  line-height: 1;
}

.showcase-table :deep(.el-table) {
  --el-table-border-color: rgba(236, 221, 199, 0.92);
  --el-table-header-bg-color: rgba(255, 248, 238, 0.96);
  --el-table-tr-bg-color: rgba(255, 253, 249, 0.96);
  --el-table-row-hover-bg-color: rgba(255, 245, 229, 0.92);
  --el-table-text-color: #57412d;
  --el-table-header-text-color: #8b5e34;
}

.showcase-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.showcase-table :deep(th.el-table__cell) {
  font-weight: 700;
}

.showcase-table :deep(.el-table__cell) {
  padding: 14px 0;
}

@media (max-width: 900px) {
  .detail-section-head,
  .stock-head {
    flex-direction: column;
  }

  .stock-highlight-card {
    width: 100%;
    min-width: 0;
  }
}

@media (max-width: 680px) {
  .detail-section-card {
    padding: 18px;
    border-radius: 22px;
  }
}
</style>
