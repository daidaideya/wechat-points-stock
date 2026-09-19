<template>
  <section class="dashboard-bottom-grid aligned-dashboard-grid">
    <el-card shadow="never" class="dashboard-panel-card recent-panel-card aligned-list-card">
      <template #header>
        <div class="dashboard-panel-header aligned-panel-header">
          <div class="dashboard-panel-title-wrap">
            <span class="dashboard-panel-icon soft-blue">
              <el-icon><Clock /></el-icon>
            </span>
            <div>
              <div class="dashboard-panel-title">最新小程序更新</div>
              <div class="dashboard-panel-subtitle">快速查看最近同步的记录与时间</div>
            </div>
          </div>
          <el-button text @click="emit('refresh')">刷新</el-button>
        </div>
      </template>

      <el-skeleton v-if="props.loading" :rows="6" animated />
      <el-empty v-else-if="!props.recentUpdates.length" description="暂无更新记录" />
      <div v-else class="recent-update-list aligned-panel-list">
        <div
          v-for="item in props.recentUpdates"
          :key="`${item.program_id}-${item.wechat_id}-${item.report_time}`"
          class="recent-update-item aligned-list-item"
        >
          <div class="recent-update-main">
            <div class="recent-update-name-row">
              <span class="recent-update-name">{{ item.program_name || item.program_id || '未知小程序' }}</span>
              <el-tag size="small" round effect="plain">{{ item.points ?? 0 }} 积分</el-tag>
            </div>
            <div class="recent-update-meta">
              <span>{{ item.program_id || '未知 AppID' }}</span>
              <span>{{ item.wechat_id || '未知微信号' }}</span>
            </div>
          </div>
          <div class="recent-update-time">{{ props.formatDate(item.report_time) }}</div>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="dashboard-panel-card dashboard-side-panel aligned-list-card">
      <template #header>
        <div class="dashboard-panel-header aligned-panel-header">
          <div class="dashboard-panel-title-wrap">
            <span class="dashboard-panel-icon soft-orange">
              <el-icon><Warning /></el-icon>
            </span>
            <div>
              <div class="dashboard-panel-title">今天没报的小程序</div>
              <div class="dashboard-panel-subtitle">当天尚未同步积分的小程序列表</div>
            </div>
          </div>
          <el-tag round effect="plain" type="danger">{{ props.unreportedPrograms.length }} 个</el-tag>
        </div>
      </template>

      <el-skeleton v-if="props.loading" :rows="6" animated />
      <el-empty v-else-if="!props.unreportedPrograms.length" description="今天全部已上报" />
      <div v-else class="recent-update-list aligned-panel-list unreported-program-list">
        <div
          v-for="item in props.unreportedPrograms"
          :key="item.program_id"
          class="recent-update-item aligned-list-item unreported-program-item"
        >
          <div class="recent-update-main">
            <div class="recent-update-name-row">
              <span class="recent-update-name">{{ item.program_name || item.program_id || '未知小程序' }}</span>
              <el-tag size="small" round effect="plain" :type="item.is_favorite ? 'warning' : 'info'">
                {{ item.is_favorite ? '重点关注' : '待上报' }}
              </el-tag>
            </div>
            <div class="recent-update-meta">
              <span>{{ item.program_id || '未知 AppID' }}</span>
              <span v-if="(item.tags || []).length">{{ item.tags.join(' / ') }}</span>
              <span v-else>暂无标签</span>
            </div>
          </div>
          <div class="recent-update-time">{{ props.formatDate(item.last_report_time || item.last_update_time) }}</div>
        </div>
      </div>
    </el-card>
  </section>

  <el-dialog
    :model-value="props.unreportedDialogVisible"
    title="今天没报的小程序"
    width="960px"
    class="dashboard-unreported-dialog"
    @update:model-value="emit('update:unreported-dialog-visible', $event)"
  >
    <div
      v-if="props.unreportedDialogLoading"
      class="dashboard-dialog-loading"
      role="status"
      aria-live="polite"
      aria-busy="true"
      aria-label="正在加载未上报小程序"
    >
      <el-skeleton :rows="8" animated />
    </div>
    <el-empty v-else-if="!props.allUnreportedPrograms.length" description="今天全部已上报" />
    <div v-else class="dashboard-dialog-list">
      <div v-for="item in props.allUnreportedPrograms" :key="`dialog-${item.program_id}`" class="dashboard-dialog-item">
        <div class="dashboard-dialog-main">
          <div class="dashboard-dialog-name-row">
            <span class="dashboard-dialog-name">{{ item.program_name || item.program_id || '未知小程序' }}</span>
            <el-tag size="small" round effect="plain" :type="item.is_favorite ? 'warning' : 'info'">
              {{ item.is_favorite ? '重点关注' : '待上报' }}
            </el-tag>
          </div>
          <div class="dashboard-dialog-meta">
            <span>{{ item.program_id || '未知 AppID' }}</span>
            <span v-if="(item.tags || []).length">{{ item.tags.join(' / ') }}</span>
            <span v-else>暂无标签</span>
            <span v-if="item.note">备注：{{ item.note }}</span>
          </div>
        </div>
        <div class="dashboard-dialog-time">{{ props.formatDate(item.last_report_time || item.last_update_time) }}</div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { Clock, Warning } from '@element-plus/icons-vue'

const props = defineProps({
  loading: { type: Boolean, default: false },
  recentUpdates: { type: Array, default: () => [] },
  unreportedPrograms: { type: Array, default: () => [] },
  allUnreportedPrograms: { type: Array, default: () => [] },
  unreportedDialogVisible: { type: Boolean, default: false },
  unreportedDialogLoading: { type: Boolean, default: false },
  formatDate: { type: Function, required: true },
})

const emit = defineEmits(['refresh', 'update:unreported-dialog-visible'])
</script>
