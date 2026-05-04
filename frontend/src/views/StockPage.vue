<template>
  <div class="page-stack stock-page">
    <section v-if="loading" class="skeleton-grid compact stock-skeleton-grid">
      <el-card v-for="item in 4" :key="item" shadow="hover" class="program-card skeleton-card compact">
        <el-skeleton animated>
          <template #template>
            <el-skeleton-item variant="image" style="width: 100%; height: 168px; border-radius: 18px; margin-bottom: 14px" />
            <el-skeleton-item variant="h3" style="width: 74%; height: 24px; margin-bottom: 12px" />
            <el-skeleton-item variant="text" style="width: 92%; margin-bottom: 8px" />
            <el-skeleton-item variant="text" style="width: 60%; margin-bottom: 12px" />
            <el-skeleton-item variant="text" style="width: 100%; height: 32px" />
          </template>
        </el-skeleton>
      </el-card>
    </section>

    <section v-else class="page-stack stock-content-stack">
      <el-card shadow="never" class="stock-table-card stock-gallery-card">
        <template #header>
          <div class="stock-table-header stock-table-header-stack">
            <div class="stock-search-bar">
              <el-input
                v-model="keywordInput"
                clearable
                size="large"
                placeholder="搜索商品名称 / 商品ID / 小程序名称 / program_id，回车直接搜索"
                @keyup.enter="applySearch"
                @clear="applySearch"
              >
                <template #append>
                  <el-button @click="applySearch">搜索</el-button>
                </template>
              </el-input>
              <el-button plain @click="hiddenDrawerVisible = true">
                已隐藏 {{ hiddenTotal }}
              </el-button>
              <el-button plain @click="offShelfDrawerVisible = true">
                已下架 {{ offShelfTotal }}
              </el-button>
              <el-button type="primary" plain @click="refreshStockCenter" :loading="refreshing">刷新数据</el-button>
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
                  @click="selectTag('')"
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
                  @click="selectTag(tag)"
                >
                  <span class="stock-tag-chip-dot"></span>
                  <span>{{ tag }}</span>
                </button>
                <span v-if="!availableTags.length" class="stock-tag-empty">暂无可筛选标签</span>
              </div>
            </div>

            <div class="stock-table-summary">
              <button
                type="button"
                class="stock-summary-item"
                :class="{ active: activeStatus === 'all' }"
                @click="applyMetricFilter('all')"
              >
                总商品 {{ summary.totalProducts }}
              </button>
              <button
                type="button"
                class="stock-summary-item success"
                :class="{ active: activeStatus === 'in_stock' }"
                @click="applyMetricFilter('in_stock')"
              >
                有库存 {{ summary.inStockProducts }}
              </button>
              <button
                type="button"
                class="stock-summary-item danger"
                :class="{ active: activeStatus === 'out_of_stock' }"
                @click="applyMetricFilter('out_of_stock')"
              >
                无库存 {{ summary.outOfStockProducts }}
              </button>
              <button
                type="button"
                class="stock-summary-item brand"
                :class="{ active: activeStatus === 'redeemable' }"
                @click="applyMetricFilter('redeemable')"
              >
                可兑换 {{ summary.redeemableProducts }}
              </button>
            </div>

            <div class="stock-toolbar-meta stock-toolbar-meta-compact">
              <div class="stock-meta-left">
                <el-tag round effect="plain" type="info">当前结果 {{ filteredProducts.length }}</el-tag>
                <el-tag round effect="plain" type="info">已加载 {{ visibleProducts.length }} 条</el-tag>
                <el-tag v-if="searchKeyword" round effect="plain" type="warning">关键词：{{ searchKeyword }}</el-tag>
                <el-tag v-if="currentTag" round effect="plain" type="success">标签：{{ currentTag }}</el-tag>
                <el-tag v-if="loadedFromCache" round effect="plain" type="success">缓存命中</el-tag>
              </div>
              <div class="stock-meta-right">
                <span class="stock-meta-text">每次下拉自动加载 {{ PAGE_SIZE }} 条</span>
              </div>
            </div>
          </div>
        </template>

        <div v-if="loadError" class="program-state-card compact stock-state-card">
          <el-result icon="error" title="库存数据加载失败" sub-title="请检查接口或网络状态后重新尝试。">
            <template #extra>
              <el-button type="primary" @click="refreshStockCenter">重新加载</el-button>
            </template>
          </el-result>
        </div>

        <div v-else-if="!filteredProducts.length" class="program-state-card compact stock-state-card">
          <el-empty description="没有符合条件的商品">
            <template #description>
              <p>可尝试重新输入关键词，或点击上方统计标签切换筛选条件。</p>
            </template>
            <div class="empty-state-actions">
              <el-button type="primary" plain @click="resetFilters">清空搜索与筛选</el-button>
              <el-button plain @click="hiddenDrawerVisible = true">查看已隐藏</el-button>
            </div>
          </el-empty>
        </div>

        <div v-else class="stock-gallery-list">
          <article v-for="item in visibleProducts" :key="`${item.program_id}-${item.product_id}`" class="stock-gallery-item">
            <div class="stock-gallery-image-wrap">
              <el-image
                v-if="item.image_url || item.image_local_path"
                :src="item.image_url || item.image_local_path"
                class="stock-gallery-image"
                fit="cover"
                :preview-src-list="[item.image_url || item.image_local_path]"
                preview-teleported
                loading="lazy"
              />
              <div v-else class="stock-gallery-image stock-gallery-image-empty">暂无图片</div>
              <div class="stock-gallery-image-mask">
                <el-tag size="small" round effect="dark" :type="item.statusTagType">{{ item.statusLabel }}</el-tag>
              </div>
            </div>

            <div class="stock-gallery-main">
              <div class="stock-gallery-top-row">
                <div class="stock-gallery-title-block">
                  <h3 class="stock-gallery-title">{{ item.product_name || item.product_id }}</h3>
                  <div class="stock-gallery-program-row merged-program-row">
                    <div class="stock-gallery-program-name">{{ item.program_name || item.program_id }}</div>
                    <div class="stock-gallery-chip-row inline-program-action-row">
                      <el-tag size="small" round effect="plain" :type="item.redeemable ? 'success' : 'info'">
                        {{ item.redeemable ? '可兑换' : '不可兑换' }}
                      </el-tag>
                      <el-button
                        size="small"
                        plain
                        type="danger"
                        :loading="hidingProductId === item.id"
                        @click="hideProduct(item)"
                      >
                        不感兴趣
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>

              <div class="stock-gallery-core-row three-col-core-row">
                <div class="stock-gallery-core-item">
                  <span class="stock-core-label">积分</span>
                  <span class="stock-core-value accent">{{ item.points ?? 0 }}</span>
                </div>
                <div class="stock-gallery-core-item">
                  <span class="stock-core-label">库存</span>
                  <span class="stock-core-value">{{ item.stock ?? 0 }}</span>
                </div>
                <div class="stock-gallery-core-item compact">
                  <span class="stock-core-label">最高分</span>
                  <span class="stock-core-value accent">{{ item.maxUserPoints }}</span>
                </div>
              </div>
            </div>
          </article>
        </div>

        <div v-if="filteredProducts.length" class="stock-pagination-row stock-infinite-row">
          <div class="stock-pagination-text">已显示 {{ visibleProducts.length }} / {{ filteredProducts.length }} 条</div>
          <span class="stock-meta-text" v-if="hasMore">继续下拉自动加载更多</span>
          <span class="stock-meta-text" v-else>已加载全部数据</span>
        </div>

        <div
          v-if="filteredProducts.length && hasMore"
          ref="loadMoreSentinel"
          class="infinite-sentinel stock-infinite-sentinel"
          aria-hidden="true"
        ></div>
      </el-card>
    </section>

    <el-drawer v-model="detailDrawerVisible" :title="detailProduct?.product_name || '商品详情'" size="520px">
      <template v-if="detailProduct">
        <div class="stock-detail-stack">
          <div class="stock-detail-hero">
            <el-image
              v-if="detailProduct.image_url || detailProduct.image_local_path"
              :src="detailProduct.image_url || detailProduct.image_local_path"
              class="stock-detail-image"
              fit="cover"
              :preview-src-list="[detailProduct.image_url || detailProduct.image_local_path]"
              preview-teleported
            />
            <div v-else class="stock-detail-image stock-detail-image-empty">暂无图片</div>
            <div class="stock-detail-info">
              <div class="stock-detail-name">{{ detailProduct.product_name || detailProduct.product_id }}</div>
              <div class="stock-detail-subline">{{ detailProduct.product_id || '未设置商品ID' }}</div>
              <div class="stock-detail-tag-row">
                <el-tag round effect="plain">{{ detailProduct.program_name || detailProduct.program_id }}</el-tag>
                <el-tag round effect="plain" :type="detailProduct.statusTagType">{{ detailProduct.statusLabel }}</el-tag>
                <el-tag round effect="plain" :type="detailProduct.redeemable ? 'success' : 'info'">
                  {{ detailProduct.redeemable ? '可兑换' : '不可兑换' }}
                </el-tag>
              </div>
            </div>
          </div>

          <div class="stock-detail-grid">
            <div class="stock-detail-item">
              <span class="stock-detail-label">当前库存</span>
              <strong>{{ detailProduct.stock ?? 0 }}</strong>
            </div>
            <div class="stock-detail-item">
              <span class="stock-detail-label">所需积分</span>
              <strong>{{ detailProduct.points ?? 0 }}</strong>
            </div>
            <div class="stock-detail-item">
              <span class="stock-detail-label">最高积分</span>
              <strong>{{ detailProduct.maxUserPoints ?? 0 }}</strong>
            </div>
            <div class="stock-detail-item">
              <span class="stock-detail-label">兑换判断</span>
              <strong>{{ detailProduct.redeemable ? '当前可兑换' : '当前不可兑换' }}</strong>
            </div>
            <div class="stock-detail-item wide">
              <span class="stock-detail-label">所属小程序</span>
              <strong>{{ detailProduct.program_name || detailProduct.program_id }}</strong>
              <span class="stock-detail-subtext">{{ detailProduct.program_id }}</span>
            </div>
            <div class="stock-detail-item wide">
              <span class="stock-detail-label">图片来源</span>
              <strong>{{ detailProduct.image_url || detailProduct.image_local_path || '暂无图片' }}</strong>
            </div>
          </div>
        </div>
      </template>
    </el-drawer>

    <el-drawer
      v-model="hiddenDrawerVisible"
      title="已隐藏商品"
      size="560px"
      @open="fetchHiddenProducts()"
    >
      <div class="hidden-products-drawer">
        <div class="hidden-products-toolbar">
          <el-input
            v-model="hiddenKeywordInput"
            clearable
            placeholder="搜索已隐藏商品"
            @keyup.enter="fetchHiddenProducts(1)"
            @clear="fetchHiddenProducts(1)"
          >
            <template #append>
              <el-button @click="fetchHiddenProducts(1)">搜索</el-button>
            </template>
          </el-input>
          <el-tag round effect="plain" type="info">隐藏数 {{ hiddenTotal }}</el-tag>
        </div>

        <div v-if="hiddenLoading" class="hidden-products-loading">
          <el-skeleton :rows="5" animated />
        </div>

        <el-empty v-else-if="!hiddenProducts.length" description="暂无已隐藏商品">
          <template #description>
            <p>你隐藏掉的商品会出现在这里。</p>
          </template>
        </el-empty>

        <div v-else class="hidden-products-list">
          <article v-for="item in hiddenProducts" :key="`hidden-${item.id}`" class="hidden-product-card">
            <el-image
              v-if="item.image_url || item.image_local_path"
              :src="item.image_url || item.image_local_path"
              class="hidden-product-thumb"
              fit="cover"
              :preview-src-list="[item.image_url || item.image_local_path]"
              preview-teleported
            />
            <div v-else class="hidden-product-thumb hidden-product-thumb-empty">无图</div>
            <div class="hidden-product-main">
              <div class="hidden-product-name">{{ item.product_name || item.product_id }}</div>
              <div class="hidden-product-meta">{{ item.program_name || item.program_id }} · {{ item.points ?? 0 }} 积分 · 库存 {{ item.stock ?? 0 }}</div>
              <div class="hidden-product-time">隐藏时间：{{ formatHiddenAt(item.hidden_at) }}</div>
            </div>
            <el-button
              size="small"
              type="primary"
              plain
              :loading="restoringProductId === item.id"
              @click="restoreProduct(item)"
            >
              恢复显示
            </el-button>
          </article>
        </div>
      </div>
    </el-drawer>

    <el-drawer
      v-model="offShelfDrawerVisible"
      title="已下架商品"
      size="680px"
      @open="fetchOffShelfProducts()"
    >
      <div class="hidden-products-drawer">
        <div class="hidden-products-toolbar">
          <el-input
            v-model="offShelfKeywordInput"
            clearable
            placeholder="搜索已下架商品 / 小程序"
            @keyup.enter="fetchOffShelfProducts()"
            @clear="fetchOffShelfProducts()"
          >
            <template #append>
              <el-button @click="fetchOffShelfProducts()">搜索</el-button>
            </template>
          </el-input>
          <el-tag round effect="plain" type="warning">下架数 {{ offShelfTotal }}</el-tag>
        </div>

        <div v-if="offShelfLoading" class="hidden-products-loading">
          <el-skeleton :rows="6" animated />
        </div>

        <el-empty v-else-if="!offShelfPrograms.length" description="暂无已下架商品">
          <template #description>
            <p>自动比对后判定为下架的商品会按小程序聚合展示在这里。</p>
          </template>
        </el-empty>

        <div v-else class="off-shelf-program-list">
          <article v-for="group in offShelfPrograms" :key="group.program_id" class="off-shelf-program-card">
            <div class="off-shelf-program-head">
              <div>
                <div class="off-shelf-program-name">{{ group.program_name || group.program_id }}</div>
                <div class="off-shelf-program-id">{{ group.program_id }}</div>
              </div>
              <el-tag round effect="plain" type="danger">下架 {{ group.count }}</el-tag>
            </div>

            <div class="off-shelf-product-list">
              <div v-for="item in group.products" :key="`${group.program_id}-${item.product_id}`" class="off-shelf-product-item">
                <el-image
                  v-if="item.image_url || item.image_local_path"
                  :src="item.image_url || item.image_local_path"
                  class="hidden-product-thumb"
                  fit="cover"
                  :preview-src-list="[item.image_url || item.image_local_path]"
                  preview-teleported
                />
                <div v-else class="hidden-product-thumb hidden-product-thumb-empty">无图</div>
                <div class="hidden-product-main">
                  <div class="hidden-product-name">{{ item.product_name || item.product_id }}</div>
                  <div class="hidden-product-meta">{{ item.points ?? 0 }} 积分 · 库存 {{ item.stock ?? 0 }}</div>
                  <div class="hidden-product-time">下架时间：{{ formatHiddenAt(item.unlisted_at || item.hidden_at) }}</div>
                </div>
                <div class="off-shelf-product-actions">
                  <el-button
                    size="small"
                    type="primary"
                    plain
                    :loading="relistingId === item.id"
                    @click="relistProduct(item, group)"
                  >恢复上架</el-button>
                </div>
              </div>
            </div>
          </article>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const PAGE_SIZE = 20
const STOCK_CACHE_TTL = 60 * 1000
const HIDDEN_PAGE_SIZE = 100

const loading = ref(false)
const refreshing = ref(false)
const loadError = ref(false)
const loadedFromCache = ref(false)
const keywordInput = ref('')
const searchKeyword = ref('')
const activeStatus = ref('all')
const currentTag = ref('')
const availableTags = ref([])
const allProducts = shallowRef([])
const visibleCount = ref(PAGE_SIZE)
const detailDrawerVisible = ref(false)
const detailProduct = ref(null)
const loadMoreSentinel = ref(null)
const hiddenDrawerVisible = ref(false)
const hiddenLoading = ref(false)
const hiddenProducts = ref([])
const hiddenTotal = ref(0)
const hiddenKeywordInput = ref('')
const offShelfDrawerVisible = ref(false)
const offShelfLoading = ref(false)
const offShelfPrograms = ref([])
const offShelfTotal = ref(0)
const offShelfKeywordInput = ref('')
const hidingProductId = ref(null)
const restoringProductId = ref(null)
const relistingId = ref(null)

let observer = null
let stockCenterRequest = null
let stockCenterCache = null

const summary = computed(() => {
  let inStockProducts = 0
  let outOfStockProducts = 0
  let redeemableProducts = 0

  for (const item of allProducts.value) {
    if (item.inStock) {
      inStockProducts += 1
    } else {
      outOfStockProducts += 1
    }
    if (item.redeemable) {
      redeemableProducts += 1
    }
  }

  return {
    totalProducts: allProducts.value.length,
    inStockProducts,
    outOfStockProducts,
    redeemableProducts,
  }
})

const filteredProducts = computed(() => {
  const normalizedKeyword = searchKeyword.value.trim().toLowerCase()

  return allProducts.value.filter((item) => {
    const matchKeyword = !normalizedKeyword || [
      item.product_name,
      item.product_id,
      item.program_id,
      item.program_name,
    ].some((field) => String(field || '').toLowerCase().includes(normalizedKeyword))

    const matchStatus =
      activeStatus.value === 'all' ||
      (activeStatus.value === 'in_stock' && item.inStock) ||
      (activeStatus.value === 'out_of_stock' && !item.inStock) ||
      (activeStatus.value === 'redeemable' && item.redeemable)

    const matchTag = !currentTag.value || (Array.isArray(item.tags) && item.tags.includes(currentTag.value))

    return matchKeyword && matchStatus && matchTag
  })
})

const visibleProducts = computed(() => filteredProducts.value.slice(0, visibleCount.value))
const hasMore = computed(() => visibleProducts.value.length < filteredProducts.value.length)

function buildStatus(stock) {
  const stockValue = Number(stock || 0)
  if (stockValue > 0) {
    return { inStock: true, statusKey: 'in_stock', statusLabel: '有库存', statusTagType: 'success' }
  }
  return { inStock: false, statusKey: 'out_of_stock', statusLabel: '无库存', statusTagType: 'danger' }
}

function normalizeProduct(item) {
  const status = buildStatus(item.stock)
  const maxUserPoints = Number(item.max_user_points ?? item.maxUserPoints ?? 0)
  const points = Number(item.points || 0)
  const redeemable = status.inStock && maxUserPoints >= points

  return {
    ...item,
    ...status,
    hasImage: Boolean(item.image_url || item.image_local_path),
    program_name: item.program_name || item.program_id,
    maxUserPoints,
    redeemable,
  }
}

function normalizeStockCenterResponse(data) {
  availableTags.value = Array.isArray(data?.available_tags) ? data.available_tags : []

  const items = Array.isArray(data?.items) ? data.items : []
  return items.map((item) => normalizeProduct({
    ...item,
    tags: Array.isArray(item.tags) ? item.tags : [],
  })).sort((a, b) => {
    if (a.redeemable !== b.redeemable) {
      return Number(b.redeemable) - Number(a.redeemable)
    }
    if (a.inStock !== b.inStock) {
      return Number(b.inStock) - Number(a.inStock)
    }
    return String(a.product_name || '').localeCompare(String(b.product_name || ''), 'zh-CN')
  })
}

function formatHiddenAt(value) {
  if (!value) return '未知'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

async function fetchStockCenter(forceRefresh = false) {
  const now = Date.now()
  if (!forceRefresh && stockCenterCache && now - stockCenterCache.timestamp < STOCK_CACHE_TTL) {
    loadedFromCache.value = true
    return stockCenterCache.data
  }

  if (!forceRefresh && stockCenterRequest) {
    loadedFromCache.value = true
    return stockCenterRequest
  }

  loadedFromCache.value = false
  stockCenterRequest = api.get('/stock/center')
    .then(({ data }) => {
      stockCenterCache = {
        data,
        timestamp: Date.now(),
      }
      return data
    })
    .finally(() => {
      stockCenterRequest = null
    })

  return stockCenterRequest
}

async function loadStockCenter(options = {}) {
  const { forceRefresh = false, silent = false } = options

  if (forceRefresh) {
    refreshing.value = true
  } else if (!silent) {
    loading.value = true
  }

  loadError.value = false

  try {
    const data = await fetchStockCenter(forceRefresh)
    allProducts.value = normalizeStockCenterResponse(data)
    resetVisibleCount()
  } catch (error) {
    console.error(error)
    loadError.value = true
    ElMessage.error('加载库存中心失败')
  } finally {
    loading.value = false
    refreshing.value = false
    await nextTick()
    initObserver()
  }
}

async function refreshStockCenter() {
  await loadStockCenter({ forceRefresh: true })
}

function applySearch() {
  searchKeyword.value = keywordInput.value.trim()
  resetVisibleCount()
}

function applyMetricFilter(status) {
  activeStatus.value = status
  resetVisibleCount()
}

function selectTag(tag) {
  currentTag.value = currentTag.value === tag ? '' : tag
  resetVisibleCount()
}

function resetFilters() {
  keywordInput.value = ''
  searchKeyword.value = ''
  activeStatus.value = 'all'
  currentTag.value = ''
  resetVisibleCount()
}

function openDetailDrawer(product) {
  detailProduct.value = product
  detailDrawerVisible.value = true
}

function resetVisibleCount() {
  visibleCount.value = PAGE_SIZE
}

function loadMore() {
  if (!hasMore.value) return
  visibleCount.value += PAGE_SIZE
}

function initObserver() {
  if (observer) {
    observer.disconnect()
    observer = null
  }
  if (!loadMoreSentinel.value || !hasMore.value) return

  observer = new IntersectionObserver(
    (entries) => {
      const entry = entries[0]
      if (entry?.isIntersecting) {
        loadMore()
      }
    },
    {
      root: null,
      rootMargin: '180px 0px',
      threshold: 0,
    },
  )

  observer.observe(loadMoreSentinel.value)
}

async function fetchHiddenProducts(page = 1) {
  hiddenLoading.value = true
  try {
    const keyword = hiddenKeywordInput.value.trim()
    const params = { page, size: HIDDEN_PAGE_SIZE }
    if (keyword) params.q = keyword
    const { data } = await api.get('/stock/hidden', { params })
    hiddenProducts.value = Array.isArray(data.items) ? data.items.map(normalizeProduct) : []
    hiddenTotal.value = Number(data.total || 0)
  } catch (error) {
    console.error(error)
    hiddenProducts.value = []
    ElMessage.error('加载已隐藏商品失败')
  } finally {
    hiddenLoading.value = false
  }
}

async function fetchOffShelfProducts() {
  offShelfLoading.value = true
  try {
    const keyword = offShelfKeywordInput.value.trim()
    const params = {}
    if (keyword) params.q = keyword
    const { data } = await api.get('/stock/off-shelf', { params })
    offShelfPrograms.value = Array.isArray(data.items)
      ? data.items.map((group) => ({
          ...group,
          products: Array.isArray(group.products) ? group.products.map(normalizeProduct) : [],
        }))
      : []
    offShelfTotal.value = Number(data.total || 0)
  } catch (error) {
    console.error(error)
    offShelfPrograms.value = []
    ElMessage.error('加载已下架商品失败')
  } finally {
    offShelfLoading.value = false
  }
}

async function relistProduct(product, group) {
  if (!product?.id || relistingId.value) return
  relistingId.value = product.id
  try {
    await api.put(`/stock/products/${product.id}/relist`)
    // 从所在分组里移除该商品；如果分组空了一并清掉
    if (group) {
      group.products = group.products.filter((item) => item.id !== product.id)
      group.count = group.products.length
    }
    offShelfPrograms.value = offShelfPrograms.value.filter((g) => (g.products || []).length > 0)
    offShelfTotal.value = Math.max(0, offShelfTotal.value - 1)
    // 主列表的缓存可能不再准确，标记失效
    stockCenterCache = null
    ElMessage.success(`「${product.product_name || product.product_id}」已恢复上架`)
  } catch (error) {
    console.error(error)
    ElMessage.error('恢复上架失败')
  } finally {
    relistingId.value = null
  }
}

async function hideProduct(product) {
  try {
    await ElMessageBox.confirm(
      `隐藏后，“${product.product_name || product.product_id}”会从默认商品列表移除。`,
      '确认隐藏商品',
      {
        confirmButtonText: '确认隐藏',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
  } catch {
    return
  }

  hidingProductId.value = product.id
  try {
    await api.put(`/stock/products/${product.id}/hide`)
    allProducts.value = allProducts.value.filter((item) => item.id !== product.id)
    if (detailProduct.value?.id === product.id) {
      detailDrawerVisible.value = false
      detailProduct.value = null
    }
    hiddenTotal.value += 1
    if (hiddenDrawerVisible.value) {
      await fetchHiddenProducts(1)
    }
    if (offShelfDrawerVisible.value) {
      await fetchOffShelfProducts()
    }
    ElMessage.success('已隐藏该商品')
  } catch (error) {
    console.error(error)
    ElMessage.error('隐藏商品失败')
  } finally {
    hidingProductId.value = null
  }
}

async function restoreProduct(product) {
  restoringProductId.value = product.id
  try {
    await api.put(`/stock/products/${product.id}/restore`)
    hiddenProducts.value = hiddenProducts.value.filter((item) => item.id !== product.id)
    hiddenTotal.value = Math.max(0, hiddenTotal.value - 1)
    stockCenterCache = null
    await loadStockCenter({ forceRefresh: true, silent: true })
    if (offShelfDrawerVisible.value) {
      await fetchOffShelfProducts()
    }
    ElMessage.success('商品已恢复显示')
  } catch (error) {
    console.error(error)
    ElMessage.error('恢复商品失败')
  } finally {
    restoringProductId.value = null
  }
}

watch(
  () => [filteredProducts.value.length, hasMore.value],
  async () => {
    await nextTick()
    initObserver()
  },
)

watch(hiddenDrawerVisible, (visible) => {
  if (visible) {
    fetchHiddenProducts(1)
  }
})

watch(offShelfDrawerVisible, (visible) => {
  if (visible) {
    fetchOffShelfProducts()
  }
})

onMounted(async () => {
  await loadStockCenter()
  await fetchHiddenProducts(1)
  await fetchOffShelfProducts()
})

onBeforeUnmount(() => {
  if (observer) {
    observer.disconnect()
  }
})
</script>

<style scoped>
.stock-page {
  gap: 20px;
}
.stock-content-stack {
  gap: 20px;
}
.stock-table-card {
  border-radius: 24px;
}
.stock-gallery-card {
  border: 1px solid rgba(233, 220, 200, 0.92);
  background: rgba(255, 252, 247, 0.92);
  box-shadow: 0 18px 40px rgba(126, 98, 63, 0.06);
}
.stock-table-header-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
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
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.78), 0 12px 26px rgba(125, 95, 58, 0.06);
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
.stock-gallery-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}
.stock-gallery-item {
  display: grid;
  grid-template-columns: 168px minmax(0, 1fr);
  gap: 18px;
  padding: 18px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: inset 0 0 0 1px rgba(236, 221, 199, 0.92);
  align-items: stretch;
}
.stock-gallery-image-wrap {
  position: relative;
  width: 168px;
  height: 168px;
  flex: 0 0 168px;
}
.stock-gallery-image,
.stock-gallery-image-empty,
.stock-detail-image,
.stock-detail-image-empty,
.hidden-product-thumb,
.hidden-product-thumb-empty {
  width: 100%;
  height: 168px;
  border-radius: 18px;
  object-fit: cover;
}
.stock-gallery-image-empty,
.stock-detail-image-empty,
.hidden-product-thumb-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(250, 240, 224, 0.9);
  color: #9b7e5c;
  font-size: 13px;
}
.stock-gallery-image-mask {
  position: absolute;
  left: 8px;
  bottom: 8px;
}
.stock-gallery-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.stock-gallery-top-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: flex-start;
}
.stock-gallery-title-block {
  min-width: 0;
  flex: 1;
}
.stock-gallery-title {
  margin: 0;
  font-size: 18px;
  line-height: 1.45;
  color: #3a2a1d;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.stock-gallery-program-name {
  color: #8f7658;
  font-size: 13px;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.merged-program-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 8px;
}
.inline-program-action-row {
  margin-top: 0;
  flex: 0 0 auto;
  justify-content: flex-end;
}
.stock-gallery-actions {
  flex: 0 0 auto;
}
.stock-gallery-core-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}
.two-col-core-row {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.three-col-core-row {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
.stock-gallery-core-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 16px;
  background: rgba(255, 252, 247, 0.9);
  box-shadow: inset 0 0 0 1px rgba(236, 221, 199, 0.92);
}
.stock-gallery-core-item.compact {
  background: rgba(255, 245, 229, 0.78);
}
.stock-core-label {
  color: #a08668;
  font-size: 12px;
  line-height: 1;
}
.stock-core-value {
  color: #5f4932;
  font-size: 20px;
  line-height: 1.1;
  font-weight: 800;
}
.stock-core-value.accent {
  color: #a16207;
}
.stock-gallery-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-top: 12px;
}
.simplified-chip-row {
  margin-top: 12px;
}
.under-stock-row {
  justify-content: flex-start;
}
.ordered-action-row {
  gap: 10px;
}
.stock-pagination-row {
  margin-top: 18px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #9b7e5c;
}
.stock-detail-stack {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.stock-detail-hero {
  display: flex;
  gap: 16px;
}
.stock-detail-image,
.stock-detail-image-empty {
  width: 160px;
  height: 160px;
}
.stock-detail-info {
  flex: 1;
}
.stock-detail-name {
  font-size: 22px;
  font-weight: 800;
  color: #2f2418;
}
.stock-detail-subline,
.stock-detail-subtext,
.hidden-product-time,
.off-shelf-program-id {
  margin-top: 6px;
  color: #9b7e5c;
  font-size: 13px;
}
.stock-detail-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
.stock-detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.stock-detail-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: inset 0 0 0 1px rgba(236, 221, 199, 0.92);
}
.stock-detail-item.wide {
  grid-column: 1 / -1;
}
.stock-detail-label {
  color: #9b7e5c;
  font-size: 13px;
}
.hidden-products-drawer {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.hidden-products-toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
}
.hidden-products-toolbar :deep(.el-input) {
  flex: 1;
}
.hidden-products-list,
.off-shelf-product-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.hidden-product-card,
.off-shelf-product-item {
  display: flex;
  gap: 14px;
  align-items: center;
  padding: 12px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: inset 0 0 0 1px rgba(236, 221, 199, 0.92);
}
.hidden-product-thumb,
.hidden-product-thumb-empty {
  width: 72px;
  height: 72px;
  flex: 0 0 72px;
}
.hidden-product-main {
  flex: 1;
  min-width: 0;
}
.off-shelf-product-actions {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
}
.hidden-product-name,
.off-shelf-program-name {
  color: #3a2a1d;
  font-weight: 700;
}
.hidden-product-meta {
  margin-top: 6px;
  color: #7b6650;
  font-size: 13px;
}
.off-shelf-program-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.off-shelf-program-card {
  padding: 16px;
  border-radius: 20px;
  background: rgba(255, 250, 245, 0.94);
  box-shadow: inset 0 0 0 1px rgba(236, 221, 199, 0.92);
}
.off-shelf-program-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 12px;
}
.hidden-products-loading {
  padding: 12px 0;
}
.stock-state-card {
  padding: 24px 8px;
}
.stock-infinite-sentinel {
  height: 2px;
}

@media (max-width: 1200px) {
  .stock-gallery-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .stock-filter-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }
  .stock-tag-list {
    justify-content: flex-start;
  }
}

@media (max-width: 900px) {
  .stock-search-bar,
  .hidden-products-toolbar,
  .stock-detail-hero {
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

  .stock-gallery-list {
    grid-template-columns: 1fr;
  }

  .stock-gallery-item {
    grid-template-columns: 1fr;
  }

  .stock-gallery-image-wrap {
    width: 100%;
    height: 220px;
    flex-basis: auto;
  }

  .stock-gallery-image,
  .stock-gallery-image-empty {
    height: 220px;
  }

  .stock-detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
