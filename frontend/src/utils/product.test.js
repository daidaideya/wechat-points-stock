import test from 'node:test'
import assert from 'node:assert/strict'

import {
  formatCashAmount,
  formatMoney,
  formatProductPrice,
  getRedeemBlockedLabel,
  isRedeemable,
} from './product.js'

test('formats money and product prices consistently', () => {
  assert.equal(formatMoney(12.5), '12.5')
  assert.equal(formatMoney(Number.POSITIVE_INFINITY), '0')
  assert.equal(formatCashAmount(null), '—')
  assert.equal(formatCashAmount(9.9), '¥9.9')
  assert.equal(formatProductPrice({ points: 300 }), '300 积分')
  assert.equal(formatProductPrice({ points: 300, cash: 9.9 }), '300 积分 + ¥9.9')
  assert.equal(formatProductPrice({ cash: 9.9 }), '¥9.9')
})

test('requires stock, points, and cash balances for redeemability', () => {
  const product = { stock: 2, points: 300, cash: 9.9 }
  assert.equal(isRedeemable(product, 300, 10), true)
  assert.equal(isRedeemable(product, 300, 9), false)
  assert.equal(isRedeemable(product, 299, 10), false)
  assert.equal(isRedeemable({ ...product, stock: 0 }, 300, 10), false)
  assert.equal(isRedeemable({ stock: 1, points: 300, cash: 0 }, 300, null), true)
})

test('explains the first blocking redeemability condition', () => {
  assert.equal(getRedeemBlockedLabel({ stock: 0 }, 0, null), '无货')
  assert.equal(getRedeemBlockedLabel({ stock: 1, points: 300, cash: 9.9 }, 200, 5), '积分/现金不足')
  assert.equal(getRedeemBlockedLabel({ stock: 1, points: 300, cash: 9.9 }, 300, 5), '现金不足')
  assert.equal(getRedeemBlockedLabel({ stock: 1, points: 300, cash: 0 }, 200, null), '积分不足')
  assert.equal(getRedeemBlockedLabel({ stock: 1, points: 300, cash: 0 }, 300, null), '不可兑换')
})
