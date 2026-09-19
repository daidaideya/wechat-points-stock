<template>
  <div class="showcase-card-footer compact-footer">
    <div class="showcase-footer-meta">
      <span class="showcase-footer-icon">◔</span>
      <span class="showcase-footer-time">{{ props.formatDate(props.program.last_update_time) }}</span>
    </div>

    <div class="mobile-primary-actions">
      <button
        type="button"
        class="mobile-text-action stock-action"
        :class="{ 'is-disabled-action': !props.program.has_stock }"
        :disabled="!props.program.has_stock"
        @click="emitOpenStock"
      >
        <el-icon><Box /></el-icon>
        <span>库存</span>
      </button>
      <button type="button" class="mobile-text-action detail-action" @click="emitOpenDetail">
        <el-icon><ArrowRight /></el-icon>
        <span>详情</span>
      </button>
    </div>

    <div class="showcase-card-actions footer-actions ref-action-group">
      <el-tooltip content="编辑备注" placement="top" :disabled="props.isTouchLayout">
        <button
          type="button"
          class="showcase-icon-button ref-action-button icon-plain-button"
          title="编辑备注"
          @click="emitOpenNote"
        >
          <el-icon><EditPen /></el-icon>
        </button>
      </el-tooltip>

      <el-tooltip
        :content="props.program.has_stock ? '查看库存' : '暂无库存可查看'"
        placement="top"
        :disabled="props.isTouchLayout"
      >
        <span class="action-tooltip-wrap desktop-only-action">
          <button
            type="button"
            class="showcase-icon-button ref-action-button icon-plain-button"
            :class="{ 'is-disabled-action': !props.program.has_stock }"
            :disabled="!props.program.has_stock"
            :title="props.program.has_stock ? '查看库存' : '暂无库存可查看'"
            @click="emitOpenStock"
          >
            <el-icon><Box /></el-icon>
          </button>
        </span>
      </el-tooltip>

      <el-tooltip
        :content="props.program.is_favorite ? '取消收藏' : '加入收藏'"
        placement="top"
        :disabled="props.isTouchLayout"
      >
        <button
          type="button"
          class="showcase-icon-button ref-action-button favorite-toggle ref-action-button-favorite icon-plain-button"
          :class="{ active: props.program.is_favorite }"
          :title="props.program.is_favorite ? '取消收藏' : '加入收藏'"
          @click="emitToggleFavorite"
        >
          <el-icon v-if="props.updatingProgramId !== props.program.program_id"><Star /></el-icon>
          <span v-else class="showcase-button-loading">...</span>
        </button>
      </el-tooltip>

      <el-tooltip
        :content="(props.program.tags || []).length ? '编辑标签' : '添加标签'"
        placement="top"
        :disabled="props.isTouchLayout"
      >
        <button
          type="button"
          class="showcase-icon-button ref-action-button icon-plain-button"
          title="编辑标签"
          @click="emitOpenTags"
        >
          <el-icon><CollectionTag /></el-icon>
        </button>
      </el-tooltip>

      <el-tooltip content="查看详情" placement="top" :disabled="props.isTouchLayout">
        <button
          type="button"
          class="showcase-icon-button ref-action-button icon-plain-button desktop-only-action"
          title="查看详情"
          @click="emitOpenDetail"
        >
          <el-icon><ArrowRight /></el-icon>
        </button>
      </el-tooltip>

      <el-dropdown trigger="click" placement="top-end" @command="emitCommand">
        <button
          type="button"
          title="更多操作"
          class="showcase-icon-button ref-action-button icon-plain-button"
          :disabled="isMoreActionBusy"
          @click.stop
        >
          <el-icon v-if="!isMoreActionBusy"><MoreFilled /></el-icon>
          <span v-else class="showcase-button-loading">...</span>
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="archive">
              <el-icon><Box /></el-icon>
              <span>{{ props.program.is_archived ? '取消归档' : '归档' }}</span>
            </el-dropdown-item>
            <el-dropdown-item command="delete" divided>
              <el-icon><Delete /></el-icon>
              <span class="dropdown-danger-text">删除</span>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ArrowRight, Box, CollectionTag, Delete, EditPen, MoreFilled, Star } from '@element-plus/icons-vue'

const props = defineProps({
  program: { type: Object, required: true },
  isTouchLayout: { type: Boolean, default: false },
  updatingProgramId: { type: String, default: '' },
  archivingProgramId: { type: String, default: '' },
  deletingProgramId: { type: String, default: '' },
  formatDate: { type: Function, required: true },
})

const isMoreActionBusy = computed(
  () => props.archivingProgramId === props.program.program_id || props.deletingProgramId === props.program.program_id,
)

const emit = defineEmits(['open-tags', 'open-stock', 'open-detail', 'open-note', 'toggle-favorite', 'command'])

function emitOpenTags() {
  emit('open-tags', props.program)
}

function emitOpenStock() {
  if (props.program.has_stock) emit('open-stock', props.program)
}

function emitOpenDetail() {
  emit('open-detail', props.program)
}

function emitOpenNote() {
  emit('open-note', props.program)
}

function emitToggleFavorite() {
  emit('toggle-favorite', props.program)
}

function emitCommand(command) {
  emit('command', command, props.program)
}
</script>

<style scoped>
.showcase-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid rgba(236, 220, 196, 0.75);
}

.compact-footer {
  align-items: center;
  flex-wrap: wrap;
}

.showcase-footer-meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex-wrap: nowrap;
  white-space: nowrap;
  color: #8e7454;
  font-size: 12px;
}

.showcase-footer-time {
  white-space: nowrap;
}

.showcase-footer-icon {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 243, 225, 0.92);
  color: #a16207;
  font-size: 12px;
}

.footer-actions {
  padding: 4px;
  border-radius: 14px;
  background: rgba(255, 248, 236, 0.88);
  box-shadow: inset 0 0 0 1px rgba(232, 210, 184, 0.72);
}

.showcase-card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
  flex: 0 0 auto;
}

.ref-action-group {
  gap: 6px;
}

.mobile-primary-actions {
  display: none;
}

.mobile-text-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 40px;
  min-width: 0;
  padding: 0 14px;
  border: 0;
  border-radius: 12px;
  background: linear-gradient(135deg, #fff8ef, #fff1df);
  color: #8b5e34;
  font-size: 13px;
  font-weight: 700;
  box-shadow: inset 0 0 0 1px rgba(232, 210, 184, 0.85);
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
}

.mobile-text-action.detail-action {
  background: linear-gradient(135deg, #f0c37c, #d9a25f);
  color: #fff;
  box-shadow: 0 8px 16px rgba(219, 162, 88, 0.22);
}

.mobile-text-action.is-disabled-action,
.mobile-text-action:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  box-shadow: none;
  background: rgba(245, 240, 232, 0.95);
  color: #b7a28a;
}

.showcase-icon-button {
  width: 36px;
  height: 36px;
  min-width: 36px;
  min-height: 36px;
  border: 0;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: #8a6c4c;
  box-shadow: none;
  cursor: pointer;
  transition:
    color 0.18s ease,
    transform 0.18s ease,
    background 0.18s ease,
    box-shadow 0.18s ease;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
}

.ref-action-button {
  padding: 0;
  background: transparent;
  color: #6f7783;
  box-shadow: none;
}

.icon-plain-button {
  min-width: 36px;
  line-height: 1;
  opacity: 1;
}

.ref-action-button:hover {
  color: #4b5563;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 6px 14px rgba(126, 98, 63, 0.08);
  transform: translateY(-1px);
}

.action-tooltip-wrap {
  display: inline-flex;
}

.ref-action-button:disabled,
.ref-action-button.is-disabled-action,
.ref-action-button:disabled:hover,
.ref-action-button.is-disabled-action:hover {
  color: #c4b5a0;
  background: rgba(245, 240, 232, 0.9);
  box-shadow: none;
  transform: none;
  cursor: not-allowed;
  opacity: 0.72;
}

.ref-action-button-favorite.active {
  color: #e5a22d;
  background: rgba(255, 248, 230, 0.98);
  opacity: 1;
}

.ref-action-button-favorite.active:hover {
  color: #d99623;
  background: rgba(255, 244, 214, 0.98);
}

.showcase-button-loading {
  font-size: 12px;
  letter-spacing: 0.2em;
}

.dropdown-danger-text {
  color: #c2410c;
  font-weight: 600;
}

@media (max-width: 768px) {
  .showcase-card-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .showcase-card-footer.compact-footer {
    gap: 10px;
  }

  .showcase-footer-meta {
    width: 100%;
  }

  .mobile-primary-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    width: 100%;
  }

  .mobile-text-action {
    width: 100%;
    min-height: 44px;
  }

  .showcase-card-actions {
    justify-content: space-between;
    flex-wrap: nowrap;
    width: 100%;
  }

  .ref-action-group {
    gap: 4px;
    width: 100%;
    justify-content: space-between;
  }

  .showcase-icon-button,
  .icon-plain-button {
    width: 44px;
    height: 44px;
    min-width: 44px;
    min-height: 44px;
    border-radius: 14px;
  }

  .desktop-only-action {
    display: none !important;
  }

  .compact-footer {
    align-items: stretch;
    justify-content: flex-start;
  }

  .footer-actions {
    justify-content: space-between;
    width: 100%;
    padding: 6px;
  }
}

@media (max-width: 480px) {
  .showcase-footer-time {
    font-size: 11px;
  }

  .ref-action-group {
    gap: 2px;
  }
}
</style>
