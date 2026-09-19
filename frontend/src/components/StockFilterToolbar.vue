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
