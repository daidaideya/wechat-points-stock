<template>
  <div class="users-summary-grid">
    <div class="users-summary-card">
      <div class="users-summary-icon" aria-hidden="true">👥</div>
      <div class="users-summary-body">
        <span class="users-summary-label">用户数量</span>
        <strong class="users-summary-value">{{ props.userCount }}</strong>
      </div>
    </div>
    <div class="users-summary-card">
      <div class="users-summary-icon" aria-hidden="true">🎯</div>
      <div class="users-summary-body">
        <span class="users-summary-label">活跃小程序总计</span>
        <strong class="users-summary-value">{{ props.totalActivePrograms }}</strong>
      </div>
    </div>
    <div class="users-summary-card">
      <div class="users-summary-icon" aria-hidden="true">📦</div>
      <div class="users-summary-body">
        <span class="users-summary-label">活跃 APP 总计</span>
        <strong class="users-summary-value">{{ props.totalActiveApps }}</strong>
      </div>
    </div>
    <div class="users-summary-card">
      <div class="users-summary-icon" aria-hidden="true">📱</div>
      <div class="users-summary-body">
        <span class="users-summary-label">已留手机号</span>
        <strong class="users-summary-value">{{ props.usersWithPhone }}</strong>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  userCount: { type: Number, default: 0 },
  totalActivePrograms: { type: Number, default: 0 },
  totalActiveApps: { type: Number, default: 0 },
  usersWithPhone: { type: Number, default: 0 },
})
</script>

<style scoped>
.users-summary-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.users-summary-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 249, 240, 0.9);
  border: 1px solid rgba(232, 211, 183, 0.86);
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease;
}

.users-summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(145, 109, 61, 0.1);
}

.users-summary-icon {
  flex: 0 0 auto;
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(231, 179, 90, 0.22), rgba(216, 154, 60, 0.16));
  font-size: 22px;
  line-height: 1;
}

.users-summary-body {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.users-summary-label {
  display: block;
  color: #8a6c4c;
  font-size: 12px;
}

.users-summary-value {
  display: block;
  margin-top: 6px;
  color: #3a2b1a;
  font-size: 26px;
  line-height: 1.1;
}

@media (max-width: 900px) {
  .users-summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
