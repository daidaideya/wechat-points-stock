<template>
  <SettingsSectionCard title="数据库备份 / 恢复" description="导出备份，或从备份文件恢复当前 SQLite 数据库。">
    <el-form label-width="140px" class="settings-form" :disabled="props.disabled">
      <p class="settings-help-block">
        导出当前 SQLite 数据库作为备份；导入会完整替换现有数据。导入前请先导出一份备份。 导入成功后会在数据库旁保留
        <code>.pre_restore</code> 回滚副本。
      </p>
      <el-form-item label="备份导出">
        <el-button type="primary" plain :loading="props.exporting" @click="emit('export')"> 导出数据库 </el-button>
      </el-form-item>
      <el-form-item label="备份恢复">
        <div class="settings-inline-row">
          <input
            ref="fileInputRef"
            type="file"
            accept=".db,application/x-sqlite3,application/octet-stream"
            class="settings-file-input"
            :disabled="props.disabled"
            @change="handleFileChange"
          />
          <el-button type="danger" plain :loading="props.importing" :disabled="props.disabled" @click="triggerImport">
            选择文件并导入
          </el-button>
        </div>
      </el-form-item>
    </el-form>
  </SettingsSectionCard>
</template>

<script setup>
import { ref } from 'vue'
import SettingsSectionCard from './SettingsSectionCard.vue'

const props = defineProps({
  exporting: {
    type: Boolean,
    default: false,
  },
  importing: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['export', 'import-file'])
const fileInputRef = ref(null)

function triggerImport() {
  fileInputRef.value?.click()
}

function handleFileChange(event) {
  const file = event?.target?.files?.[0]
  // Reset immediately so canceling the confirmation still allows selecting the same file again.
  if (event?.target) event.target.value = ''
  if (file) emit('import-file', file)
}
</script>

<style scoped>
.settings-help-block {
  margin: 0 0 16px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.settings-inline-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.settings-file-input {
  display: none;
}
</style>
