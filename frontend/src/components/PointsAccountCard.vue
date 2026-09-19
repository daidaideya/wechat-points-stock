<template>
  <article class="points-account-card">
    <div class="points-account-head">
      <div class="points-account-title-wrap">
        <div class="points-account-title-row">
          <h3 class="points-account-title">{{ item.account.nickname || item.account.wechat_id }}</h3>
          <el-tag v-if="item.totalDiff > 0" type="success" effect="light">今日上涨</el-tag>
          <el-tag v-else-if="item.totalDiff < 0" type="danger" effect="light">今日下降</el-tag>
          <el-tag v-else type="info" effect="light">今日平稳</el-tag>
          <el-tag v-if="item.stale" type="warning" effect="light">未更新</el-tag>
        </div>
        <div class="points-account-subtitle">
          <span>{{ item.account.wechat_id }}</span>
          <span v-if="item.account.phone">手机号：{{ item.account.phone }}</span>
          <span v-if="item.account.device">设备：{{ item.account.device }}</span>
        </div>
      </div>
      <div class="points-account-actions">
        <el-tooltip content="查看未注册小程序" placement="top">
          <el-button
            class="points-icon-button"
            circle
            plain
            :disabled="!item.unregisteredProgramCount"
            @click="emit('open-unregistered', item)"
          >
            <el-icon><Warning /></el-icon>
          </el-button>
        </el-tooltip>
        <el-button type="primary" plain @click="emit('open-details', item)">
          查看明细
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
    </div>

    <div class="points-account-metrics">
      <div class="points-account-metric">
        <span class="points-account-metric-label">账号总积分</span>
        <strong>{{ format.formatNumber(item.totalPoints) }}</strong>
      </div>
      <div class="points-account-metric">
        <span class="points-account-metric-label">账号总现金</span>
        <strong>{{ format.formatCash(item.totalCash) }}</strong>
      </div>
      <div class="points-account-metric">
        <span class="points-account-metric-label">今日积分变化</span>
        <strong :class="format.diffClass(item.totalDiff)">{{ format.formatSigned(item.totalDiff) }}</strong>
      </div>
      <div class="points-account-metric">
        <span class="points-account-metric-label">今日现金变化</span>
        <strong :class="format.diffClass(item.totalCashDiff)">{{ format.formatSignedCash(item.totalCashDiff) }}</strong>
      </div>
      <div class="points-account-metric">
        <span class="points-account-metric-label">活跃小程序</span>
        <strong>{{ item.activeProgramCount }}</strong>
      </div>
      <div class="points-account-metric">
        <span class="points-account-metric-label">已登记项目</span>
        <strong>{{ item.registeredProgramCount }}</strong>
      </div>
    </div>

    <div class="points-account-meta">
      <span class="points-meta-chip">
        <el-icon><Clock /></el-icon>
        最近更新：{{ format.formatDate(item.latestReportTime) }}
      </span>
      <span class="points-meta-chip" :class="item.totalDiff >= 0 ? 'positive' : 'negative'">
        <el-icon><TrendCharts /></el-icon>
        波动：{{ item.totalDiff === 0 ? '平稳' : item.totalDiff > 0 ? '上涨中' : '回落中' }}
      </span>
    </div>

    <div class="points-top-programs">
      <div class="points-block-title">Top 小程序</div>
      <div v-if="item.topPrograms.length" class="points-program-list">
        <div
          v-for="program in item.topPrograms"
          :key="`${item.account.wechat_id}-${program.program_id}`"
          class="points-program-item"
        >
          <div class="points-program-main">
            <div class="points-program-name">{{ program.program_name }}</div>
            <div class="points-program-time">{{ format.formatDate(program.report_time) }}</div>
          </div>
          <div class="points-program-side">
            <div class="points-program-points">{{ format.formatPointsValue(program.points) }}</div>
            <div class="points-program-cash">{{ format.formatCash(program.cash) }}</div>
            <div class="points-program-diff" :class="format.diffClass(program.diff)">
              积分 {{ format.formatSigned(program.diff) }}
            </div>
            <div class="points-program-diff" :class="format.diffClass(program.cash_diff)">
              现金 {{ format.formatSignedCash(program.cash_diff) }}
            </div>
          </div>
        </div>
      </div>
      <el-empty v-else description="暂无积分明细" :image-size="88" />
    </div>
  </article>
</template>

<script setup>
import { toRef } from 'vue'
import { ArrowRight, Clock, TrendCharts, Warning } from '@element-plus/icons-vue'

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
  format: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['open-details', 'open-unregistered'])
const item = toRef(props, 'item')
const format = toRef(props, 'format')
</script>
