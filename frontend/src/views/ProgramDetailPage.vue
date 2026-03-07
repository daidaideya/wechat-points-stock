<template>
  <div class="page-stack">
    <el-card shadow="never">
      <template #header>
        <div class="section-header">
          <span>{{ detail?.program_name || programId }}</span>
          <div class="section-actions">
            <el-button @click="loadDetail">刷新</el-button>
            <el-button @click="router.push('/programs')">返回列表</el-button>
          </div>
        </div>
      </template>

      <el-skeleton v-if="loading" :rows="8" animated />
      <div v-else class="page-stack">
        <section class="summary-row">
          <el-card shadow="never" class="summary-card">
            <div class="summary-label">program_id</div>
            <div class="summary-value small">{{ detail?.program_id }}</div>
          </el-card>
          <el-card shadow="never" class="summary-card">
            <div class="summary-label">收藏状态</div>
            <div class="summary-value small">{{ detail?.is_favorite ? '已收藏' : '未收藏' }}</div>
          </el-card>
          <el-card shadow="never" class="summary-card">
            <div class="summary-label">最近更新</div>
            <div class="summary-value small">{{ formatDate(detail?.last_update_time) }}</div>
          </el-card>
        </section>

        <el-card shadow="never">
          <template #header>积分排行榜</template>
          <el-table :data="detail?.ranking || []" stripe>
            <el-table-column prop="nickname" label="昵称" min-width="160" />
            <el-table-column prop="wechat_id" label="微信号" min-width="180" />
            <el-table-column prop="device" label="设备" min-width="140" />
            <el-table-column prop="points" label="积分" width="120" />
            <el-table-column label="更新时间" min-width="180">
              <template #default="scope">{{ formatDate(scope.row.report_time) }}</template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="never">
          <template #header>库存详情</template>
          <div class="stock-summary">当前最高用户积分：<strong>{{ stock?.max_user_points ?? 0 }}</strong></div>
          <el-table :data="stock?.products || []" stripe>
            <el-table-column prop="product_name" label="商品名称" min-width="240" />
            <el-table-column prop="points" label="所需积分" width="120" />
            <el-table-column prop="stock" label="库存" width="100" />
          </el-table>
        </el-card>
      </div>
    </el-card>
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
