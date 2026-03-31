<template>
  <div class="access-gate-page">
    <div class="access-gate-shell">
      <div class="access-gate-card">
        <div class="access-gate-header">
          <div class="access-gate-brand-mark">
            <el-icon><Lock /></el-icon>
          </div>
          <div class="access-gate-header-text">
            <div class="access-gate-title">wechat points stock</div>
            <div class="access-gate-subtitle">访问控制验证</div>
          </div>
        </div>

        <div class="access-gate-description"></div>

        <el-form @submit.prevent>
          <el-form-item label="ACCESS KEY">
            <el-input
              v-model="accessKey"
              type="password"
              show-password
              placeholder="请输入访问密钥"
              @keyup.enter="submitAccess"
            />
          </el-form-item>

          <el-alert
            v-if="errorMessage"
            :title="errorMessage"
            type="error"
            :closable="false"
            show-icon
            class="access-gate-alert"
          />

          <el-button type="primary" class="access-gate-button" :loading="submitting" @click="submitAccess">
            进入系统
          </el-button>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Lock } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import api, { setAccessSession } from '../api'

const router = useRouter()
const accessKey = ref('')
const submitting = ref(false)
const errorMessage = ref('')

async function submitAccess() {
  if (!accessKey.value.trim()) {
    errorMessage.value = '请输入访问密钥'
    return
  }

  submitting.value = true
  errorMessage.value = ''

  try {
    await api.post('/access/verify', {
      access_key: accessKey.value,
    })

    setAccessSession(accessKey.value)
    router.replace('/dashboard')
  } catch (error) {
    console.error(error)
    errorMessage.value = error?.response?.data?.detail || '访问密钥错误'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.access-gate-page {
  min-height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background:
    linear-gradient(rgba(229, 209, 176, 0.18) 1px, transparent 1px),
    linear-gradient(90deg, rgba(229, 209, 176, 0.18) 1px, transparent 1px),
    linear-gradient(180deg, #fffaf2 0%, #fff7eb 48%, #f8ebd3 100%);
  background-size: 24px 24px, 24px 24px, 100% 100%;
}

.access-gate-shell {
  width: 100%;
  max-width: 560px;
}

.access-gate-card {
  width: 100%;
  padding: 34px 30px;
  border-radius: 28px;
  background: rgba(255, 253, 249, 0.96);
  border: 1px solid rgba(232, 211, 183, 0.92);
  box-shadow: 0 22px 60px rgba(145, 109, 61, 0.12);
}

.access-gate-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
}

.access-gate-brand-mark {
  width: 56px;
  height: 56px;
  border-radius: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(231, 179, 90, 0.34), rgba(216, 154, 60, 0.18));
  color: #9a631a;
  font-size: 24px;
  box-shadow: inset 0 0 0 1px rgba(214, 181, 132, 0.22);
  flex: 0 0 56px;
}

.access-gate-header-text {
  text-align: left;
}

.access-gate-title {
  font-size: 24px;
  font-weight: 800;
  color: #3a2b1a;
  text-transform: lowercase;
  line-height: 1.2;
}

.access-gate-subtitle {
  margin-top: 6px;
  font-size: 14px;
  color: #8a6c4c;
}

.access-gate-description {
  margin-top: 22px;
  margin-bottom: 28px;
  text-align: center;
  font-size: 14px;
  color: #8a6c4c;
}

.access-gate-alert {
  margin-bottom: 16px;
}

.access-gate-button {
  width: 100%;
  height: 44px;
  border: 0;
  background: linear-gradient(135deg, #e7b35a, #d89a3c);
  box-shadow: 0 10px 24px rgba(216, 154, 60, 0.18);
}

:deep(.el-form-item__label) {
  color: #8a6c4c;
  font-size: 12px;
  letter-spacing: 0.08em;
}

:deep(.el-input__wrapper) {
  background: #fffaf2;
  box-shadow: 0 0 0 1px rgba(225, 204, 176, 0.7) inset;
}

:deep(.el-input__inner) {
  color: #3a2b1a;
}

@media (max-width: 640px) {
  .access-gate-page {
    padding: 18px;
  }

  .access-gate-card {
    padding: 28px 20px;
    border-radius: 22px;
  }

  .access-gate-header {
    align-items: flex-start;
  }

  .access-gate-title {
    font-size: 20px;
  }
}
</style>
