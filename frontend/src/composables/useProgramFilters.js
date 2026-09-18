import { computed, ref, unref } from 'vue'

const STATUS_LABELS = {
  archived: '仅归档',
  all: '全部状态',
}

const FAVORITE_LABELS = {
  favorite: '仅收藏',
  unfavorite: '仅未收藏',
}

const QL_STATUS_LABELS = {
  enabled: '青龙启用',
  disabled: '青龙禁用',
  unknown: '青龙未关联',
}

export function useProgramFilters({ listKind = 'mini', pageSize = 20 } = {}) {
  const currentTag = ref('')
  const searchKeyword = ref('')
  const favoriteFilter = ref('all')
  const statusFilter = ref('active')
  const qlStatusFilter = ref('all')
  const sortFilter = ref('default')

  const hasActiveFilters = computed(() => {
    return Boolean(searchKeyword.value.trim())
      || favoriteFilter.value !== 'all'
      || Boolean(currentTag.value)
      || statusFilter.value !== 'active'
      || qlStatusFilter.value !== 'all'
      || sortFilter.value !== 'default'
  })

  const activeFilterChips = computed(() => {
    const chips = []
    if (searchKeyword.value.trim()) {
      chips.push({ key: 'search', label: `搜索：${searchKeyword.value.trim()}` })
    }
    if (statusFilter.value !== 'active') {
      chips.push({ key: 'status', label: STATUS_LABELS[statusFilter.value] || statusFilter.value })
    }
    if (favoriteFilter.value !== 'all') {
      chips.push({ key: 'favorite', label: FAVORITE_LABELS[favoriteFilter.value] || favoriteFilter.value })
    }
    if (qlStatusFilter.value !== 'all') {
      chips.push({ key: 'ql', label: QL_STATUS_LABELS[qlStatusFilter.value] || qlStatusFilter.value })
    }
    if (sortFilter.value !== 'default') {
      chips.push({ key: 'sort', label: '按定时排序' })
    }
    if (currentTag.value) {
      chips.push({ key: 'tag', label: `标签：${currentTag.value}` })
    }
    return chips
  })

  function buildProgramParams(page = 1) {
    const params = { page, size: pageSize, kind: unref(listKind) }
    const keyword = searchKeyword.value.trim()
    if (keyword) params.q = keyword
    if (favoriteFilter.value === 'favorite') params.is_favorite = true
    else if (favoriteFilter.value === 'unfavorite') params.is_favorite = false
    if (currentTag.value) params.tag = currentTag.value
    if (statusFilter.value && statusFilter.value !== 'active') params.status = statusFilter.value
    else params.status = 'active'
    if (qlStatusFilter.value && qlStatusFilter.value !== 'all') params.ql_status = qlStatusFilter.value
    if (sortFilter.value && sortFilter.value !== 'default') params.sort = sortFilter.value
    else params.sort = 'default'
    return params
  }

  function setStatusFilter(value) {
    statusFilter.value = value
  }

  function setFavoriteFilter(value) {
    favoriteFilter.value = value
  }

  function setQlStatusFilter(value) {
    qlStatusFilter.value = value
  }

  function setSortFilter(value) {
    sortFilter.value = value
  }

  function toggleTag(tag) {
    currentTag.value = currentTag.value === tag ? '' : tag
  }

  function clearFilterChip(key) {
    if (key === 'search') searchKeyword.value = ''
    if (key === 'status') statusFilter.value = 'active'
    if (key === 'favorite') favoriteFilter.value = 'all'
    if (key === 'ql') qlStatusFilter.value = 'all'
    if (key === 'sort') sortFilter.value = 'default'
    if (key === 'tag') currentTag.value = ''
  }

  function resetFilters() {
    searchKeyword.value = ''
    favoriteFilter.value = 'all'
    currentTag.value = ''
    statusFilter.value = 'active'
    qlStatusFilter.value = 'all'
    sortFilter.value = 'default'
  }

  return {
    currentTag,
    searchKeyword,
    favoriteFilter,
    statusFilter,
    qlStatusFilter,
    sortFilter,
    hasActiveFilters,
    activeFilterChips,
    buildProgramParams,
    setStatusFilter,
    setFavoriteFilter,
    setQlStatusFilter,
    setSortFilter,
    toggleTag,
    clearFilterChip,
    resetFilters,
  }
}
