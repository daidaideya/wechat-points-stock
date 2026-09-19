<template>
  <el-drawer
    class="stock-product-detail-drawer"
    :model-value="props.modelValue"
    :title="props.product?.product_name || '商品详情'"
    size="520px"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <template v-if="props.product">
      <div class="stock-detail-stack">
        <div class="stock-detail-hero">
          <el-image
            v-if="props.product.image_url || props.product.image_local_path"
            :src="props.product.image_url || props.product.image_local_path"
            class="stock-detail-image"
            fit="cover"
            :preview-src-list="[props.product.image_url || props.product.image_local_path]"
            preview-teleported
          />
          <div v-else class="stock-detail-image stock-detail-image-empty">暂无图片</div>
          <div class="stock-detail-info">
            <div class="stock-detail-name">{{ props.product.product_name || props.product.product_id }}</div>
            <div class="stock-detail-subline">{{ props.product.product_id || '未设置商品ID' }}</div>
            <div class="stock-detail-tag-row">
              <el-tag round effect="plain">{{ props.product.program_name || props.product.program_id }}</el-tag>
              <el-tag round effect="plain" :type="props.product.statusTagType">
                {{ props.product.statusLabel }}
              </el-tag>
              <el-tag round effect="plain" :type="props.product.redeemable ? 'success' : 'info'">
                {{ props.product.redeemable ? '可兑换' : '不可兑换' }}
              </el-tag>
            </div>
          </div>
        </div>

        <div class="stock-detail-grid">
          <div class="stock-detail-item">
            <span class="stock-detail-label">当前库存</span>
            <strong>{{ props.product.stock ?? 0 }}</strong>
          </div>
          <div class="stock-detail-item">
            <span class="stock-detail-label">兑换价格</span>
            <strong>{{ props.formatProductPrice(props.product) }}</strong>
          </div>
          <div class="stock-detail-item">
            <span class="stock-detail-label">最高积分</span>
            <strong>{{ props.product.maxUserPoints ?? 0 }}</strong>
          </div>
          <div class="stock-detail-item">
            <span class="stock-detail-label">最高现金</span>
            <strong>{{ props.formatCashAmount(props.product.maxUserCash) }}</strong>
          </div>
          <div class="stock-detail-item">
            <span class="stock-detail-label">兑换判断</span>
            <strong>{{ props.product.redeemable ? '当前可兑换' : '当前不可兑换' }}</strong>
          </div>
          <div class="stock-detail-item wide">
            <span class="stock-detail-label">所属小程序</span>
            <strong>{{ props.product.program_name || props.product.program_id }}</strong>
            <span class="stock-detail-subtext">{{ props.product.program_id }}</span>
          </div>
          <div class="stock-detail-item wide">
            <span class="stock-detail-label">图片来源</span>
            <strong>{{ props.product.image_url || props.product.image_local_path || '暂无图片' }}</strong>
          </div>
        </div>
      </div>
    </template>
  </el-drawer>
</template>

<script setup>
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  product: {
    type: Object,
    default: null,
  },
  formatProductPrice: {
    type: Function,
    required: true,
  },
  formatCashAmount: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits(['update:modelValue'])
</script>

<style scoped>
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
  border-radius: 18px;
  object-fit: cover;
}

.stock-detail-image-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(250, 240, 224, 0.9);
  color: #9b7e5c;
  font-size: 13px;
}

.stock-detail-info {
  flex: 1;
  min-width: 0;
}

.stock-detail-name {
  font-size: 22px;
  font-weight: 800;
  color: #2f2418;
  overflow-wrap: anywhere;
}

.stock-detail-subline,
.stock-detail-subtext {
  margin-top: 6px;
  color: #9b7e5c;
  font-size: 13px;
  overflow-wrap: anywhere;
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
  min-width: 0;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: inset 0 0 0 1px rgba(236, 221, 199, 0.92);
}

.stock-detail-item.wide {
  grid-column: 1 / -1;
}

.stock-detail-item strong {
  overflow-wrap: anywhere;
}

.stock-detail-label {
  color: #9b7e5c;
  font-size: 13px;
}

@media (max-width: 900px) {
  .stock-detail-hero {
    flex-direction: column;
    align-items: stretch;
  }

  .stock-detail-image,
  .stock-detail-image-empty {
    width: 100%;
  }

  .stock-detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
