<template>
  <el-table :data="props.items" stripe row-key="wechat_id" class="users-table">
    <el-table-column label="排序" width="88" align="center">
      <template #default="scope">
        <div class="users-sort-cell">
          <button type="button" class="users-drag-handle" title="拖拽排序" aria-label="拖拽排序" @click.stop>
            <el-icon><Rank /></el-icon>
          </button>
          <span class="users-sort-index">{{ scope.$index + 1 }}</span>
        </div>
      </template>
    </el-table-column>
    <el-table-column label="昵称" min-width="180">
      <template #default="scope">
        <div class="users-table-identity">
          <div class="users-avatar users-avatar-sm" :style="{ background: avatarColor(scope.row) }">
            {{ avatarChar(scope.row) }}
          </div>
          <span class="users-table-nickname">{{ displayName(scope.row) }}</span>
        </div>
      </template>
    </el-table-column>
    <el-table-column label="手机号" min-width="150">
      <template #default="scope">{{ displayPhone(scope.row) || '—' }}</template>
    </el-table-column>
    <el-table-column label="微信号" min-width="180">
      <template #default="scope">{{ displayWechatId(scope.row) || '—' }}</template>
    </el-table-column>
    <el-table-column prop="device" label="设备" min-width="140" />
    <el-table-column prop="active_program_count" label="活跃小程序" width="110" align="center" />
    <el-table-column prop="active_app_count" label="活跃APP" width="100" align="center" />
    <el-table-column label="操作" width="240" fixed="right">
      <template #default="scope">
        <el-button size="small" @click="emit('edit', scope.row, $event)">编辑</el-button>
        <el-button size="small" @click="emit('view-points', scope.row, $event)">积分</el-button>
        <el-button
          size="small"
          type="danger"
          plain
          :loading="props.deletingWechatId === scope.row.wechat_id"
          @click="emit('remove', scope.row)"
        >
          删除
        </el-button>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
import { Rank } from '@element-plus/icons-vue'
import { avatarChar, avatarColor, displayName, displayPhone, displayWechatId } from '../utils/user'

const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  deletingWechatId: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['edit', 'view-points', 'remove'])
</script>

<style scoped>
.users-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.users-table :deep(th.el-table__cell) {
  background: rgba(255, 248, 238, 0.9);
  color: #8a6c4c;
}

.users-table :deep(td.el-table__cell) {
  background: rgba(255, 253, 249, 0.96);
}

.users-sort-cell {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
}

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

.users-sort-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(231, 179, 90, 0.16);
  color: #b87718;
  font-size: 12px;
  font-weight: 700;
}

.users-table-identity {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  max-width: 100%;
}

.users-table-nickname {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.users-avatar-sm {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  font-size: 14px;
  box-shadow: 0 4px 10px rgba(58, 43, 26, 0.14);
}

:deep(.users-sortable-ghost) {
  opacity: 0.45;
}

:deep(.users-sortable-chosen) {
  box-shadow: 0 10px 24px rgba(145, 109, 61, 0.16);
}

:deep(.users-sortable-drag) {
  opacity: 0.95;
}

:global(.sortable-fallback.users-sortable-drag),
:global(.sortable-fallback) {
  opacity: 0.95 !important;
}
</style>
