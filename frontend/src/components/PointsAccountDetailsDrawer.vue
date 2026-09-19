<template>
  <el-drawer v-model="detailVisible" class="points-detail-drawer" :size="drawerSize" :with-header="false">
    <template v-if="account">
      <div class="points-detail-stack">
        <section class="points-detail-hero">
          <div class="points-detail-hero-main">
            <div class="points-detail-title-row">
              <h2 class="points-detail-title">
                {{ account.account.nickname || account.account.wechat_id }}
              </h2>
              <el-tag v-if="account.stale" type="warning" effect="light">今日未更新</el-tag>
            </div>
            <div class="points-detail-subtitle">
              <span>{{ account.account.wechat_id }}</span>
              <span v-if="account.account.phone">手机号：{{ account.account.phone }}</span>
              <span v-if="account.account.device">设备：{{ account.account.device }}</span>
            </div>
          </div>
          <div class="points-detail-hero-actions">
            <el-button @click="closeDetails">关闭</el-button>
          </div>
        </section>

        <section class="points-detail-summary">
          <div class="points-detail-summary-item">
            <span>总积分</span>
            <strong>{{ formatters.formatNumber(account.totalPoints) }}</strong>
          </div>
          <div class="points-detail-summary-item">
            <span>总现金</span>
            <strong>{{ formatters.formatCash(account.totalCash) }}</strong>
          </div>
          <div class="points-detail-summary-item">
            <span>今日积分变化</span>
            <strong :class="formatters.diffClass(account.totalDiff)">
              {{ formatters.formatSigned(account.totalDiff) }}
            </strong>
          </div>
          <div class="points-detail-summary-item">
            <span>今日现金变化</span>
            <strong :class="formatters.diffClass(account.totalCashDiff)">
              {{ formatters.formatSignedCash(account.totalCashDiff) }}
            </strong>
          </div>
          <div class="points-detail-summary-item">
            <span>活跃项目</span>
            <strong>{{ account.activeProgramCount }}</strong>
          </div>
          <div class="points-detail-summary-item">
            <span>最近更新时间</span>
            <strong>{{ formatters.formatDate(account.latestReportTime) }}</strong>
          </div>
        </section>

        <section class="toolbar-card points-detail-toolbar-card">
          <div class="points-detail-toolbar">
            <el-input v-model="detailKeyword" clearable placeholder="搜索小程序名称 / program_id">
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>

            <el-select v-model="detailSortMode">
              <el-option label="按积分排序" value="points" />
              <el-option label="按今日变化排序" value="diff" />
              <el-option label="按更新时间排序" value="report_time" />
              <el-option label="按名称排序" value="name" />
            </el-select>

            <el-switch v-model="detailOnlyChanged" inline-prompt active-text="仅异常" inactive-text="全部" />
          </div>
        </section>

        <section class="points-detail-programs">
          <article
            v-for="program in detailPrograms"
            :key="`${account.account.wechat_id}-${program.program_id}`"
            class="points-detail-program-card"
          >
            <div class="points-detail-program-main">
              <div class="points-detail-program-name">{{ program.program_name }}</div>
              <div class="points-detail-program-id">{{ program.program_id }}</div>
            </div>
            <div class="points-detail-program-side">
              <div class="points-detail-program-points">积分 {{ formatters.formatPointsValue(program.points) }}</div>
              <div class="points-detail-program-points">现金 {{ formatters.formatCash(program.cash) }}</div>
              <div class="points-detail-program-diff" :class="formatters.diffClass(program.diff)">
                积分 {{ formatters.formatSigned(program.diff) }}
              </div>
              <div class="points-detail-program-diff" :class="formatters.diffClass(program.cash_diff)">
                现金 {{ formatters.formatSignedCash(program.cash_diff) }}
              </div>
            </div>
            <div class="points-detail-program-foot">
              <span>更新时间：{{ formatters.formatDate(program.report_time) }}</span>
              <el-tag v-if="program.points === '未注册' && program.cash === '未注册'" type="info" effect="light">
                未注册
              </el-tag>
              <el-tag v-else-if="(program.diff || 0) > 0 || (program.cash_diff || 0) > 0" type="success" effect="light">
                上涨
              </el-tag>
              <el-tag v-else-if="(program.diff || 0) < 0 || (program.cash_diff || 0) < 0" type="danger" effect="light">
                下降
              </el-tag>
              <el-tag v-else type="info" effect="light">平稳</el-tag>
            </div>
          </article>

          <el-empty v-if="!detailPrograms.length" description="没有符合条件的小程序数据" :image-size="88" />
        </section>
      </div>
    </template>
  </el-drawer>

  <el-drawer v-model="unregisteredVisible" class="points-unregistered-drawer" :size="drawerSize" :with-header="false">
    <template v-if="account">
      <div class="points-detail-stack">
        <section class="points-detail-hero points-unregistered-hero">
          <div class="points-detail-hero-main">
            <div class="points-detail-title-row">
              <h2 class="points-detail-title">未注册小程序</h2>
              <el-tag type="warning" effect="light">{{ account.unregisteredProgramCount }} 个待处理</el-tag>
            </div>
            <div class="points-detail-subtitle">
              <span>{{ account.account.nickname || account.account.wechat_id }}</span>
              <span>{{ account.account.wechat_id }}</span>
            </div>
          </div>
          <div class="points-detail-hero-actions">
            <el-button @click="closeUnregistered">关闭</el-button>
          </div>
        </section>

        <section class="toolbar-card points-unregistered-summary-card">
          <div class="points-unregistered-summary">
            <div class="points-unregistered-summary-item">
              <span>未注册数量</span>
              <strong>{{ account.unregisteredProgramCount }}</strong>
            </div>
            <div class="points-unregistered-summary-item">
              <span>账号设备</span>
              <strong>{{ account.account.device || '未填写' }}</strong>
            </div>
            <div class="points-unregistered-summary-item">
              <span>手机号</span>
              <strong>{{ account.account.phone || '未填写' }}</strong>
            </div>
          </div>
        </section>

        <section v-if="unregisteredPrograms.length" class="points-unregistered-list">
          <article
            v-for="program in unregisteredPrograms"
            :key="`${account.account.wechat_id}-unregistered-${program.program_id}`"
            class="points-unregistered-card"
          >
            <div class="points-unregistered-main">
              <div class="points-unregistered-name">{{ program.program_name || '未命名小程序' }}</div>
              <div class="points-unregistered-id">{{ program.program_id }}</div>
            </div>
            <div class="points-unregistered-side">
              <el-tag type="warning" effect="light">未注册</el-tag>
              <span class="points-unregistered-time">最近记录：{{ formatters.formatDate(program.report_time) }}</span>
            </div>
          </article>
        </section>

        <el-empty v-else description="当前账号没有未注册小程序" :image-size="88" />
      </div>
    </template>
  </el-drawer>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps({
  account: { type: Object, default: null },
  detailVisible: { type: Boolean, default: false },
  unregisteredVisible: { type: Boolean, default: false },
  drawerSize: { type: String, default: '720px' },
  formatters: { type: Object, required: true },
})

const emit = defineEmits(['update:detailVisible', 'update:unregisteredVisible'])

const detailKeyword = ref('')
const detailSortMode = ref('points')
const detailOnlyChanged = ref(false)

const detailVisible = computed({
  get: () => props.detailVisible,
  set: (value) => emit('update:detailVisible', value),
})

const unregisteredVisible = computed({
  get: () => props.unregisteredVisible,
  set: (value) => emit('update:unregisteredVisible', value),
})

const account = computed(() => props.account)

const detailPrograms = computed(() => {
  if (!account.value) return []

  const keyword = detailKeyword.value.trim().toLowerCase()
  const source = (Array.isArray(account.value.points) ? account.value.points : []).filter((program) => {
    const matchedKeyword = !keyword || `${program.program_name} ${program.program_id}`.toLowerCase().includes(keyword)
    if (!matchedKeyword) return false
    if (!detailOnlyChanged.value) return true
    return program.diff !== 0 || program.points === '未注册'
  })

  return [...source].sort((a, b) => {
    switch (detailSortMode.value) {
      case 'diff':
        return (b.diff || 0) - (a.diff || 0)
      case 'report_time': {
        const timeA = a.report_time ? new Date(a.report_time).getTime() : 0
        const timeB = b.report_time ? new Date(b.report_time).getTime() : 0
        return timeB - timeA
      }
      case 'name':
        return `${a.program_name}`.localeCompare(`${b.program_name}`, 'zh-CN')
      case 'points':
      default: {
        const pointsA = typeof a.points === 'number' ? a.points : -1
        const pointsB = typeof b.points === 'number' ? b.points : -1
        return pointsB - pointsA
      }
    }
  })
})

const unregisteredPrograms = computed(() => account.value?.unregisteredPrograms || [])

function resetDetailFilters() {
  detailKeyword.value = ''
  detailSortMode.value = 'points'
  detailOnlyChanged.value = false
}

function closeDetails() {
  detailVisible.value = false
}

function closeUnregistered() {
  unregisteredVisible.value = false
}

watch(
  () => props.detailVisible,
  (visible) => {
    if (visible) resetDetailFilters()
  },
)
</script>
