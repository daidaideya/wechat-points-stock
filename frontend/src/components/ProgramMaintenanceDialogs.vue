<template>
  <el-dialog
    :model-value="noteVisible"
    title="编辑备注"
    :width="noteDialogWidth"
    class="showcase-dialog"
    @update:model-value="emit('update:note-visible', $event)"
  >
    <div class="showcase-dialog-body">
      <div class="showcase-dialog-intro">
        <div>
          <div class="showcase-dialog-title">维护小程序备注</div>
          <div class="showcase-dialog-subtitle">为当前小程序补充说明，便于后续识别、分类和管理。</div>
        </div>
        <div class="showcase-dialog-badge">
          {{ currentProgram?.program_name || currentProgram?.program_id || '当前小程序' }}
        </div>
      </div>

      <div class="dialog-panel">
        <div class="block-label">备注内容</div>
        <el-input
          v-model="editingNote"
          class="showcase-dialog-textarea"
          type="textarea"
          :rows="6"
          maxlength="200"
          show-word-limit
          placeholder="请输入备注"
        />
      </div>
    </div>

    <template #footer>
      <el-button @click="closeNoteDialog">取消</el-button>
      <el-button type="primary" :loading="savingNote" @click="emit('save-note', editingNote)">保存</el-button>
    </template>
  </el-dialog>

  <el-dialog
    :model-value="tagsVisible"
    title="编辑标签"
    :width="tagsDialogWidth"
    class="showcase-dialog showcase-tags-dialog"
    @update:model-value="emit('update:tags-visible', $event)"
  >
    <div class="tags-dialog-body">
      <div class="tags-dialog-intro">
        <div>
          <div class="tags-dialog-title">维护当前小程序标签</div>
          <div class="tags-dialog-subtitle">点击下方标签即可快速添加或移除，支持自定义标签。</div>
        </div>
        <div class="tags-dialog-counter">已选 {{ editingTags.length }} 个</div>
      </div>

      <div class="dialog-section dialog-panel">
        <div class="block-label">快捷标签</div>
        <div class="tag-list content tags-dialog-list">
          <button
            v-for="tag in quickTags"
            :key="tag"
            type="button"
            class="dialog-tag-chip"
            :class="{ active: editingTags.includes(tag) }"
            @click="toggleEditingTag(tag)"
          >
            {{ tag }}
          </button>
          <button type="button" class="dialog-tag-chip add-chip" @click="promptCustomTag">+ 自定义</button>
        </div>
      </div>

      <div class="dialog-section dialog-panel">
        <div class="block-label">已选标签</div>
        <div class="tag-list content tags-dialog-list selected-tags-list">
          <el-tag
            v-for="tag in editingTags"
            :key="tag"
            class="selected-dialog-tag"
            closable
            @close="removeEditingTag(tag)"
          >
            {{ tag }}
          </el-tag>
          <div v-if="!editingTags.length" class="tags-empty-state">暂无标签，可从上方快捷标签或自定义输入中添加</div>
        </div>
      </div>

      <div class="dialog-section dialog-panel compact-tip-panel">
        <div class="block-label">自定义标签</div>
        <el-input
          v-model="customTagInput"
          class="tags-custom-input"
          maxlength="20"
          placeholder="输入自定义标签后点击添加"
          @keyup.enter="addCustomTagFromInput"
        >
          <template #append>
            <el-button class="tags-add-button" @click="addCustomTagFromInput">添加</el-button>
          </template>
        </el-input>
        <div class="tags-dialog-tip">支持增删改：点击快捷标签切换，点击已选标签右侧关闭按钮删除。</div>
      </div>
    </div>

    <template #footer>
      <el-button @click="closeTagsDialog">取消</el-button>
      <el-button type="primary" :loading="savingTags" @click="emit('save-tags', [...editingTags])">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  noteVisible: { type: Boolean, default: false },
  tagsVisible: { type: Boolean, default: false },
  viewportWidth: { type: Number, default: 1200 },
  currentProgram: { type: Object, default: null },
  availableTags: { type: Array, default: () => [] },
  savingNote: { type: Boolean, default: false },
  savingTags: { type: Boolean, default: false },
  normalizeTags: { type: Function, required: true },
})

const emit = defineEmits(['update:note-visible', 'update:tags-visible', 'save-note', 'save-tags'])

const editingNote = ref('')
const editingTags = ref([])
const customTagInput = ref('')
const noteDialogWidth = computed(() => (props.viewportWidth <= 640 ? '94%' : '560px'))
const tagsDialogWidth = computed(() => (props.viewportWidth <= 640 ? '94%' : '620px'))
const quickTags = computed(() => {
  const knownSet = new Set(props.availableTags)
  return [...props.availableTags, ...editingTags.value.filter((tag) => !knownSet.has(tag))]
})

function syncNote() {
  editingNote.value = props.currentProgram?.note || ''
}

function syncTags() {
  editingTags.value = props.normalizeTags(props.currentProgram?.tags || [])
  customTagInput.value = ''
}

watch(
  () => props.noteVisible,
  (visible) => {
    if (visible) syncNote()
  },
  { immediate: true },
)

watch(
  () => props.tagsVisible,
  (visible) => {
    if (visible) syncTags()
  },
  { immediate: true },
)

watch(
  () => props.currentProgram,
  () => {
    if (props.noteVisible) syncNote()
    if (props.tagsVisible) syncTags()
  },
)

function closeNoteDialog() {
  emit('update:note-visible', false)
}

function closeTagsDialog() {
  emit('update:tags-visible', false)
}

function appendTag(tag) {
  editingTags.value = props.normalizeTags([...editingTags.value, tag])
}

function toggleEditingTag(tag) {
  if (editingTags.value.includes(tag)) {
    removeEditingTag(tag)
    return
  }
  appendTag(tag)
}

async function promptCustomTag() {
  try {
    const { value } = await ElMessageBox.prompt('请输入自定义标签', '新增标签', {
      confirmButtonText: '添加',
      cancelButtonText: '取消',
      inputPattern: /\S+/,
      inputErrorMessage: '标签不能为空',
    })
    const normalized = String(value || '')
      .trim()
      .slice(0, 20)
    if (normalized) appendTag(normalized)
  } catch {
    // ignore
  }
}

function addCustomTagFromInput() {
  const normalized = String(customTagInput.value || '')
    .trim()
    .slice(0, 20)
  if (!normalized) return
  appendTag(normalized)
  customTagInput.value = ''
}

function removeEditingTag(tag) {
  editingTags.value = editingTags.value.filter((item) => item !== tag)
}
</script>

<style scoped>
.showcase-dialog-body,
.tags-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.showcase-dialog-intro,
.tags-dialog-intro {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 2px 2px 6px;
}

.showcase-dialog-title,
.tags-dialog-title {
  color: #3a2a1d;
  font-size: 16px;
  font-weight: 700;
}

.showcase-dialog-subtitle,
.tags-dialog-subtitle {
  margin-top: 6px;
  color: #9b7e5c;
  font-size: 13px;
  line-height: 1.6;
}

.showcase-dialog-badge,
.tags-dialog-counter {
  flex: 0 0 auto;
  padding: 8px 14px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(255, 244, 221, 0.96), rgba(255, 237, 213, 0.9));
  color: #8b5e34;
  font-size: 12px;
  font-weight: 700;
  box-shadow: inset 0 0 0 1px rgba(231, 202, 163, 0.72);
}

.dialog-panel {
  padding: 16px 16px 14px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255, 251, 245, 0.96), rgba(255, 247, 235, 0.94));
  box-shadow: inset 0 0 0 1px rgba(235, 220, 194, 0.88);
}

.compact-tip-panel {
  padding-bottom: 16px;
}

.tags-dialog-list {
  gap: 10px;
}

.dialog-tag-chip {
  border: 0;
  padding: 9px 15px;
  border-radius: 999px;
  background: #fffaf3;
  color: #8a6c4c;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: inset 0 0 0 1px rgba(232, 210, 184, 0.82);
  transition: all 0.2s ease;
}

.dialog-tag-chip:hover {
  transform: translateY(-1px);
  background: #fff2df;
  color: #7a5530;
}

.dialog-tag-chip.active {
  background: linear-gradient(135deg, #d8f2e5, #c4ead6);
  color: #21684f;
  box-shadow: 0 10px 22px rgba(103, 170, 136, 0.16);
}

.dialog-tag-chip.add-chip {
  background: linear-gradient(135deg, rgba(243, 248, 255, 0.96), rgba(230, 241, 255, 0.94));
  color: #2563eb;
  box-shadow: inset 0 0 0 1px rgba(174, 205, 255, 0.86);
}

.dialog-tag-chip.add-chip:hover {
  background: linear-gradient(135deg, rgba(233, 243, 255, 0.98), rgba(219, 235, 255, 0.96));
  color: #1d4ed8;
}

.selected-tags-list {
  min-height: 44px;
}

.selected-dialog-tag {
  --el-tag-bg-color: rgba(214, 241, 230, 0.96);
  --el-tag-border-color: rgba(155, 209, 182, 0.88);
  --el-tag-hover-color: rgba(198, 233, 217, 1);
  --el-tag-text-color: #21684f;
  padding-inline: 10px;
  border-radius: 999px;
  font-weight: 600;
}

.tags-empty-state {
  width: 100%;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
  color: #9b7e5c;
  font-size: 13px;
  line-height: 1.6;
  box-shadow: inset 0 0 0 1px rgba(238, 225, 204, 0.92);
}

.showcase-dialog-textarea :deep(.el-textarea__inner),
.tags-custom-input :deep(.el-input__wrapper),
.tags-custom-input :deep(.el-input-group__append) {
  background: #fffaf3;
  box-shadow: 0 0 0 1px rgba(232, 210, 184, 0.78) inset;
}

.showcase-dialog-textarea :deep(.el-textarea__inner) {
  min-height: 148px;
  border-radius: 18px;
  color: #5f4932;
  line-height: 1.75;
}

.tags-custom-input :deep(.el-input__wrapper.is-focus),
.showcase-dialog-textarea :deep(.el-textarea__inner:focus) {
  box-shadow: 0 0 0 1px #d6a96b inset;
}

.tags-add-button {
  color: #8b5e34;
  font-weight: 700;
}

.tags-dialog-tip {
  margin-top: 10px;
  color: #a0815d;
  font-size: 12px;
  line-height: 1.7;
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
  .showcase-dialog-intro {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
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
}
</style>
