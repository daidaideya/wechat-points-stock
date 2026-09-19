<template>
  <div class="stock-table-header stock-table-header-stack">
    <div class="stock-search-bar">
      <el-input
        v-model="keywordInput"
        clearable
        size="large"
        placeholder="搜索商品名称 / 商品ID / 小程序名称 / program_id，回车直接搜索"
        @keyup.enter="emit('apply-search')"
        @clear="emit('apply-search')"
      >
        <template #append>
          <el-button @click="emit('apply-search')">搜索</el-button>
        </template>
      </el-input>
      <el-button plain @click="emit('open-hidden')"> 已隐藏 {{ hiddenTotal }} </el-button>
      <el-button plain @click="emit('open-off-shelf')"> 已下架 {{ offShelfTotal }} </el-button>
      <el-button type="primary" plain :loading="refreshing" @click="emit('refresh')">刷新数据</el-button>
    </div>

    <div class="stock-filter-toolbar">
      <div class="stock-filter-label-wrap">
        <div class="stock-filter-badge">标签筛选</div>
        <div class="stock-filter-title-group">
          <span class="stock-filter-label">按小程序标签筛选库存商品</span>
          <span class="stock-filter-tip">可快速定位同类商品，点击标签立即切换</span>
        </div>
      </div>
      <div class="stock-tag-list">
        <button
          type="button"
          class="stock-tag-chip stock-tag-chip-all"
          :class="{ active: currentTag === '' }"
          @click="emit('select-tag', '')"
        >
          <span class="stock-tag-chip-dot"></span>
          <span>全部</span>
        </button>
        <button
          v-for="tag in availableTags"
          :key="tag"
          type="button"
          class="stock-tag-chip"
          :class="{ active: currentTag === tag }"
          @click="emit('select-tag', tag)"
        >
          <span class="stock-tag-chip-dot"></span>
          <span>{{ tag }}</span>
        </button>
        <span v-if="!availableTags.length" class="stock-tag-empty">暂无可筛选标签</span>
      </div>
    </div>

    <div class="stock-filter-toolbar stock-price-filter-toolbar">
      <div class="stock-filter-label-wrap">
        <div class="stock-filter-badge stock-filter-badge-price">价格筛选</div>
        <div class="stock-filter-title-group">
          <span class="stock-filter-label">按兑换价格类型筛选</span>
          <span class="stock-filter-tip">纯积分 / 积分加钱购，可限定加钱金额上限</span>
        </div>
      </div>
      <div class="stock-price-filter-body">
        <div class="stock-price-mode-list">
          <button
            type="button"
            class="stock-tag-chip stock-tag-chip-all"
            :class="{ active: priceMode === 'all' }"
            @click="emit('select-price-mode', 'all')"
          >
            <span class="stock-tag-chip-dot"></span>
            <span>全部商品 {{ summary.totalProducts }}</span>
          </button>
          <button
            type="button"
            class="stock-tag-chip"
            :class="{ active: priceMode === 'points_only' }"
            @click="emit('select-price-mode', 'points_only')"
          >
            <span class="stock-tag-chip-dot"></span>
            <span>纯积分 {{ summary.pointsOnlyProducts }}</span>
          </button>
          <button
            type="button"
            class="stock-tag-chip"
            :class="{ active: priceMode === 'points_plus_cash' }"
            @click="emit('select-price-mode', 'points_plus_cash')"
          >
            <span class="stock-tag-chip-dot"></span>
            <span>积分加钱购 {{ summary.mixedProducts }}</span>
          </button>
        </div>
        <div v-if="priceMode === 'points_plus_cash'" class="stock-cash-cap-panel">
          <span class="stock-cash-cap-label">现金上限</span>
          <div class="stock-cash-cap-presets">
            <button
              v-for="preset in cashCapPresets"
              :key="preset"
              type="button"
              class="stock-cash-cap-chip"
              :class="{ active: isCashCapPresetActive(preset) }"
              @click="emit('apply-cash-cap-preset', preset)"
            >
              ≤ ¥{{ formatMoney(preset) }}
            </button>
            <button
              type="button"
              class="stock-cash-cap-chip"
              :class="{ active: cashCapInput === '' && cashCapValue === null }"
              @click="emit('clear-cash-cap')"
            >
              不限
            </button>
          </div>
          <div class="stock-cash-cap-custom">
            <span class="stock-cash-cap-prefix">自定义 ≤ ¥</span>
            <el-input
              v-model="cashCapInput"
              clearable
              size="small"
              class="stock-cash-cap-input"
              placeholder="如 1 / 9.9"
              @keyup.enter="emit('apply-cash-cap')"
              @clear="emit('clear-cash-cap')"
            />
            <el-button size="small" type="primary" plain @click="emit('apply-cash-cap')">应用</el-button>
          </div>
        </div>
      </div>
    </div>

    <div class="stock-table-summary">
      <button
        type="button"
        class="stock-summary-item"
        :class="{ active: activeStatus === 'all' }"
        @click="emit('apply-metric-filter', 'all')"
      >
        总商品 {{ summary.totalProducts }}
      </button>
      <button
        type="button"
        class="stock-summary-item success"
        :class="{ active: activeStatus === 'in_stock' }"
        @click="emit('apply-metric-filter', 'in_stock')"
      >
        有库存 {{ summary.inStockProducts }}
      </button>
      <button
        type="button"
        class="stock-summary-item danger"
        :class="{ active: activeStatus === 'out_of_stock' }"
        @click="emit('apply-metric-filter', 'out_of_stock')"
      >
        无库存 {{ summary.outOfStockProducts }}
      </button>
      <button
        type="button"
        class="stock-summary-item brand"
        :class="{ active: activeStatus === 'redeemable' }"
        @click="emit('apply-metric-filter', 'redeemable')"
      >
        可兑换 {{ summary.redeemableProducts }}
      </button>
    </div>

    <div class="stock-toolbar-meta stock-toolbar-meta-compact">
      <div class="stock-meta-left">
        <el-tag round effect="plain" type="info">当前结果 {{ totalResults }}</el-tag>
        <el-tag round effect="plain" type="info">已加载 {{ visibleCount }} 条</el-tag>
        <el-tag v-if="searchKeyword" round effect="plain" type="warning">关键词：{{ searchKeyword }}</el-tag>
        <el-tag v-if="currentTag" round effect="plain" type="success">标签：{{ currentTag }}</el-tag>
        <el-tag v-if="priceMode !== 'all'" round effect="plain" type="warning">{{ priceModeLabel }}</el-tag>
        <el-tag v-if="loadedFromCache" round effect="plain" type="success">缓存命中</el-tag>
      </div>
      <div class="stock-meta-right">
        <span class="stock-meta-text">每次下拉自动加载 {{ pageSize }} 条</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatMoney } from '../utils/product'

const props = defineProps({
  keywordInput: { type: String, default: '' },
  cashCapInput: { type: String, default: '' },
  cashCapValue: { type: Number, default: null },
  hiddenTotal: { type: Number, default: 0 },
  offShelfTotal: { type: Number, default: 0 },
  refreshing: { type: Boolean, default: false },
  availableTags: { type: Array, default: () => [] },
  currentTag: { type: String, default: '' },
  priceMode: { type: String, default: 'all' },
  priceModeLabel: { type: String, default: '' },
  activeStatus: { type: String, default: 'all' },
  searchKeyword: { type: String, default: '' },
  loadedFromCache: { type: Boolean, default: false },
  totalResults: { type: Number, default: 0 },
  visibleCount: { type: Number, default: 0 },
  pageSize: { type: Number, default: 20 },
  cashCapPresets: { type: Array, default: () => [] },
  summary: {
    type: Object,
    default: () => ({
      totalProducts: 0,
      inStockProducts: 0,
      outOfStockProducts: 0,
      redeemableProducts: 0,
      pointsOnlyProducts: 0,
      mixedProducts: 0,
    }),
  },
  isCashCapPresetActive: { type: Function, default: () => false },
})

const emit = defineEmits([
  'update:keywordInput',
  'update:cashCapInput',
  'apply-search',
  'open-hidden',
  'open-off-shelf',
  'refresh',
  'select-tag',
  'select-price-mode',
  'apply-cash-cap',
  'apply-cash-cap-preset',
  'clear-cash-cap',
  'apply-metric-filter',
])

const keywordInput = computed({
  get: () => props.keywordInput,
  set: (value) => emit('update:keywordInput', value),
})

const cashCapInput = computed({
  get: () => props.cashCapInput,
  set: (value) => emit('update:cashCapInput', value),
})

const cashCapValue = computed(() => props.cashCapValue)
const isCashCapPresetActive = (preset) => props.isCashCapPresetActive(preset)
</script>

<style scoped>
/* 这些样式属于筛选工具栏本身；组件拆分后不能再依赖 StockPage 的 scoped 样式。 */
.stock-search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.stock-search-bar :deep(.el-input) {
  flex: 1;
}

.stock-filter-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px;
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(255, 248, 238, 0.98), rgba(255, 253, 248, 0.92));
  border: 1px solid rgba(236, 219, 193, 0.92);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.78),
    0 12px 26px rgba(125, 95, 58, 0.06);
}

.stock-filter-label-wrap {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.stock-filter-badge {
  flex: 0 0 auto;
  padding: 8px 14px;
  border-radius: 999px;
  background: linear-gradient(135deg, #f5c77e, #e7a95c);
  color: #fff;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  box-shadow: 0 10px 20px rgba(225, 163, 79, 0.22);
}

.stock-filter-title-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.stock-filter-label {
  color: #5f452b;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.3;
}

.stock-filter-tip {
  color: #9b7e5c;
  font-size: 12px;
  line-height: 1.4;
}

.stock-tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  justify-content: flex-end;
}

.stock-tag-chip {
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

.stock-tag-chip:hover {
  transform: translateY(-1px);
  border-color: rgba(226, 175, 102, 0.95);
  background: rgba(255, 249, 241, 0.96);
  color: #9a6224;
  box-shadow: 0 10px 22px rgba(198, 146, 72, 0.14);
}

.stock-tag-chip-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(233, 184, 110, 0.95), rgba(216, 145, 58, 0.95));
  box-shadow: 0 0 0 4px rgba(244, 207, 157, 0.3);
}

.stock-tag-chip.active {
  border-color: transparent;
  background: linear-gradient(135deg, #f1c983, #df9f50);
  color: #fff;
  box-shadow: 0 12px 24px rgba(213, 153, 72, 0.28);
}

.stock-tag-chip.active .stock-tag-chip-dot {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.22);
}

.stock-tag-chip-all {
  background: rgba(255, 250, 244, 0.92);
}

.stock-filter-badge-price {
  background: linear-gradient(135deg, #8ec5ff, #5b9cf5);
}

.stock-price-filter-toolbar {
  align-items: flex-start;
}

.stock-price-filter-body {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
  min-width: 0;
  flex: 1;
}

.stock-price-mode-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
}

.stock-cash-cap-panel {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 10px 12px;
  width: 100%;
  padding: 12px 14px;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(239, 246, 255, 0.92), rgba(255, 251, 245, 0.92));
  box-shadow: inset 0 0 0 1px rgba(186, 214, 248, 0.9);
}

.stock-cash-cap-label {
  color: #3b6ea8;
  font-size: 13px;
  font-weight: 700;
}

.stock-cash-cap-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.stock-cash-cap-chip {
  border: 1px solid rgba(163, 201, 245, 0.95);
  border-radius: 999px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.92);
  color: #2f5f98;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.16s ease;
}

.stock-cash-cap-chip:hover {
  border-color: rgba(91, 156, 245, 0.95);
  color: #1d4ed8;
  transform: translateY(-1px);
}

.stock-cash-cap-chip.active {
  border-color: transparent;
  background: linear-gradient(135deg, #74b0f8, #4f8fe8);
  color: #fff;
  box-shadow: 0 10px 18px rgba(79, 143, 232, 0.22);
}

.stock-cash-cap-custom {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.stock-cash-cap-prefix {
  color: #6b8eb8;
  font-size: 12px;
  font-weight: 600;
}

.stock-cash-cap-input {
  width: 110px;
}

.stock-cash-cap-input :deep(.el-input__wrapper) {
  border-radius: 999px;
}

.stock-tag-empty {
  color: #ab8d6a;
  font-size: 13px;
}

.stock-table-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.stock-summary-item {
  border: 0;
  border-radius: 999px;
  padding: 10px 16px;
  background: rgba(255, 245, 229, 0.9);
  color: #8b5e34;
  font-weight: 700;
  cursor: pointer;
}

.stock-summary-item.active {
  background: linear-gradient(135deg, #f0c37c, #d9a25f);
  color: #fff;
}

.stock-summary-item.success {
  background: rgba(220, 252, 231, 0.88);
  color: #166534;
}

.stock-summary-item.danger {
  background: rgba(254, 226, 226, 0.9);
  color: #b91c1c;
}

.stock-summary-item.brand {
  background: rgba(219, 234, 254, 0.88);
  color: #1d4ed8;
}

.stock-toolbar-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.stock-meta-left {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.stock-meta-right {
  color: #9b7e5c;
  font-size: 13px;
}

@media (max-width: 1200px) {
  .stock-filter-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .stock-price-filter-body,
  .stock-price-mode-list,
  .stock-cash-cap-panel {
    align-items: flex-start;
    justify-content: flex-start;
  }

  .stock-tag-list {
    justify-content: flex-start;
  }
}

@media (max-width: 900px) {
  .stock-search-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .stock-filter-toolbar {
    padding: 14px;
    gap: 14px;
  }

  .stock-filter-label-wrap {
    align-items: flex-start;
  }

  .stock-filter-badge {
    padding: 7px 12px;
  }

  .stock-tag-list {
    width: 100%;
    gap: 8px;
  }

  .stock-tag-chip {
    padding: 9px 12px;
    font-size: 12px;
  }

  .stock-cash-cap-panel {
    padding: 12px;
  }

  .stock-cash-cap-input {
    width: 96px;
  }
}
</style>
