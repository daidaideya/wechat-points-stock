<template>
  <el-dialog
    :model-value="props.modelValue"
    :title="dialogTitle"
    :width="props.dialogWidth"
    :top="props.dialogTop"
    :fullscreen="props.fullscreen"
    class="showcase-dialog showcase-detail-dialog"
    destroy-on-close
    @update:model-value="handleModelUpdate"
  >
    <div class="showcase-dialog-body detail-dialog-body">
      <div class="showcase-dialog-intro">
        <div>
          <div class="showcase-dialog-title">{{ props.isAppList ? 'APP 详情' : '小程序详情' }}</div>
          <div class="showcase-dialog-subtitle">当前页查看积分排行与基础信息，无需跳转离开列表。</div>
        </div>
        <div class="stock-dialog-badges">
          <div class="showcase-dialog-badge stock-badge">{{ props.detailData?.is_favorite ? '已收藏' : '未收藏' }}</div>
          <div class="showcase-dialog-badge stock-badge">最高积分 {{ props.detailData?.max_user_points ?? 0 }}</div>
          <div class="showcase-dialog-badge stock-badge">排行 {{ detailRanking.length }}</div>
        </div>
      </div>

      <div v-if="props.loading" class="stock-loading dialog-panel">
        <el-skeleton :rows="6" animated />
      </div>
      <template v-else>
        <div class="stock-summary-grid">
          <div class="stock-summary-card dialog-panel">
            <div class="stock-summary-label">program_id</div>
            <div class="stock-summary-value mono-text detail-id-value">{{ props.detailData?.program_id || '—' }}</div>
          </div>
          <div class="stock-summary-card dialog-panel">
            <div class="stock-summary-label">最近更新</div>
            <div class="stock-summary-value detail-update-value">
              {{ props.formatDate(props.detailData?.last_update_time) }}
            </div>
          </div>
          <div class="stock-summary-card dialog-panel">
            <div class="stock-summary-label">标签数量</div>
            <div class="stock-summary-value">{{ (props.detailData?.tags || []).length || 0 }}</div>
          </div>
          <div class="stock-summary-card dialog-panel">
            <div class="stock-summary-label">最高用户积分</div>
            <div class="stock-summary-value success-text">{{ props.detailData?.max_user_points ?? 0 }}</div>
          </div>
        </div>

        <div class="detail-info-grid">
          <div class="dialog-panel detail-info-card">
            <div class="stock-section-title">标签</div>
            <div class="detail-tag-row">
              <span v-for="tag in props.detailData?.tags || []" :key="tag" class="info-tag">{{ tag }}</span>
              <span v-if="!(props.detailData?.tags || []).length" class="info-tag empty">未设置标签</span>
            </div>
          </div>
          <div class="dialog-panel detail-info-card">
            <div class="stock-section-title">备注</div>
            <p class="detail-note-text">{{ props.detailData?.note || '暂无备注信息' }}</p>
          </div>
        </div>

        <div class="dialog-panel stock-table-panel">
          <div class="stock-section-title-row">
            <div class="stock-section-title">积分排行榜</div>
            <div class="stock-section-hint">展示该小程序下账号最新积分</div>
          </div>
          <el-table :data="detailRanking" stripe class="showcase-dialog-table">
            <el-table-column type="index" label="#" width="60" />
            <el-table-column prop="nickname" label="昵称" min-width="120">
              <template #default="scope">{{ scope.row.nickname || '未命名' }}</template>
            </el-table-column>
            <!-- APP 排行优先展示手机号；小程序仍显示微信号 -->
            <el-table-column v-if="props.isAppList" label="手机号" min-width="150">
              <template #default="scope">{{ rankingPhone(scope.row) || '—' }}</template>
            </el-table-column>
            <el-table-column v-else label="微信号" min-width="160">
              <template #default="scope">{{ rankingWechatId(scope.row) || '—' }}</template>
            </el-table-column>
            <el-table-column v-if="props.isAppList" label="微信号" min-width="140">
              <template #default="scope">{{ rankingWechatId(scope.row) || '—' }}</template>
            </el-table-column>
            <el-table-column prop="device" label="设备" min-width="100">
              <template #default="scope">{{ scope.row.device || '—' }}</template>
            </el-table-column>
            <el-table-column prop="points" label="积分" width="100">
              <template #default="scope">{{ scope.row.points ?? 0 }}</template>
            </el-table-column>
            <el-table-column prop="cash" label="现金" width="100">
              <template #default="scope">
                {{ scope.row.cash == null || scope.row.cash === '' ? '—' : `¥${scope.row.cash}` }}
              </template>
            </el-table-column>
            <el-table-column label="更新时间" min-width="160">
              <template #default="scope">{{ props.formatDate(scope.row.report_time) }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!detailRanking.length" description="暂无积分排行数据" :image-size="80" />
        </div>
      </template>
    </div>
    <template #footer>
      <el-button @click="closeDialog">关闭</el-button>
      <el-button v-if="props.detailData?.has_stock" type="primary" @click="openStockFromDetail">查看库存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  dialogWidth: {
    type: String,
    default: '1040px',
  },
  dialogTop: {
    type: String,
    default: '5vh',
  },
  fullscreen: {
    type: Boolean,
    default: false,
  },
  isAppList: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  detailData: {
    type: Object,
    default: null,
  },
  formatDate: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits(['update:modelValue', 'open-stock'])

const detailRanking = computed(() => {
  const ranking = Array.isArray(props.detailData?.ranking) ? [...props.detailData.ranking] : []
  return ranking.sort((a, b) => {
    const ap = Number(a?.points) || 0
    const bp = Number(b?.points) || 0
    if (bp !== ap) return bp - ap
    const ac = Number(a?.cash) || 0
    const bc = Number(b?.cash) || 0
    return bc - ac
  })
})

const dialogTitle = computed(() => {
  if (!props.detailData?.program_name && !props.detailData?.program_id) {
    return props.isAppList ? 'APP 详情' : '小程序详情'
  }
  return `${props.detailData.program_name || props.detailData.program_id} - 详情`
})

function handleModelUpdate(value) {
  emit('update:modelValue', value)
}

function closeDialog() {
  handleModelUpdate(false)
}

function isPhoneLike(value) {
  return /^1[3-9]\d{9}$/.test(String(value || '').trim())
}

function rankingPhone(row) {
  const phone = String(row?.phone || '').trim()
  if (phone) return phone
  const wid = String(row?.wechat_id || '').trim()
  return isPhoneLike(wid) ? wid : ''
}

function rankingWechatId(row) {
  const wid = String(row?.wechat_id || '').trim()
  if (!wid || isPhoneLike(wid)) return ''
  return wid
}

function openStockFromDetail() {
  if (!props.detailData?.program_id || !props.detailData.has_stock) return
  closeDialog()
  emit('open-stock', props.detailData)
}
</script>

<style scoped>
.showcase-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.showcase-dialog-intro {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 2px 2px 6px;
}

.showcase-dialog-title {
  color: #3a2a1d;
  font-size: 16px;
  font-weight: 700;
}

.showcase-dialog-subtitle {
  margin-top: 6px;
  color: #9b7e5c;
  font-size: 13px;
  line-height: 1.6;
}

.showcase-dialog-badge {
  flex: 0 0 auto;
  padding: 8px 14px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(255, 244, 221, 0.96), rgba(255, 237, 213, 0.9));
  color: #8b5e34;
  font-size: 12px;
  font-weight: 700;
  box-shadow: inset 0 0 0 1px rgba(231, 202, 163, 0.72);
}

.stock-badge {
  color: #a16207;
}

.stock-dialog-badges {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.dialog-panel {
  padding: 16px 16px 14px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255, 251, 245, 0.96), rgba(255, 247, 235, 0.94));
  box-shadow: inset 0 0 0 1px rgba(235, 220, 194, 0.88);
}

.detail-info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-info-card {
  min-height: 110px;
}

.detail-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.info-tag {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 244, 221, 0.95);
  color: #8b5e34;
  font-size: 12px;
  font-weight: 700;
}

.info-tag.empty {
  background: rgba(248, 250, 252, 0.95);
  color: #94a3b8;
}

.detail-note-text {
  margin: 0;
  color: #4a3623;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.detail-id-value,
.detail-update-value {
  font-size: 15px !important;
}

.mono-text {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  word-break: break-all;
}

.stock-summary-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.stock-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.stock-section-title {
  margin-bottom: 12px;
  color: #7b5a37;
  font-size: 14px;
  font-weight: 700;
}

.stock-section-title-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.stock-section-title-row .stock-section-title {
  margin-bottom: 0;
}

.stock-section-hint {
  color: #9b7e5c;
  font-size: 12px;
  line-height: 1.4;
  text-align: right;
}

.stock-summary-label {
  color: #9b7e5c;
  font-size: 13px;
  font-weight: 600;
}

.stock-summary-value {
  color: #a16207;
  font-size: 30px;
  line-height: 1;
  font-weight: 800;
}

.success-text {
  color: #15803d;
}

.stock-table-panel {
  padding-top: 12px;
}

.showcase-dialog-table :deep(.el-table) {
  --el-table-border-color: rgba(236, 221, 199, 0.92);
  --el-table-header-bg-color: rgba(255, 248, 238, 0.96);
  --el-table-tr-bg-color: rgba(255, 253, 249, 0.96);
  --el-table-row-hover-bg-color: rgba(255, 245, 229, 0.92);
  --el-table-text-color: #57412d;
  --el-table-header-text-color: #8b5e34;
}

.showcase-dialog-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.showcase-dialog-table :deep(th.el-table__cell) {
  font-weight: 700;
}

.showcase-dialog-table :deep(.el-table__cell) {
  padding: 14px 0;
}

.stock-loading {
  padding: 16px;
}

.showcase-dialog :deep(.el-dialog) {
  border-radius: 28px;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(255, 253, 249, 0.98), rgba(255, 248, 238, 0.98));
  box-shadow: 0 26px 60px rgba(97, 72, 43, 0.16);
}

.showcase-dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding: 24px 28px 10px;
}

.showcase-dialog :deep(.el-dialog__title) {
  color: #2f2418;
  font-size: 22px;
  font-weight: 800;
}

.showcase-dialog :deep(.el-dialog__body) {
  padding: 8px 28px 18px;
}

.showcase-dialog :deep(.el-dialog__footer) {
  padding: 10px 28px 26px;
}

.showcase-dialog :deep(.el-dialog__headerbtn) {
  top: 24px;
  right: 24px;
}

.showcase-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #a18461;
}

.showcase-dialog :deep(.el-dialog__footer .el-button) {
  min-width: 92px;
  height: 40px;
  border-radius: 14px;
}

.showcase-dialog :deep(.el-dialog__footer .el-button--default) {
  border-color: rgba(219, 183, 141, 0.74);
  color: #8b5e34;
  background: #fff9f2;
}

.showcase-dialog :deep(.el-dialog__footer .el-button--primary) {
  border: 0;
  background: linear-gradient(135deg, #f0c37c, #d9a25f);
  box-shadow: 0 12px 24px rgba(219, 162, 88, 0.22);
}

@media (max-width: 768px) {
  .detail-info-grid,
  .stock-summary-grid {
    grid-template-columns: 1fr;
  }

  .showcase-dialog :deep(.el-dialog) {
    margin: 0 auto;
    max-width: 100vw;
  }

  .showcase-dialog :deep(.el-dialog__body) {
    max-height: min(78vh, 720px);
    overflow: auto;
    -webkit-overflow-scrolling: touch;
  }

  .showcase-dialog.is-fullscreen :deep(.el-dialog__body) {
    max-height: none;
  }

  .showcase-dialog-table {
    width: 100%;
  }

  .showcase-dialog-table :deep(.el-table) {
    width: 100% !important;
  }

  .showcase-dialog-table :deep(.el-table__body-wrapper) {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
}
</style>
