import assert from 'node:assert/strict'
import test from 'node:test'
import { formatApiDate, getApiDateKey, parseApiDate } from './date.js'

test('parses legacy naive timestamps as UTC', () => {
  assert.equal(parseApiDate('2026-09-18 16:20:00').toISOString(), '2026-09-18T16:20:00.000Z')
  assert.equal(parseApiDate('2026-09-18T16:20:00Z').toISOString(), '2026-09-18T16:20:00.000Z')
})

test('formats API timestamps in Asia/Shanghai with fallbacks', () => {
  assert.equal(formatApiDate(null), '暂无')
  assert.equal(formatApiDate('', '暂无数据'), '暂无数据')
  assert.equal(formatApiDate('not-a-date'), 'not-a-date')
  assert.equal(formatApiDate('2026-09-18T16:20:00Z'), '2026/09/19 00:20:00')
})

test('builds a stable local-date key for today checks', () => {
  assert.equal(getApiDateKey('2026-09-18T16:20:00Z'), '2026-09-19')
  assert.equal(getApiDateKey('not-a-date'), null)
})
