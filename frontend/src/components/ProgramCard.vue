<template>
  <article
    class="showcase-card masonry-card"
    :class="{
      'is-favorite': props.program.is_favorite,
      'has-stock': props.program.has_stock,
      'is-archived': props.program.is_archived,
    }"
  >
    <div v-if="props.program.is_archived" class="archived-badge">已归档</div>
    <div class="showcase-card-top">
      <div class="showcase-card-brand no-avatar-brand">
        <div class="showcase-card-brand-text full-width-brand-text">
          <div class="showcase-card-title-line">
            <span class="showcase-card-index" :title="`第 ${props.index + 1} 个`">{{ props.index + 1 }}</span>
            <h3
              class="showcase-card-title is-copyable"
              :class="props.titleSizeClass(props.program.program_name || props.program.program_id)"
              :title="`${props.program.program_name || props.program.program_id}（点击复制名称）`"
              role="button"
              tabindex="0"
              @click.stop="emitCopyName"
              @keydown.enter.prevent="emitCopyName"
              @keydown.space.prevent="emitCopyName"
            >
              {{ props.program.program_name || props.program.program_id }}
            </h3>
            <el-tooltip
              v-if="props.program.ql_status === 'enabled'"
              :content="props.program.ql_cron_name ? `青龙已启用：${props.program.ql_cron_name}` : '青龙：已启用'"
              placement="top"
            >
              <span class="ql-status-badge is-enabled" aria-label="青龙已启用">
                <el-icon><CircleCheck /></el-icon>
              </span>
            </el-tooltip>
            <el-tooltip
              v-else-if="props.program.ql_status === 'disabled'"
              :content="props.program.ql_cron_name ? `青龙已禁用：${props.program.ql_cron_name}` : '青龙：已禁用'"
              placement="top"
            >
              <span class="ql-status-badge is-disabled" aria-label="青龙已禁用">
                <el-icon><CircleClose /></el-icon>
              </span>
            </el-tooltip>
          </div>
          <div class="showcase-card-meta-row compact-meta-row">
            <span
              class="showcase-card-dot stock-dot"
              :class="{ active: props.isUpdatedToday(props.program.last_update_time) }"
            ></span>
            <span
              class="showcase-card-id is-copyable"
              :title="`${props.program.program_id}（点击复制 program_id）`"
              role="button"
              tabindex="0"
              @click.stop="emitCopyId"
              @keydown.enter.prevent="emitCopyId"
              @keydown.space.prevent="emitCopyId"
              v-text="props.program.program_id"
            ></span>
            <el-tooltip
              v-if="props.program.ql_schedule"
              :content="props.formatQlScheduleTooltip(props.program)"
              placement="top"
            >
              <span class="ql-schedule-chip" :class="`is-${props.program.ql_status || 'unknown'}`">
                <span class="ql-schedule-label">定时</span>
                <code class="ql-schedule-code">{{ props.program.ql_schedule }}</code>
              </span>
            </el-tooltip>
          </div>
          <div
            class="showcase-card-tag-row"
            role="button"
            tabindex="0"
            @click.stop="emitOpenTags"
            @keydown.enter.prevent="emitOpenTags"
            @keydown.space.prevent="emitOpenTags"
          >
            <span v-if="(props.program.tags || []).length" class="showcase-chip success inline-tag-chip">
              标签：{{ (props.program.tags || []).join(' / ') }}
            </span>
            <span v-else class="showcase-chip warning inline-tag-chip">标签：未设置标签</span>
          </div>
          <ProgramMetricStrip :program="props.program" @open-stock="emitOpenStock" />
        </div>
      </div>
    </div>

    <p class="showcase-card-note masonry-note" :class="{ empty: !props.program.note }">
      {{ props.program.note || '暂无备注' }}
    </p>

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
  </article>
</template>

<script setup>
import { computed } from 'vue'
import {
  ArrowRight,
  Box,
  CircleCheck,
  CircleClose,
  CollectionTag,
  Delete,
  EditPen,
  MoreFilled,
  Star,
} from '@element-plus/icons-vue'
import ProgramMetricStrip from './ProgramMetricStrip.vue'

const props = defineProps({
  program: { type: Object, required: true },
  index: { type: Number, required: true },
  isTouchLayout: { type: Boolean, default: false },
  updatingProgramId: { type: String, default: '' },
  archivingProgramId: { type: String, default: '' },
  deletingProgramId: { type: String, default: '' },
  titleSizeClass: { type: Function, required: true },
  isUpdatedToday: { type: Function, required: true },
  formatDate: { type: Function, required: true },
  formatQlScheduleTooltip: { type: Function, required: true },
})

const isMoreActionBusy = computed(
  () => props.archivingProgramId === props.program.program_id || props.deletingProgramId === props.program.program_id,
)

const emit = defineEmits([
  'copy-name',
  'copy-id',
  'open-tags',
  'open-stock',
  'open-detail',
  'open-note',
  'toggle-favorite',
  'command',
])

function emitCopyName() {
  emit('copy-name', props.program)
}

function emitCopyId() {
  emit('copy-id', props.program)
}

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
.showcase-card {
  position: relative;
  display: flex;
  width: 100%;
  flex-direction: column;
  min-height: 0;
  margin: 0;
  padding: 22px;
  border-radius: 24px;
  background: #fffdf9;
  border: 1px solid rgba(239, 226, 208, 0.95);
  box-shadow: 0 8px 18px rgba(126, 98, 63, 0.05);
  overflow: hidden;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.showcase-card:hover {
  transform: translateY(-2px);
  border-color: rgba(230, 196, 154, 0.98);
  box-shadow: 0 10px 24px rgba(126, 98, 63, 0.07);
}

.showcase-card.is-favorite {
  border-color: rgba(240, 196, 113, 0.72);
}

.showcase-card.is-archived {
  opacity: 0.62;
  filter: grayscale(0.55);
  background: rgba(248, 244, 235, 0.92);
}

.showcase-card.is-archived:hover {
  opacity: 0.85;
  filter: grayscale(0.2);
}

.archived-badge {
  position: absolute;
  top: 14px;
  right: 14px;
  z-index: 1;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(120, 113, 108, 0.92);
  color: #f5f5f4;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  box-shadow: 0 4px 10px rgba(68, 64, 60, 0.18);
  pointer-events: none;
}

.showcase-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.showcase-card-brand {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  min-width: 0;
  flex: 1;
}

.no-avatar-brand {
  gap: 0;
}

.full-width-brand-text,
.showcase-card-brand-text {
  min-width: 0;
  width: 100%;
}

.showcase-card-title-line {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 8px;
  min-width: 0;
  width: 100%;
}

.showcase-card-title {
  margin: 0;
  flex: 1 1 auto;
  min-width: 0;
  color: #2f2418;
  font-size: 18px;
  line-height: 1.25;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.showcase-card-title.is-title-md {
  font-size: 16px;
}

.showcase-card-title.is-title-sm {
  font-size: 14px;
}

.showcase-card-title.is-title-xs {
  font-size: 12px;
  letter-spacing: -0.02em;
}

.showcase-card-title.is-copyable,
.showcase-card-id.is-copyable {
  cursor: pointer;
}

.showcase-card-title.is-copyable:hover {
  color: #a16207;
}

.showcase-card-id.is-copyable:hover {
  color: #b7791f;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.showcase-card-title.is-copyable:focus-visible,
.showcase-card-id.is-copyable:focus-visible {
  outline: 2px solid rgba(214, 169, 107, 0.55);
  outline-offset: 2px;
  border-radius: 6px;
}

.showcase-card-index {
  flex: 0 0 auto;
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 24px;
  padding: 0 8px;
  margin-top: 3px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(255, 244, 221, 0.96), rgba(255, 237, 213, 0.9));
  color: #8b5e34;
  font-size: 12px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: 0.02em;
  font-variant-numeric: tabular-nums;
  box-shadow: inset 0 0 0 1px rgba(231, 202, 163, 0.72);
}

.showcase-card-meta-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
  color: #9b7e5c;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.01em;
  min-width: 0;
  width: 100%;
}

.compact-meta-row {
  margin-right: 0;
}

.showcase-card-id {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 0 1 auto;
  min-width: 0;
}

.showcase-card-tag-row {
  display: flex;
  justify-content: flex-start;
  margin-top: 6px;
  min-width: 0;
  cursor: pointer;
}

.ql-status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  flex: 0 0 auto;
  flex-shrink: 0;
  font-size: 14px;
}

.ql-status-badge.is-enabled {
  color: #15803d;
  background: rgba(220, 252, 231, 0.95);
  box-shadow: inset 0 0 0 1px rgba(34, 197, 94, 0.35);
}

.ql-status-badge.is-disabled {
  color: #b91c1c;
  background: rgba(254, 226, 226, 0.95);
  box-shadow: inset 0 0 0 1px rgba(248, 113, 113, 0.4);
}

.ql-schedule-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  min-width: 0;
  margin-left: 4px;
  padding: 2px 8px 2px 6px;
  border-radius: 999px;
  background: rgba(241, 245, 249, 0.95);
  color: #475569;
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.35);
  cursor: default;
}

.ql-schedule-chip.is-enabled {
  background: rgba(236, 253, 245, 0.95);
  color: #047857;
  box-shadow: inset 0 0 0 1px rgba(52, 211, 153, 0.35);
}

.ql-schedule-chip.is-disabled {
  background: rgba(254, 242, 242, 0.95);
  color: #b91c1c;
  box-shadow: inset 0 0 0 1px rgba(248, 113, 113, 0.35);
}

.ql-schedule-label {
  flex: 0 0 auto;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  opacity: 0.85;
}

.ql-schedule-code {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.2;
  background: transparent;
  color: inherit;
}

.showcase-card-dot {
  width: 10px;
  height: 10px;
  flex: 0 0 10px;
  border-radius: 999px;
  background: #cfd5dd;
  box-shadow: 0 0 0 2px rgba(207, 213, 221, 0.18);
}

.stock-dot.active {
  background: #22c55e;
  box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.16);
}

.showcase-card-note {
  margin: 12px 0 0;
  color: #6f5a44;
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  overflow: hidden;
  max-height: calc(1.8em * 6);
}

.masonry-note.empty {
  min-height: 56px;
  color: #a0896e;
}

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

.showcase-chip {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.showcase-chip.success {
  background: rgba(211, 239, 227, 0.92);
  color: #21684f;
}

.showcase-chip.warning {
  background: rgba(252, 237, 214, 0.92);
  color: #a16207;
}

.inline-tag-chip {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 2px 8px;
  font-size: 12px;
  line-height: 1.35;
  font-weight: 600;
}

.dropdown-danger-text {
  color: #c2410c;
  font-weight: 600;
}

@media (max-width: 768px) {
  .showcase-card {
    border-radius: 22px;
  }

  .showcase-card-top,
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
