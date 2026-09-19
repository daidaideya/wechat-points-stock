<template>
  <el-card shadow="never" class="ql-card">
    <template #header>
      <div class="ql-card-header">
        <div>
          <div class="ql-card-title">当前时间线</div>
          <div class="ql-card-subtitle">
            按每日最早触发时间排序；标签表示与前一个任务的间隔，标黄小于 {{ intervalMinutes }} 分钟，标绿大于
            {{ intervalMinutes }} 分钟
          </div>
        </div>
        <div class="ql-card-header-actions">
          <el-switch v-model="showDisabledModel" active-text="显示已禁用" />
        </div>
      </div>
    </template>

    <el-skeleton v-if="loading" :rows="8" animated />
    <el-empty v-else-if="!filteredGroups.length" description="没有匹配的任务" />
    <template v-else>
      <div v-for="group in filteredGroups" :key="group.hour" class="ql-hour-group">
        <div class="ql-hour-label">{{ group.hour >= 0 ? String(group.hour).padStart(2, '0') + ':00' : '其他' }}</div>
        <div class="ql-hour-rows">
          <QinglongCronRow
            v-for="cron in group.crons"
            :key="cronKey(cron)"
            :cron="cron"
            :excluded="isExcluded(cron)"
            :crowded="isCrowded(cron)"
            :sparse="isSparse(cron)"
            :minute-gap="minuteGap(cron)"
            @edit="emit('edit', $event)"
            @toggle-exclude="emit('toggle-exclude', $event)"
          />
        </div>
      </div>
    </template>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import QinglongCronRow from './QinglongCronRow.vue'

const props = defineProps({
  loading: { type: Boolean, default: false },
  filteredGroups: { type: Array, default: () => [] },
  intervalMinutes: { type: Number, default: 2 },
  showDisabled: { type: Boolean, default: false },
  cronKey: { type: Function, required: true },
  isExcluded: { type: Function, required: true },
  isCrowded: { type: Function, required: true },
  isSparse: { type: Function, required: true },
  minuteGap: { type: Function, required: true },
})

const emit = defineEmits(['update:showDisabled', 'edit', 'toggle-exclude'])

const showDisabledModel = computed({
  get: () => props.showDisabled,
  set: (value) => emit('update:showDisabled', value),
})
</script>
