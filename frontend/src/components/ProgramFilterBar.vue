<template>
  <section class="toolbar-card programs-toolbar-card showcase-toolbar-card">
    <div class="filter-shell">
      <div class="filter-search-row">
        <el-input
          :model-value="props.searchKeyword"
          clearable
          size="large"
          class="showcase-search-input filter-search-input"
          placeholder="搜索名称 / program_id / 拼音"
          @update:model-value="onSearchKeywordUpdate"
          @keyup.enter="onSearch"
          @clear="onSearch"
        >
          <template #prefix>
            <el-icon class="filter-search-icon"><Search /></el-icon>
          </template>
          <template #append>
            <el-button class="filter-search-btn" @click="onSearch">搜索</el-button>
          </template>
        </el-input>

        <div class="filter-search-side">
          <div class="toolbar-status-chip compact warm-chip filter-count-chip">
            <span class="toolbar-status-value">{{ props.loadedCount }}</span>
            <span class="toolbar-status-label">已加载</span>
          </div>
          <el-button
            class="showcase-reset-button filter-reset-btn"
            plain
            :disabled="!props.hasActiveFilters"
            @click="onReset"
          >
            重置
          </el-button>
        </div>
      </div>

      <div class="filter-control-row">
        <div class="filter-group">
          <span class="filter-group-label">状态</span>
          <div class="segmented-group">
            <button type="button" class="segmented-item" :class="{ active: props.statusFilter === 'active' }" @click="onStatus('active')">活跃</button>
            <button type="button" class="segmented-item" :class="{ active: props.statusFilter === 'archived' }" @click="onStatus('archived')">归档</button>
            <button type="button" class="segmented-item" :class="{ active: props.statusFilter === 'all' }" @click="onStatus('all')">全部</button>
          </div>
        </div>

        <div class="filter-group">
          <span class="filter-group-label">收藏</span>
          <div class="segmented-group">
            <button type="button" class="segmented-item" :class="{ active: props.favoriteFilter === 'all' }" @click="onFavorite('all')">全部</button>
            <button type="button" class="segmented-item" :class="{ active: props.favoriteFilter === 'favorite' }" @click="onFavorite('favorite')">收藏</button>
            <button type="button" class="segmented-item" :class="{ active: props.favoriteFilter === 'unfavorite' }" @click="onFavorite('unfavorite')">未藏</button>
          </div>
        </div>

        <div class="filter-group">
          <span class="filter-group-label">青龙</span>
          <div class="segmented-group">
            <button type="button" class="segmented-item" :class="{ active: props.qlStatusFilter === 'all' }" @click="onQlStatus('all')">全部</button>
            <button type="button" class="segmented-item" :class="{ active: props.qlStatusFilter === 'enabled' }" @click="onQlStatus('enabled')">启用</button>
            <button type="button" class="segmented-item" :class="{ active: props.qlStatusFilter === 'disabled' }" @click="onQlStatus('disabled')">禁用</button>
            <button type="button" class="segmented-item" :class="{ active: props.qlStatusFilter === 'unknown' }" @click="onQlStatus('unknown')">未关联</button>
          </div>
        </div>

        <div class="filter-group">
          <span class="filter-group-label">排序</span>
          <div class="segmented-group">
            <button type="button" class="segmented-item" :class="{ active: props.sortFilter === 'default' }" @click="onSort('default')">默认</button>
            <button type="button" class="segmented-item" :class="{ active: props.sortFilter === 'cron' }" @click="onSort('cron')">定时</button>
          </div>
        </div>
      </div>

      <div class="filter-tags-panel">
        <div class="filter-tags-header">
          <span class="filter-group-label">标签</span>
          <span class="filter-tags-current">{{ props.currentTag || '全部标签' }}</span>
          <span v-if="props.availableTags.length" class="filter-tags-count">{{ props.availableTags.length }}</span>
        </div>

        <div class="tag-list content filter-tag-list showcase compact">
          <button
            type="button"
            class="filter-chip"
            :class="{ active: props.currentTag === '' }"
            @click="onTag('')"
          >
            全部
          </button>
          <button
            v-for="tag in props.availableTags"
            :key="tag"
            type="button"
            class="filter-chip"
            :class="{ active: props.currentTag === tag }"
            @click="onTag(tag)"
          >
            {{ tag }}
          </button>
          <span v-if="!props.availableTags.length" class="empty-text">暂无可筛选标签</span>
        </div>
      </div>

      <div v-if="props.activeFilterChips.length" class="active-filter-bar">
        <span class="active-filter-label">当前筛选</span>
        <div class="active-filter-list">
          <button
            v-for="chip in props.activeFilterChips"
            :key="chip.key"
            type="button"
            class="active-filter-chip"
            @click="onClearChip(chip.key)"
          >
            {{ chip.label }}
            <span class="active-filter-close">×</span>
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { Search } from '@element-plus/icons-vue'

const props = defineProps({
  searchKeyword: { type: String, default: '' },
  statusFilter: { type: String, default: 'active' },
  favoriteFilter: { type: String, default: 'all' },
  qlStatusFilter: { type: String, default: 'all' },
  sortFilter: { type: String, default: 'default' },
  currentTag: { type: String, default: '' },
  availableTags: { type: Array, default: () => [] },
  activeFilterChips: { type: Array, default: () => [] },
  hasActiveFilters: { type: Boolean, default: false },
  loadedCount: { type: Number, default: 0 },
})

const emit = defineEmits([
  'update:searchKeyword',
  'search',
  'reset',
  'status',
  'favorite',
  'ql-status',
  'sort',
  'tag',
  'clear-chip',
])

function onSearchKeywordUpdate(value) {
  emit('update:searchKeyword', value)
}

function onSearch() {
  emit('search')
}

function onReset() {
  emit('reset')
}

function onStatus(value) {
  emit('status', value)
}

function onFavorite(value) {
  emit('favorite', value)
}

function onQlStatus(value) {
  emit('ql-status', value)
}

function onSort(value) {
  emit('sort', value)
}

function onTag(value) {
  emit('tag', value)
}

function onClearChip(value) {
  emit('clear-chip', value)
}
</script>

<style scoped>
.showcase-toolbar-card {
  border-radius: 26px;
  border: 1px solid rgba(235, 220, 194, 0.88);
  background: rgba(255, 252, 247, 0.9);
  box-shadow: 0 10px 24px rgba(126, 98, 63, 0.04);
  backdrop-filter: blur(2px);
  padding: 16px 18px;
}

.filter-shell {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.filter-search-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
}

.filter-search-side {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 0 0 auto;
}

.warm-chip {
  background: linear-gradient(135deg, rgba(255, 244, 221, 0.96), rgba(255, 237, 213, 0.9));
  color: #8b5e34;
}

.filter-count-chip {
  min-width: 78px;
  justify-content: center;
}

.showcase-search-input :deep(.el-input__wrapper),
.showcase-search-input :deep(.el-input-group__append) {
  background: #fffaf3;
  box-shadow: 0 0 0 1px rgba(232, 210, 184, 0.78) inset;
}

.showcase-search-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #d6a96b inset;
}

.filter-search-icon {
  color: #b08958;
}

.filter-search-btn {
  color: #8b5e34 !important;
  font-weight: 700;
}

.showcase-reset-button,
.filter-reset-btn {
  flex: 0 0 auto;
  min-width: 72px;
  height: 40px;
  padding: 0 14px;
  border-color: rgba(219, 183, 141, 0.74);
  color: #8b5e34;
  background: #fff9f2;
  font-size: 13px;
}

.filter-control-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 16px;
  align-items: center;
}

.filter-group {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.filter-group-label {
  flex: 0 0 auto;
  color: #9b7e5c;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.segmented-group {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  border-radius: 999px;
  background: rgba(255, 248, 236, 0.95);
  box-shadow: inset 0 0 0 1px rgba(231, 208, 176, 0.82);
}

.segmented-item {
  border: 0;
  background: transparent;
  color: #8a6c4c;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  padding: 8px 12px;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.16s ease;
  white-space: nowrap;
}

.segmented-item:hover {
  background: rgba(255, 255, 255, 0.72);
}

.segmented-item.active {
  background: linear-gradient(135deg, #f5d8a8, #efc381);
  color: #5b3b14;
  box-shadow: 0 8px 16px rgba(225, 172, 88, 0.18);
}

.filter-tags-panel {
  border-radius: 16px;
  background: rgba(255, 250, 242, 0.8);
  box-shadow: inset 0 0 0 1px rgba(232, 210, 184, 0.72);
  padding: 10px 12px 12px;
}

.filter-tags-header {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  margin-bottom: 10px;
}

.filter-tags-current {
  color: #6f5a44;
  font-size: 13px;
  font-weight: 700;
}

.filter-tags-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(245, 216, 168, 0.7);
  color: #8b5e34;
  font-size: 11px;
  font-weight: 700;
}

.filter-tag-list.showcase {
  gap: 8px;
  margin-top: 0;
  padding-top: 0;
  border-top: 0;
}

.filter-chip {
  border: 0;
  padding: 8px 12px;
  border-radius: 999px;
  background: #fff8ef;
  color: #8a6c4c;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: inset 0 0 0 1px rgba(231, 208, 176, 0.86);
  transition: all 0.2s ease;
}

.filter-chip:hover {
  transform: translateY(-1px);
  background: #fff3de;
}

.filter-chip.active {
  background: linear-gradient(135deg, #f5d8a8, #efc381);
  color: #5b3b14;
  box-shadow: 0 10px 18px rgba(225, 172, 88, 0.18);
}

.active-filter-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 10px;
}

.active-filter-label {
  color: #9b7e5c;
  font-size: 12px;
  font-weight: 700;
}

.active-filter-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.active-filter-chip {
  border: 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 244, 221, 0.95);
  color: #8b5e34;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.active-filter-close {
  font-size: 14px;
  line-height: 1;
  opacity: 0.75;
}

@media (max-width: 960px) {
  .filter-search-row {
    grid-template-columns: 1fr;
  }

  .filter-search-side {
    justify-content: space-between;
  }

  .filter-control-row {
    gap: 10px;
  }
}

@media (max-width: 768px) {
  .showcase-toolbar-card {
    border-radius: 22px;
  }

  .filter-group {
    width: 100%;
    justify-content: space-between;
  }

  .segmented-group {
    flex: 1 1 auto;
    justify-content: space-between;
  }
}
</style>
