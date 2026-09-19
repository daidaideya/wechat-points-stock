<template>
  <aside class="settings-nav-panel">
    <nav aria-label="设置导航">
      <div class="settings-nav-title">设置导航</div>
      <button
        v-for="item in items"
        :key="item.key"
        type="button"
        class="settings-nav-item"
        :class="{ active: modelValue === item.key }"
        :aria-current="modelValue === item.key ? 'page' : undefined"
        :disabled="disabled"
        @click="selectSection(item.key)"
      >
        <span class="settings-nav-icon" aria-hidden="true">{{ item.icon }}</span>
        <span class="settings-nav-copy">
          <strong>{{ item.label }}</strong>
          <small>{{ item.desc }}</small>
        </span>
      </button>
    </nav>
  </aside>
</template>

<script setup>
defineProps({
  items: { type: Array, required: true },
  modelValue: { type: String, required: true },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

function selectSection(key) {
  emit('update:modelValue', key)
}
</script>

<style scoped>
.settings-nav-panel {
  padding: 14px;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255, 250, 242, 0.98), rgba(255, 246, 234, 0.92));
  border: 1px solid rgba(232, 210, 184, 0.9);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.settings-nav-panel > nav {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.settings-nav-title {
  margin-bottom: 4px;
  padding: 0 6px;
  color: #8b5e34;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.settings-nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px;
  border: 0;
  border-radius: 14px;
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition:
    background 0.18s ease,
    box-shadow 0.18s ease,
    transform 0.18s ease;
}

.settings-nav-item:hover {
  background: rgba(255, 255, 255, 0.72);
}

.settings-nav-item.active {
  background: #fff;
  box-shadow: 0 10px 20px rgba(180, 132, 72, 0.12);
  transform: translateY(-1px);
}

.settings-nav-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  background: rgba(255, 244, 221, 0.95);
  flex: 0 0 auto;
}

.settings-nav-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.settings-nav-copy strong {
  color: #3f2a18;
  font-size: 14px;
  font-weight: 700;
}

.settings-nav-copy small {
  color: #9b7e5c;
  font-size: 12px;
  line-height: 1.35;
}

@media (max-width: 960px) {
  .settings-nav-panel > nav {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }

  .settings-nav-title {
    grid-column: 1 / -1;
  }

  .settings-nav-item {
    flex-direction: column;
    align-items: flex-start;
    min-height: 88px;
  }
}

@media (max-width: 640px) {
  .settings-nav-panel > nav {
    grid-template-columns: 1fr;
  }

  .settings-nav-item {
    flex-direction: row;
    min-height: auto;
  }
}
</style>
