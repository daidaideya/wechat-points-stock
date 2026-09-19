<template>
  <section class="detail-hero-card">
    <div class="detail-hero-main">
      <div class="detail-hero-text">
        <div class="detail-overline">小程序详情</div>
        <h1 class="detail-title">{{ props.detail?.program_name || props.programId }}</h1>
        <div class="detail-meta-row">
          <span class="detail-meta-chip id-chip">{{ props.detail?.program_id || props.programId }}</span>
          <span class="detail-meta-chip" :class="props.detail?.is_favorite ? 'favorite-chip' : 'normal-chip'">
            {{ props.detail?.is_favorite ? '已收藏' : '未收藏' }}
          </span>
          <span class="detail-meta-chip update-chip">
            最近更新：{{ props.formatDate(props.detail?.last_update_time) }}
          </span>
        </div>
      </div>

      <div class="detail-hero-actions">
        <el-button class="hero-action-button" @click="emit('refresh')">刷新</el-button>
        <el-button type="primary" class="hero-primary-button" @click="emit('back')">返回列表</el-button>
      </div>
    </div>

    <section class="detail-summary-grid">
      <article class="summary-panel">
        <div class="summary-label">program_id</div>
        <div class="summary-value mono-text">{{ props.detail?.program_id || props.programId }}</div>
      </article>
      <article class="summary-panel">
        <div class="summary-label">收藏状态</div>
        <div class="summary-value">{{ props.detail?.is_favorite ? '已加入收藏' : '暂未收藏' }}</div>
      </article>
      <article class="summary-panel">
        <div class="summary-label">标签数量</div>
        <div class="summary-value">{{ (props.detail?.tags || []).length || 0 }}</div>
      </article>
      <article class="summary-panel">
        <div class="summary-label">最高用户积分</div>
        <div class="summary-value emphasis-value">{{ props.stock?.max_user_points ?? 0 }}</div>
      </article>
    </section>

    <section class="detail-info-grid">
      <article class="info-card">
        <div class="info-card-label">标签</div>
        <div class="info-tag-row">
          <span v-for="tag in props.detail?.tags || []" :key="tag" class="info-tag">{{ tag }}</span>
          <span v-if="!(props.detail?.tags || []).length" class="info-tag empty">未设置标签</span>
        </div>
      </article>

      <article class="info-card">
        <div class="info-card-label">备注</div>
        <p class="info-note">{{ props.detail?.note || '暂无备注信息' }}</p>
      </article>
    </section>
  </section>
</template>

<script setup>
const props = defineProps({
  programId: {
    type: String,
    required: true,
  },
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

const emit = defineEmits(['refresh', 'back'])
</script>

<style scoped>
.detail-hero-card {
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding: 28px;
  border-radius: 26px;
  border: 1px solid rgba(235, 220, 194, 0.88);
  background: rgba(255, 252, 247, 0.92);
  box-shadow: 0 10px 24px rgba(126, 98, 63, 0.04);
  backdrop-filter: blur(2px);
}

.detail-hero-main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.detail-hero-text {
  min-width: 0;
  flex: 1;
}

.detail-overline {
  color: #b08a5b;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.detail-title {
  margin: 10px 0 0;
  color: #2f2418;
  font-size: 30px;
  line-height: 1.2;
  font-weight: 800;
  word-break: break-word;
}

.detail-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.detail-meta-chip {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 8px 14px;
  border-radius: 999px;
  background: #fff8ef;
  color: #8a6c4c;
  font-size: 12px;
  font-weight: 700;
  box-shadow: inset 0 0 0 1px rgba(231, 208, 176, 0.86);
}

.id-chip {
  color: #7a6143;
}

.favorite-chip {
  background: rgba(211, 239, 227, 0.92);
  color: #21684f;
  box-shadow: inset 0 0 0 1px rgba(166, 216, 189, 0.9);
}

.normal-chip,
.update-chip {
  background: rgba(252, 237, 214, 0.92);
  color: #9a651d;
}

.detail-hero-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 12px;
}

.hero-action-button,
.hero-primary-button {
  min-width: 104px;
  height: 42px;
  border-radius: 14px;
}

.hero-action-button {
  border-color: rgba(219, 183, 141, 0.74);
  color: #8b5e34;
  background: #fff9f2;
}

.hero-primary-button {
  border: 0;
  background: linear-gradient(135deg, #f0c37c, #d9a25f);
  box-shadow: 0 12px 24px rgba(219, 162, 88, 0.22);
}

.detail-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.summary-panel,
.info-card {
  padding: 18px 18px 16px;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(255, 251, 245, 0.96), rgba(255, 247, 235, 0.94));
  box-shadow: inset 0 0 0 1px rgba(235, 220, 194, 0.88);
}

.summary-label,
.info-card-label {
  color: #b08a5b;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.summary-value {
  margin-top: 10px;
  color: #312417;
  font-size: 22px;
  line-height: 1.35;
  font-weight: 700;
}

.mono-text {
  font-size: 15px;
  word-break: break-all;
}

.emphasis-value {
  color: #a16207;
}

.detail-info-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1.4fr);
  gap: 16px;
}

.info-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.info-tag {
  display: inline-flex;
  align-items: center;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(211, 239, 227, 0.92);
  color: #21684f;
  font-size: 12px;
  font-weight: 600;
  box-shadow: inset 0 0 0 1px rgba(166, 216, 189, 0.9);
}

.info-tag.empty {
  background: rgba(252, 237, 214, 0.92);
  color: #a16207;
  box-shadow: inset 0 0 0 1px rgba(239, 209, 163, 0.9);
}

.info-note {
  min-height: 52px;
  margin: 14px 0 0;
  color: #6f5a44;
  font-size: 14px;
  line-height: 1.8;
}

@media (max-width: 1200px) {
  .detail-summary-grid,
  .detail-info-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .detail-hero-main {
    flex-direction: column;
  }

  .detail-hero-actions {
    justify-content: flex-start;
  }
}

@media (max-width: 680px) {
  .detail-hero-card {
    padding: 18px;
    border-radius: 22px;
  }

  .detail-title {
    font-size: 24px;
  }

  .detail-summary-grid,
  .detail-info-grid {
    grid-template-columns: 1fr;
  }

  .summary-value {
    font-size: 18px;
  }
}
</style>
