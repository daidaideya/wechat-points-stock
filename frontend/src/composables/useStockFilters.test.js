import test from 'node:test'
import assert from 'node:assert/strict'

import {
  parseCashCapInput,
  useStockFilters,
} from './useStockFilters.js'

test('parses valid, blank, and invalid cash caps', () => {
  assert.equal(parseCashCapInput(''), null)
  assert.equal(parseCashCapInput(' 9.9 '), 9.9)
  assert.equal(parseCashCapInput('Infinity'), undefined)
  assert.equal(parseCashCapInput('-1'), undefined)
})

test('builds stock parameters from the active filter state', () => {
  const filters = useStockFilters({ pageSize: 50 })
  filters.keywordInput.value = '  coffee '
  filters.applySearchInput()
  filters.setStatusFilter('in_stock')
  filters.toggleTag('饮料')
  filters.setPriceMode('points_plus_cash')
  assert.equal(filters.applyCashCapInput('9.9'), true)

  assert.deepEqual(filters.buildStockParams(3), {
    page: 3,
    size: 50,
    q: 'coffee',
    status: 'in_stock',
    tag: '饮料',
    price_mode: 'points_plus_cash',
    cash_max: 9.9,
  })
  assert.equal(filters.priceModeLabel.value, '积分加钱购 · ≤ ¥9.9')
})

test('resets dependent cash filters when price mode changes', () => {
  const filters = useStockFilters()
  filters.setCashCapPreset(5)
  assert.deepEqual(filters.buildStockParams(), {
    page: 1,
    size: 20,
    price_mode: 'points_plus_cash',
    cash_max: 5,
  })

  filters.setPriceMode('points_only')
  assert.equal(filters.cashCapValue.value, null)
  assert.equal(filters.cashCapInput.value, '')
  assert.deepEqual(filters.buildStockParams(), {
    page: 1,
    size: 20,
    price_mode: 'points_only',
  })
})
