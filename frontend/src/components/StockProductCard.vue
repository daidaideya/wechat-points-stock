<template>
  <article class="stock-gallery-item">
    <div class="stock-gallery-image-wrap">
      <el-image
        v-if="props.item.image_url || props.item.image_local_path"
        :src="props.item.image_url || props.item.image_local_path"
        class="stock-gallery-image"
        fit="cover"
        :preview-src-list="[props.item.image_url || props.item.image_local_path]"
        preview-teleported
        loading="lazy"
      />
      <div v-else class="stock-gallery-image stock-gallery-image-empty">暂无图片</div>
      <div class="stock-gallery-image-mask">
        <el-tag size="small" round effect="dark" :type="props.item.statusTagType">{{ props.item.statusLabel }}</el-tag>
      </div>
    </div>

    <div class="stock-gallery-main">
      <div class="stock-gallery-top-row">
        <div class="stock-gallery-title-block">
          <h3 class="stock-gallery-title">{{ props.item.product_name || props.item.product_id }}</h3>
          <div class="stock-gallery-program-row merged-program-row">
            <div class="stock-gallery-program-name">{{ props.item.program_name || props.item.program_id }}</div>
            <div class="stock-gallery-chip-row inline-program-action-row">
              <el-tag size="small" round effect="plain" :type="props.item.redeemable ? 'success' : 'info'">
                {{ props.item.redeemable ? '可兑换' : '不可兑换' }}
              </el-tag>
              <el-button size="small" plain type="danger" :loading="props.hiding" @click="handleHide">
                不感兴趣
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <div class="stock-gallery-core-row three-col-core-row">
        <div class="stock-gallery-core-item">
          <span class="stock-core-label">价格</span>
          <span class="stock-core-value accent stock-price-value">{{ formatProductPrice(props.item) }}</span>
        </div>
        <div class="stock-gallery-core-item">
          <span class="stock-core-label">库存</span>
          <span class="stock-core-value">{{ props.item.stock ?? 0 }}</span>
        </div>
        <div class="stock-gallery-core-item compact">
          <span class="stock-core-label">最高分</span>
          <span class="stock-core-value accent">{{ props.item.maxUserPoints }}</span>
        </div>
      </div>
    </div>
  </article>
</template>

<script setup>
import { formatProductPrice } from '../utils/product'

const props = defineProps({
  item: {
    type: Object,
    default: () => ({}),
  },
  hiding: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['hide'])

function handleHide() {
  emit('hide', props.item)
}
</script>

<style scoped>
.stock-gallery-item {
  display: grid;
  grid-template-columns: 168px minmax(0, 1fr);
  gap: 18px;
  padding: 18px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: inset 0 0 0 1px rgba(236, 221, 199, 0.92);
  align-items: stretch;
  min-width: 0;
}

.stock-gallery-image-wrap {
  position: relative;
  width: 168px;
  height: 168px;
  flex: 0 0 168px;
}

.stock-gallery-image,
.stock-gallery-image-empty {
  width: 100%;
  height: 168px;
  border-radius: 18px;
  object-fit: cover;
}

.stock-gallery-image-empty {
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

.stock-gallery-program-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 8px;
  min-width: 0;
}

.stock-gallery-program-name {
  color: #8f7658;
  font-size: 13px;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.inline-program-action-row {
  margin-top: 0;
  flex: 0 0 auto;
  justify-content: flex-end;
}

.stock-gallery-core-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
  min-width: 0;
}

.stock-gallery-core-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
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
  overflow-wrap: anywhere;
}

.stock-core-value.accent {
  color: #a16207;
}

.stock-price-value {
  font-size: 15px;
  line-height: 1.25;
  word-break: break-word;
}

.stock-gallery-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-top: 12px;
}

@container (max-width: 520px) {
  .stock-gallery-item {
    grid-template-columns: minmax(0, 1fr);
  }

  .stock-gallery-image-wrap {
    width: 100%;
    height: 180px;
  }

  .stock-gallery-image,
  .stock-gallery-image-empty {
    height: 180px;
  }

  .stock-gallery-program-row {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .stock-gallery-program-name {
    flex: 1 1 140px;
  }

  .inline-program-action-row {
    flex: 1 1 100%;
    justify-content: flex-start;
  }

  .stock-gallery-core-row {
    gap: 8px;
  }

  .stock-gallery-core-item {
    padding: 9px 8px;
  }

  .stock-core-value {
    font-size: 18px;
  }

  .stock-price-value {
    font-size: 14px;
  }
}

@media (max-width: 768px) {
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
}
</style>
