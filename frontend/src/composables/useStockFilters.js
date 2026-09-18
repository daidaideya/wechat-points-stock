import { computed, ref } from 'vue'
import { formatMoney } from '../utils/product.js'

export const CASH_CAP_PRESETS = [1, 5, 10, 20]

export function parseCashCapInput(raw) {
  const text = String(raw ?? '').trim()
  if (!text) return null
  const amount = Number(text)
  if (!Number.isFinite(amount) || amount < 0) return undefined
  return amount
}

export function useStockFilters({ pageSize = 20 } = {}) {
  const keywordInput = ref('')
  const searchKeyword = ref('')
  const activeStatus = ref('all')
  const currentTag = ref('')
  const priceMode = ref('all')
  const cashCapValue = ref(null)
  const cashCapInput = ref('')

  const priceModeLabel = computed(() => {
    if (priceMode.value === 'points_only') return '纯积分'
    if (priceMode.value === 'points_plus_cash') {
      if (cashCapValue.value == null) return '积分加钱购 · 不限金额'
      return `积分加钱购 · ≤ ¥${formatMoney(cashCapValue.value)}`
    }
    return '全部商品'
  })

  function buildStockParams(page = 1) {
    const params = { page, size: pageSize }
    if (searchKeyword.value) params.q = searchKeyword.value
    if (currentTag.value) params.tag = currentTag.value
    if (activeStatus.value !== 'all') params.status = activeStatus.value
    if (priceMode.value !== 'all') params.price_mode = priceMode.value
    if (priceMode.value === 'points_plus_cash' && cashCapValue.value != null) {
      params.cash_max = cashCapValue.value
    }
    return params
  }

  function applySearchInput() {
    searchKeyword.value = keywordInput.value.trim()
  }

  function setStatusFilter(status) {
    activeStatus.value = status
  }

  function toggleTag(tag) {
    currentTag.value = currentTag.value === tag ? '' : tag
  }

  function setPriceMode(mode) {
    priceMode.value = priceMode.value === mode && mode !== 'all' ? 'all' : mode
    if (priceMode.value !== 'points_plus_cash') {
      cashCapValue.value = null
      cashCapInput.value = ''
    }
  }

  function applyCashCapInput(raw = cashCapInput.value) {
    const parsed = parseCashCapInput(raw)
    if (parsed === undefined) return false
    cashCapValue.value = parsed
    cashCapInput.value = parsed == null ? '' : formatMoney(parsed)
    return true
  }

  function setCashCapPreset(amount) {
    cashCapValue.value = amount
    cashCapInput.value = formatMoney(amount)
    priceMode.value = 'points_plus_cash'
  }

  function clearCashCap() {
    cashCapValue.value = null
    cashCapInput.value = ''
  }

  function isCashCapPresetActive(amount) {
    return cashCapValue.value != null && Number(cashCapValue.value) === Number(amount)
  }

  function resetFilters() {
    keywordInput.value = ''
    searchKeyword.value = ''
    activeStatus.value = 'all'
    currentTag.value = ''
    priceMode.value = 'all'
    cashCapValue.value = null
    cashCapInput.value = ''
  }

  return {
    keywordInput,
    searchKeyword,
    activeStatus,
    currentTag,
    priceMode,
    cashCapValue,
    cashCapInput,
    priceModeLabel,
    buildStockParams,
    applySearchInput,
    setStatusFilter,
    toggleTag,
    setPriceMode,
    applyCashCapInput,
    setCashCapPreset,
    clearCashCap,
    isCashCapPresetActive,
    resetFilters,
  }
}
