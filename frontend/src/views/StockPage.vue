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
              <el-button type="primary" plain @click="refreshStockCenter" :loading="refreshing">刷新数据</el-button>
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
              <div class="stock-gallery-title-row">
                <h3 class="stock-gallery-title">{{ item.product_name || item.product_id }}</h3>
                <div class="stock-gallery-actions">
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

              <div class="stock-gallery-meta-row primary">
                <span class="stock-gallery-price">{{ item.points ?? 0 }} 积分</span>
                <span class="stock-gallery-stock">库存 {{ item.stock ?? 0 }}</span>
                <el-tag size="small" round effect="plain" :type="item.redeemable ? 'success' : 'info'">
                  {{ item.redeemable ? '可兑换' : '不可兑换' }}
                </el-tag>
                <el-tag size="small" round effect="plain" :type="item.hasImage ? 'success' : 'info'">
                  {{ item.hasImage ? '有图' : '无图' }}
                </el-tag>
              </div>

              <div class="stock-gallery-meta-row secondary">
                <span class="stock-gallery-label">小程序</span>
                <span class="stock-gallery-value">{{ item.program_name || item.program_id }}</span>
                <span class="stock-gallery-divider">·</span>
                <span class="stock-gallery-score-badge">
                  <span class="stock-gallery-score-label">最高分</span>
                  <span class="stock-gallery-score-value">{{ item.maxUserPoints }}</span>
                </span>
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
const hidingProductId = ref(null)
const restoringProductId = ref(null)

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

    return matchKeyword && matchStatus
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
  const items = Array.isArray(data?.items) ? data.items : []
  return items.map(normalizeProduct).sort((a, b) => {
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

function resetFilters() {
  keywordInput.value = ''
  searchKeyword.value = ''
  activeStatus.value = 'all'
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

onMounted(async () => {
  await loadStockCenter()
  await fetchHiddenProducts(1)
})

onBeforeUnmount(() => {
  if (observer) {
    observer.disconnect()
  }
})
</script>
