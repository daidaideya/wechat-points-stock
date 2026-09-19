<template>
  <section class="settings-section-card">
    <div class="settings-section-header">
      <div>
        <h3 class="settings-section-title">{{ title }}</h3>
        <p class="settings-section-desc">{{ description }}</p>
      </div>
    </div>

    <slot />
  </section>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    required: true,
  },
})
</script>

<style scoped>
.settings-section-card {
  padding: 18px 18px 8px;
  border-radius: 18px;
  background: rgba(255, 253, 249, 0.96);
  border: 1px solid rgba(236, 220, 196, 0.95);
  box-shadow: 0 8px 18px rgba(126, 98, 63, 0.05);
}

.settings-section-header {
  margin-bottom: 8px;
}

.settings-section-title {
  margin: 0;
  color: #2f2418;
  font-size: 18px;
  font-weight: 700;
}

.settings-section-desc {
  margin: 6px 0 0;
  color: #8a6c4c;
  font-size: 13px;
  line-height: 1.5;
}
</style>
