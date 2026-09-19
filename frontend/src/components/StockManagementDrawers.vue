<template>
  <el-drawer
    :model-value="hiddenVisible"
    title="已隐藏商品"
    size="560px"
    @update:model-value="emit('update:hidden-visible', $event)"
  >
    <div class="hidden-products-drawer">
      <div class="hidden-products-toolbar">
        <el-input
          :model-value="hiddenKeywordInput"
          clearable
          placeholder="搜索已隐藏商品"
          @update:model-value="emit('update:hidden-keyword-input', $event)"
          @keyup.enter="emit('fetch-hidden')"
          @clear="emit('fetch-hidden')"
        >
          <template #append>
            <el-button @click="emit('fetch-hidden')">搜索</el-button>
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
            <div class="hidden-product-meta">
              {{ item.program_name || item.program_id }} · {{ formatProductPrice(item) }} · 库存 {{ item.stock ?? 0 }}
            </div>
            <div class="hidden-product-time">隐藏时间：{{ formatHiddenAt(item.hidden_at) }}</div>
          </div>
          <el-button
            size="small"
            type="primary"
            plain
            :loading="restoringProductId === item.id"
            @click="emit('restore', item)"
          >
            恢复显示
          </el-button>
        </article>
      </div>
    </div>
  </el-drawer>

  <el-drawer
    :model-value="offShelfVisible"
    title="已下架商品"
    size="680px"
    @update:model-value="emit('update:off-shelf-visible', $event)"
  >
    <div class="hidden-products-drawer">
      <div class="hidden-products-toolbar">
        <el-input
          :model-value="offShelfKeywordInput"
          clearable
          placeholder="搜索已下架商品 / 小程序"
          @update:model-value="emit('update:off-shelf-keyword-input', $event)"
          @keyup.enter="emit('fetch-off-shelf')"
          @clear="emit('fetch-off-shelf')"
        >
          <template #append>
            <el-button @click="emit('fetch-off-shelf')">搜索</el-button>
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
            <el-tag round effect="plain" type="danger">下架 {{ group.total_count || group.count }}</el-tag>
          </div>

          <div class="off-shelf-product-list">
            <div
              v-for="item in group.products"
              :key="`${group.program_id}-${item.product_id}`"
              class="off-shelf-product-item"
            >
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
                <div class="hidden-product-meta">{{ formatProductPrice(item) }} · 库存 {{ item.stock ?? 0 }}</div>
                <div class="hidden-product-time">
                  下架时间：{{ formatHiddenAt(item.unlisted_at || item.hidden_at) }}
                </div>
              </div>
              <div class="off-shelf-product-actions">
                <el-button
                  size="small"
                  type="primary"
                  plain
                  :loading="relistingId === item.id"
                  @click="emit('relist', item, group)"
                >
                  <span>恢复上架</span>
                </el-button>
              </div>
            </div>
          </div>
        </article>
      </div>

      <div v-if="offShelfHasMore && !offShelfLoading" class="hidden-products-load-more">
        <el-button plain :loading="offShelfLoadingMore" @click="emit('fetch-off-shelf', { append: true })">
          加载更多
        </el-button>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
import { formatProductPrice } from '../utils/product'
import { formatApiDate as formatHiddenAt } from '../utils/date'

defineProps({
  hiddenVisible: { type: Boolean, default: false },
  hiddenLoading: { type: Boolean, default: false },
  hiddenProducts: { type: Array, default: () => [] },
  hiddenTotal: { type: Number, default: 0 },
  hiddenKeywordInput: { type: String, default: '' },
  offShelfVisible: { type: Boolean, default: false },
  offShelfLoading: { type: Boolean, default: false },
  offShelfLoadingMore: { type: Boolean, default: false },
  offShelfPrograms: { type: Array, default: () => [] },
  offShelfTotal: { type: Number, default: 0 },
  offShelfHasMore: { type: Boolean, default: false },
  offShelfKeywordInput: { type: String, default: '' },
  restoringProductId: { type: [Number, String], default: null },
  relistingId: { type: [Number, String], default: null },
})

const emit = defineEmits([
  'update:hidden-visible',
  'update:off-shelf-visible',
  'update:hidden-keyword-input',
  'update:off-shelf-keyword-input',
  'fetch-hidden',
  'fetch-off-shelf',
  'restore',
  'relist',
])
</script>

<style scoped>
.hidden-products-drawer {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hidden-products-load-more {
  display: flex;
  justify-content: center;
  padding: 8px 0 4px;
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
  border-radius: 14px;
  object-fit: cover;
}

.hidden-product-thumb-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(250, 240, 224, 0.9);
  color: #9b7e5c;
  font-size: 13px;
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

.hidden-product-time,
.off-shelf-program-id {
  margin-top: 6px;
  color: #9b7e5c;
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

@media (max-width: 900px) {
  .hidden-products-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .hidden-product-card,
  .off-shelf-product-item {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .off-shelf-product-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
