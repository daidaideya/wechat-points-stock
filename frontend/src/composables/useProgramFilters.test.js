import test from 'node:test'
import assert from 'node:assert/strict'
import { ref } from 'vue'

import { useProgramFilters } from './useProgramFilters.js'

test('builds program parameters for the active list and filters', () => {
  const filters = useProgramFilters({ listKind: ref('app'), pageSize: 50 })
  filters.searchKeyword.value = '  coffee '
  filters.setStatusFilter('archived')
  filters.setFavoriteFilter('favorite')
  filters.setQlStatusFilter('enabled')
  filters.setSortFilter('cron')
  filters.toggleTag('饮料')

  assert.deepEqual(filters.buildProgramParams(3), {
    page: 3,
    size: 50,
    kind: 'app',
    q: 'coffee',
    is_favorite: true,
    tag: '饮料',
    status: 'archived',
    ql_status: 'enabled',
    sort: 'cron',
  })
})

test('builds active filter chips in the page display order', () => {
  const filters = useProgramFilters()
  filters.searchKeyword.value = 'coffee'
  filters.setStatusFilter('all')
  filters.setFavoriteFilter('unfavorite')
  filters.setQlStatusFilter('unknown')
  filters.setSortFilter('cron')
  filters.toggleTag('饮料')

  assert.equal(filters.hasActiveFilters.value, true)
  assert.deepEqual(filters.activeFilterChips.value, [
    { key: 'search', label: '搜索：coffee' },
    { key: 'status', label: '全部状态' },
    { key: 'favorite', label: '仅未收藏' },
    { key: 'ql', label: '青龙未关联' },
    { key: 'sort', label: '按定时排序' },
    { key: 'tag', label: '标签：饮料' },
  ])
})

test('clears individual chips and resets all program filters', () => {
  const filters = useProgramFilters()
  filters.searchKeyword.value = 'coffee'
  filters.setStatusFilter('archived')
  filters.setFavoriteFilter('favorite')
  filters.setQlStatusFilter('disabled')
  filters.setSortFilter('cron')
  filters.toggleTag('饮料')

  filters.clearFilterChip('search')
  filters.clearFilterChip('status')
  filters.clearFilterChip('favorite')
  filters.clearFilterChip('ql')
  filters.clearFilterChip('sort')
  filters.clearFilterChip('tag')

  assert.equal(filters.hasActiveFilters.value, false)
  filters.searchKeyword.value = 'again'
  filters.setStatusFilter('all')
  filters.resetFilters()
  assert.deepEqual(filters.buildProgramParams(), {
    page: 1,
    size: 20,
    kind: 'mini',
    status: 'active',
    sort: 'default',
  })
})
