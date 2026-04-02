<template>
  <div class="page-stack program-detail-page">
    <section class="detail-hero-card">
      <div class="detail-hero-main">
        <div class="detail-hero-text">
          <div class="detail-overline">小程序详情</div>
          <h1 class="detail-title">{{ detail?.program_name || programId }}</h1>
          <div class="detail-meta-row">
            <span class="detail-meta-chip id-chip">{{ detail?.program_id || programId }}</span>
            <span class="detail-meta-chip" :class="detail?.is_favorite ? 'favorite-chip' : 'normal-chip'">
              {{ detail?.is_favorite ? '已收藏' : '未收藏' }}
            </span>
            <span class="detail-meta-chip update-chip">最近更新：{{ formatDate(detail?.last_update_time) }}</span>
          </div>
        </div>

        <div class="detail-hero-actions">
          <el-button class="hero-action-button" @click="loadDetail">刷新</el-button>
          <el-button type="primary" class="hero-primary-button" @click="goBackToPrograms">返回列表</el-button>
        </div>
      </div>

      <section class="detail-summary-grid">
        <article class="summary-panel">
          <div class="summary-label">program_id</div>
          <div class="summary-value mono-text">{{ detail?.program_id || programId }}</div>
        </article>
        <article class="summary-panel">
          <div class="summary-label">收藏状态</div>
          <div class="summary-value">{{ detail?.is_favorite ? '已加入收藏' : '暂未收藏' }}</div>
        </article>
        <article class="summary-panel">
          <div class="summary-label">标签数量</div>
          <div class="summary-value">{{ (detail?.tags || []).length || 0 }}</div>
        </article>
        <article class="summary-panel">
          <div class="summary-label">最高用户积分</div>
          <div class="summary-value emphasis-value">{{ stock?.max_user_points ?? 0 }}</div>
        </article>
      </section>

      <section class="detail-info-grid">
        <article class="info-card">
          <div class="info-card-label">标签</div>
          <div class="info-tag-row">
            <span v-for="tag in detail?.tags || []" :key="tag" class="info-tag">{{ tag }}</span>
            <span v-if="!(detail?.tags || []).length" class="info-tag empty">未设置标签</span>
          </div>
        </article>

        <article class="info-card">
          <div class="info-card-label">备注</div>
          <p class="info-note">{{ detail?.note || '暂无备注信息' }}</p>
        </article>
      </section>
    </section>

    <section v-if="loading" class="detail-loading-card">
      <el-skeleton animated>
        <template #template>
          <el-skeleton-item variant="h1" style="width: 32%; height: 28px; margin-bottom: 18px" />
          <el-skeleton-item variant="text" style="width: 56%; margin-bottom: 24px" />
          <el-skeleton-item variant="text" style="width: 100%; height: 220px; margin-bottom: 18px" />
          <el-skeleton-item variant="text" style="width: 100%; height: 220px" />
        </template>
      </el-skeleton>
    </section>

    <template v-else>
      <section class="detail-section-card">
        <div class="detail-section-head">
          <div>
            <div class="detail-section-overline">积分数据</div>
            <h3 class="detail-section-title">积分排行榜</h3>
            <p class="detail-section-description">展示当前小程序下用户积分明细和最近一次上报时间。</p>
          </div>
        </div>

        <el-table :data="detail?.ranking || []" stripe class="showcase-table">
          <el-table-column prop="nickname" label="昵称" min-width="160" />
          <el-table-column prop="wechat_id" label="微信号" min-width="180" />
          <el-table-column prop="device" label="设备" min-width="140" />
          <el-table-column prop="points" label="积分" width="120" />
          <el-table-column label="更新时间" min-width="180">
            <template #default="scope">{{ formatDate(scope.row.report_time) }}</template>
          </el-table-column>
        </el-table>
      </section>

      <section class="detail-section-card">
        <div class="detail-section-head stock-head">
          <div>
            <div class="detail-section-overline">库存数据</div>
            <h3 class="detail-section-title">库存详情</h3>
            <p class="detail-section-description">当前最高用户积分与商品库存状态一览。</p>
          </div>
          <div class="stock-highlight-card">
            <span class="stock-highlight-label">当前最高用户积分</span>
            <strong class="stock-highlight-value">{{ stock?.max_user_points ?? 0 }}</strong>
          </div>
        </div>

        <el-table :data="stock?.products || []" stripe class="showcase-table">
          <el-table-column prop="product_name" label="商品名称" min-width="260" />
          <el-table-column prop="points" label="所需积分" width="120" />
          <el-table-column prop="stock" label="库存" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.stock > 0 ? 'success' : 'danger'">{{ scope.row.stock }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

const route = useRoute()
const router = useRouter()
const programId = route.params.programId
const loading = ref(false)
const detail = ref(null)
const stock = ref(null)

function formatDate(value) {
  if (!value) return '暂无'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

function goBackToPrograms() {
  router.push({ path: '/programs', query: { restore: '1' } })
}

async function loadDetail() {
  loading.value = true
  try {
    const [detailResp, stockResp] = await Promise.all([
      api.get(`/programs/${programId}`),
      api.get(`/programs/${programId}/stock`),
    ])
    detail.value = detailResp.data
    stock.value = stockResp.data
  } catch (error) {
    console.error(error)
    ElMessage.error('加载小程序详情失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadDetail)
</script>

<style scoped>
.program-detail-page {
  position: relative;
  gap: 22px;
  padding: 6px 2px 18px;
}

.program-detail-page::before {
  content: '';
  position: fixed;
  inset: 0 0 0 260px;
  pointer-events: none;
  z-index: -1;
  background:
    linear-gradient(rgba(229, 209, 176, 0.16) 1px, transparent 1px),
    linear-gradient(90deg, rgba(229, 209, 176, 0.16) 1px, transparent 1px),
    linear-gradient(180deg, #fffaf0 0%, #fff7eb 100%);
  background-size: 24px 24px, 24px 24px, 100% 100%;
}

.detail-hero-card,
.detail-section-card,
.detail-loading-card {
  border-radius: 26px;
  border: 1px solid rgba(235, 220, 194, 0.88);
  background: rgba(255, 252, 247, 0.92);
  box-shadow: 0 10px 24px rgba(126, 98, 63, 0.04);
  backdrop-filter: blur(2px);
}

.detail-hero-card {
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding: 28px;
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

.detail-overline,
.detail-section-overline {
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
  margin: 14px 0 0;
  color: #6f5a44;
  font-size: 14px;
  line-height: 1.8;
  min-height: 52px;
}

.detail-loading-card {
  padding: 28px;
}

.detail-section-card {
  padding: 24px;
}

.detail-section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 18px;
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

@media (max-width: 1200px) {
  .detail-summary-grid,
  .detail-info-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .detail-hero-main,
  .detail-section-head,
  .stock-head {
    flex-direction: column;
  }

  .detail-hero-actions {
    justify-content: flex-start;
  }

  .stock-highlight-card {
    width: 100%;
    min-width: 0;
  }
}

@media (max-width: 680px) {
  .detail-hero-card,
  .detail-section-card,
  .detail-loading-card {
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
