<template>
  <div class="users-list-section">
    <div class="users-list-head">
      <div>
        <h3 class="section-title compact">用户列表</h3>
        <p class="section-description compact">按住左侧 <strong>⋮⋮</strong> 拖拽即可调整顺序，松手后自动保存。</p>
      </div>
      <div v-if="props.sorting" class="users-sort-saving">正在保存顺序…</div>
    </div>

    <el-skeleton v-if="props.loading" :rows="8" animated />

    <template v-else>
      <el-empty v-if="!props.items.length" description="暂无用户数据" />

      <div v-else ref="mobileListRef" class="users-mobile-list">
        <UserMobileCard
          v-for="(item, index) in props.items"
          :key="item.wechat_id"
          :item="item"
          :index="index"
          :deleting-wechat-id="props.deletingWechatId"
          @edit="emit('edit', $event)"
          @view-points="emit('view-points', $event)"
          @remove="emit('remove', $event)"
        />
      </div>

      <div v-if="props.items.length" class="users-desktop-table-wrap">
        <UserDesktopTable
          ref="desktopTableRef"
          :items="props.items"
          :deleting-wechat-id="props.deletingWechatId"
          @edit="emit('edit', $event)"
          @view-points="emit('view-points', $event)"
          @remove="emit('remove', $event)"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import UserDesktopTable from './UserDesktopTable.vue'
import UserMobileCard from './UserMobileCard.vue'

const props = defineProps({
  loading: { type: Boolean, default: false },
  sorting: { type: Boolean, default: false },
  items: { type: Array, default: () => [] },
  deletingWechatId: { type: String, default: '' },
})

const emit = defineEmits(['edit', 'view-points', 'remove'])
const mobileListRef = ref(null)
const desktopTableRef = ref(null)

function getMobileListElement() {
  return mobileListRef.value
}

function getDesktopTableInstance() {
  return desktopTableRef.value
}

defineExpose({ getMobileListElement, getDesktopTableInstance })
</script>

<style scoped>
.users-list-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.users-sort-saving {
  flex: 0 0 auto;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(96, 165, 250, 0.14);
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.users-desktop-table-wrap {
  display: block;
}

.users-mobile-list {
  display: none;
}

@container (max-width: 1200px) {
  .users-list-head {
    flex-direction: column;
    align-items: stretch;
  }

  .users-desktop-table-wrap {
    display: none;
  }

  .users-mobile-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
}

@media (max-width: 900px) {
  .users-list-head {
    flex-direction: column;
    align-items: stretch;
  }

  .users-desktop-table-wrap {
    display: none;
  }

  .users-mobile-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
}
</style>
