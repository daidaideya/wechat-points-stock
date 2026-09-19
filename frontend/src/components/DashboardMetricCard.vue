<template>
  <el-card
    shadow="hover"
    class="dashboard-metric-card dashboard-interactive-card"
    :class="[props.card.tone, { clickable: props.card.clickable }]"
    @click="handleClick"
  >
    <div class="dashboard-metric-top">
      <div>
        <div class="dashboard-metric-label">{{ props.card.label }}</div>
        <div class="dashboard-metric-value">{{ props.card.value }}</div>
      </div>
      <div class="dashboard-metric-icon">
        <el-icon><component :is="props.card.icon" /></el-icon>
      </div>
    </div>
    <div class="dashboard-metric-footer">
      <span>{{ props.card.description }}</span>
      <span v-if="props.card.emphasis" class="dashboard-metric-emphasis">{{ props.card.emphasis }}</span>
    </div>
  </el-card>
</template>

<script setup>
const props = defineProps({
  card: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['activate'])

function handleClick() {
  if (props.card.clickable) emit('activate', props.card)
}
</script>
