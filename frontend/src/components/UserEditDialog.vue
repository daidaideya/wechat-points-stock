<template>
  <el-dialog
    v-model="dialogModel"
    :title="props.editing ? '编辑用户' : '新增用户'"
    width="520px"
    class="users-edit-dialog"
    @closed="emit('closed')"
  >
    <el-form label-width="90px" class="users-form">
      <el-form-item label="微信号">
        <el-input
          :model-value="props.form.wechat_id"
          :disabled="props.editing"
          @update:model-value="updateField('wechat_id', $event)"
        />
      </el-form-item>
      <el-form-item label="昵称">
        <el-input :model-value="props.form.nickname" @update:model-value="updateField('nickname', $event)" />
      </el-form-item>
      <el-form-item label="设备">
        <el-input :model-value="props.form.device" @update:model-value="updateField('device', $event)" />
      </el-form-item>
      <el-form-item label="手机号">
        <el-input :model-value="props.form.phone" @update:model-value="updateField('phone', $event)" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogModel = false">取消</el-button>
      <el-button type="primary" class="users-primary-button" :loading="props.saving" @click="emit('save')">
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  editing: {
    type: Boolean,
    default: false,
  },
  form: {
    type: Object,
    default: () => ({}),
  },
  saving: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'update-field', 'save', 'closed'])

const dialogModel = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

function updateField(field, value) {
  emit('update-field', field, value)
}
</script>

<style scoped>
.users-edit-dialog :deep(.el-dialog) {
  border-radius: 24px;
}

.users-form :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px rgba(232, 211, 183, 0.88) inset;
  background: #fffdf9;
}

.users-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #d89a3c inset;
}

.users-primary-button {
  border: none;
  background: linear-gradient(135deg, #e7b35a, #d89a3c);
  box-shadow: 0 10px 22px rgba(216, 154, 60, 0.18);
}
</style>
