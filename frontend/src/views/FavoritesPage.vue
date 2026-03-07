<template>
  <div class="page-stack">
    <el-card shadow="never">
      <template #header>
        <div class="section-header">
          <span>收藏小程序</span>
          <el-button text @click="loadFavorites">刷新</el-button>
        </div>
      </template>

      <el-skeleton v-if="loading" :rows="6" animated />
      <el-empty v-else-if="!items.length" description="暂无收藏小程序" />
      <div v-else class="program-grid">
        <el-card v-for="program in items" :key="program.program_id" class="program-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="title-wrap">
                <h3>{{ program.program_name || program.program_id }}</h3>
                <span class="program-id">{{ program.program_id }}</span>
              </div>
              <div class="card-actions">
                <el-button circle @click="router.push(`/programs/${program.program_id}`)">详</el-button>
              </div>
            </div>
          </template>

          <div class="meta-list">
            <div class="meta-item">
              <span class="meta-label">最近更新</span>
              <span class="meta-value">{{ formatDate(program.last_update_time) }}</span>
            </div>
          </div>

          <div class="tag-block">
            <div class="block-label">标签</div>
            <div class="tag-list content">
              <el-tag v-for="tag in program.tags || []" :key="tag" size="small" round>{{ tag }}</el-tag>
              <span v-if="!(program.tags || []).length" class="empty-text">暂无标签</span>
            </div>
          </div>
        </el-card>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

const router = useRouter()
const loading = ref(false)
const items = ref([])

function formatDate(value) {
  if (!value) return '暂无数据'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

async function loadFavorites() {
  loading.value = true
  try {
    const { data } = await api.get('/programs/favorites')
    items.value = data.items || []
  } catch (error) {
    console.error(error)
    ElMessage.error('加载收藏列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadFavorites)
</script>
