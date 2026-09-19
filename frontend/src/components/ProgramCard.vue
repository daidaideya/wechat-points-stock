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

    <ProgramCardActions
      :program="props.program"
      :is-touch-layout="props.isTouchLayout"
      :updating-program-id="props.updatingProgramId"
      :archiving-program-id="props.archivingProgramId"
      :deleting-program-id="props.deletingProgramId"
      :format-date="props.formatDate"
      @open-tags="emitOpenTags"
      @open-stock="emitOpenStock"
      @open-detail="emitOpenDetail"
      @open-note="emitOpenNote"
      @toggle-favorite="emitToggleFavorite"
      @command="emitCommand"
    />
  </article>
</template>

<script setup>
import { CircleCheck, CircleClose } from '@element-plus/icons-vue'
import ProgramCardActions from './ProgramCardActions.vue'
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
  container-type: inline-size;
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
  align-items: flex-start;
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
  white-space: normal;
  overflow: visible;
  overflow-wrap: anywhere;
  word-break: break-word;
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
  overflow: visible;
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
  line-height: 1.4;
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
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
  padding: 2px 8px;
  font-size: 12px;
  line-height: 1.35;
  font-weight: 600;
}

@container (max-width: 220px) {
  .showcase-card-title-line {
    position: relative;
    display: block;
    padding-top: 30px;
  }

  .showcase-card-index {
    position: absolute;
    top: 0;
    left: 0;
    margin-top: 0;
  }

  .showcase-card-title {
    width: 100%;
  }

  .ql-status-badge {
    position: absolute;
    top: 0;
    right: 0;
  }
}

@media (max-width: 768px) {
  .showcase-card {
    border-radius: 22px;
  }

  .showcase-card-top {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
