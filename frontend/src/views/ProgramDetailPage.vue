<template>
  <div class="page-stack program-detail-page">
    <ProgramDetailOverview
      :program-id="programId"
      :detail="detail"
      :stock="stock"
      :format-date="formatDate"
      @refresh="loadDetail"
      @back="goBackToPrograms"
    />

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

    <ProgramDetailDataSections v-else :detail="detail" :stock="stock" :format-date="formatDate" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'
import ProgramDetailDataSections from '../components/ProgramDetailDataSections.vue'
import ProgramDetailOverview from '../components/ProgramDetailOverview.vue'
import { useAbortableRequest } from '../composables/useAbortableRequest'
import { getApiErrorMessage, isRequestCanceled } from '../utils/apiError'

const route = useRoute()
const router = useRouter()
const programId = String(route.params.programId || '')
const loading = ref(false)
const detail = ref(null)
const stock = ref(null)
const requestController = useAbortableRequest()

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
  const request = requestController.start()
  loading.value = true
  try {
    const [detailResp, stockResp] = await Promise.all([
      api.get(`/programs/${programId}`, { signal: request.signal }),
      api.get(`/programs/${programId}/stock`, { signal: request.signal }),
    ])
    if (!request.isCurrent()) return
    detail.value = detailResp.data
    stock.value = stockResp.data
  } catch (error) {
    if (!request.isCurrent() || isRequestCanceled(error)) return
    console.error(error)
    ElMessage.error(getApiErrorMessage(error, '加载小程序详情失败'))
  } finally {
    if (request.isCurrent()) {
      loading.value = false
      request.finish()
    }
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
  background-size:
    24px 24px,
    24px 24px,
    100% 100%;
}

.detail-loading-card {
  padding: 28px;
  border-radius: 26px;
  border: 1px solid rgba(235, 220, 194, 0.88);
  background: rgba(255, 252, 247, 0.92);
  box-shadow: 0 10px 24px rgba(126, 98, 63, 0.04);
  backdrop-filter: blur(2px);
}
</style>
