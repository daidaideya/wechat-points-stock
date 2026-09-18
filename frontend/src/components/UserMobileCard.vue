<template>
  <article class="users-mobile-card" :data-wechat-id="props.item.wechat_id">
    <div class="users-mobile-card-top">
      <div class="users-mobile-identity">
        <button
          type="button"
          class="users-drag-handle users-drag-handle-mobile"
          title="拖拽排序"
          aria-label="拖拽排序"
          @click.stop
        >
          <el-icon><Rank /></el-icon>
        </button>
        <div class="users-avatar" :style="{ background: avatarColor(props.item) }">{{ avatarChar(props.item) }}</div>
        <div class="users-mobile-title-wrap">
          <h3 class="users-mobile-title">
            <span class="users-sort-index-inline">{{ props.index + 1 }}.</span>
            {{ displayName(props.item) }}
          </h3>
          <div class="users-mobile-subtitle">{{ displayPrimaryId(props.item) }}</div>
        </div>
      </div>
      <div class="users-mobile-count-chips">
        <span class="users-mobile-count-chip">小程序 {{ props.item.active_program_count ?? 0 }}</span>
        <span class="users-mobile-count-chip app-chip">APP {{ props.item.active_app_count ?? 0 }}</span>
      </div>
    </div>

    <div class="users-mobile-meta-grid">
      <div class="users-mobile-meta-item">
        <span class="users-mobile-meta-label">设备</span>
        <span class="users-mobile-meta-value">{{ props.item.device || '未填写' }}</span>
      </div>
      <div class="users-mobile-meta-item">
        <span class="users-mobile-meta-label">手机号</span>
        <span class="users-mobile-meta-value">{{ displayPhone(props.item) || '未填写' }}</span>
      </div>
      <div v-if="displayWechatId(props.item)" class="users-mobile-meta-item">
        <span class="users-mobile-meta-label">微信号</span>
        <span class="users-mobile-meta-value">{{ displayWechatId(props.item) }}</span>
      </div>
    </div>

    <div class="users-mobile-actions">
      <div class="users-mobile-actions-main">
        <el-button size="small" @click="emit('edit', props.item)">编辑</el-button>
        <el-button size="small" @click="emit('view-points', props.item)">积分</el-button>
        <el-button
          size="small"
          type="danger"
          plain
          :loading="props.deletingWechatId === props.item.wechat_id"
          @click="emit('remove', props.item)"
        >
          删除
        </el-button>
      </div>
    </div>
  </article>
</template>

<script setup>
import { Rank } from '@element-plus/icons-vue'
import { avatarChar, avatarColor, displayName, displayPhone, displayPrimaryId, displayWechatId } from '../utils/user'

const props = defineProps({
  item: {
    type: Object,
    default: () => ({}),
  },
  index: {
    type: Number,
    default: 0,
  },
  deletingWechatId: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['edit', 'view-points', 'remove'])
</script>

<style scoped>
.users-drag-handle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  border: 0;
  border-radius: 10px;
  background: rgba(231, 179, 90, 0.14);
  color: #a16207;
  cursor: grab;
  touch-action: none;
  -webkit-user-select: none;
  user-select: none;
  transition:
    background 0.15s ease,
    color 0.15s ease,
    transform 0.15s ease;
}

.users-drag-handle:hover {
  background: rgba(231, 179, 90, 0.28);
  color: #92400e;
}

.users-drag-handle:active {
  cursor: grabbing;
  transform: scale(0.96);
}

.users-drag-handle :deep(.el-icon) {
  font-size: 16px;
}

.users-drag-handle-mobile {
  width: 36px;
  height: 36px;
  flex: 0 0 auto;
}

.users-avatar {
  flex: 0 0 auto;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  box-shadow: 0 6px 14px rgba(58, 43, 26, 0.18);
  background: linear-gradient(135deg, #e7b35a, #d89a3c);
  user-select: none;
}

.users-sort-index-inline {
  margin-right: 4px;
  color: #b87718;
  font-weight: 700;
}

.users-mobile-card.users-sortable-chosen {
  border-color: rgba(231, 179, 90, 0.9);
  box-shadow: 0 14px 28px rgba(145, 109, 61, 0.14);
}

.users-mobile-card.users-sortable-drag {
  border-color: rgba(231, 179, 90, 0.9);
  box-shadow: 0 14px 28px rgba(145, 109, 61, 0.14);
}

.users-sortable-ghost {
  opacity: 0.45;
}

.users-mobile-card {
  padding: 16px;
  border-radius: 20px;
  background: #fffdf9;
  border: 1px solid rgba(232, 211, 183, 0.9);
  box-shadow: 0 10px 24px rgba(145, 109, 61, 0.06);
}

.users-mobile-card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.users-mobile-identity {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.users-mobile-title-wrap {
  min-width: 0;
  flex: 1;
}

.users-mobile-title {
  margin: 0;
  color: #3a2b1a;
  font-size: 18px;
  line-height: 1.35;
}

.users-mobile-subtitle {
  margin-top: 6px;
  color: #8a6c4c;
  font-size: 12px;
  line-height: 1.6;
  word-break: break-all;
}

.users-mobile-count-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: flex-end;
}

.users-mobile-count-chip {
  flex: 0 0 auto;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(231, 179, 90, 0.16);
  color: #b87718;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.users-mobile-count-chip.app-chip {
  background: rgba(96, 165, 250, 0.16);
  color: #2563eb;
}

.users-mobile-meta-grid {
  margin-top: 14px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.users-mobile-meta-item {
  padding: 12px;
  border-radius: 16px;
  background: rgba(255, 248, 238, 0.9);
  border: 1px solid rgba(232, 211, 183, 0.72);
}

.users-mobile-meta-label {
  display: block;
  color: #8a6c4c;
  font-size: 11px;
}

.users-mobile-meta-value {
  display: block;
  margin-top: 6px;
  color: #3a2b1a;
  font-size: 13px;
  line-height: 1.5;
  word-break: break-all;
}

.users-mobile-actions {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.users-mobile-actions-main {
  display: inline-flex;
  gap: 8px;
  flex: 1;
}

@media (max-width: 640px) {
  .users-mobile-card-top {
    flex-direction: column;
    align-items: stretch;
  }

  .users-mobile-meta-grid {
    grid-template-columns: 1fr;
  }

  .users-mobile-actions-main {
    flex: 1 1 100%;
  }

  .users-mobile-actions-main :deep(.el-button) {
    flex: 1;
  }
}
</style>
