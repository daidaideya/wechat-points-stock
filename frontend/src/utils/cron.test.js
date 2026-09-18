import assert from 'node:assert/strict'
import test from 'node:test'

import {
  expandField,
  formatMinute,
  getNextCronSlot,
  parseDailyMinutes,
  parseTimeToMinute,
} from './cron.js'

test('expands common cron field forms and sorts values', () => {
  assert.deepEqual(expandField('*/15,3-5', 0, 59), [0, 3, 4, 5, 15, 30, 45])
  assert.deepEqual(parseDailyMinutes('*/30 9-10 * * *'), [540, 570, 600, 630])
  assert.equal(formatMinute(9 * 60 + 5), '09:05')
})

test('parses valid time values and rejects invalid clock values', () => {
  assert.equal(parseTimeToMinute('07:05'), 425)
  assert.equal(parseTimeToMinute('24:00'), null)
  assert.equal(parseTimeToMinute('12:60'), null)
  assert.equal(parseTimeToMinute('7:05'), null)
})

test('uses the newest matching code task as the next-slot baseline', () => {
  const result = getNextCronSlot([
    {
      id: 10,
      name: '旧 code',
      command: '/scripts/code/old.py',
      schedule: '40 1,13 * * *',
      earliest_minute: 100,
    },
    {
      id: 20,
      name: '最新 code',
      command: '/scripts/code/new.py',
      schedule: '58 13,20 * * *',
      earliest_minute: 838,
    },
    {
      id: 30,
      name: '其他脚本',
      command: '/scripts/other.sh',
      schedule: '10 8 * * *',
      earliest_minute: 490,
    },
  ], { intervalMinutes: 2 })

  assert.deepEqual(result, {
    schedule: '0 14,21 * * *',
    time: '14:00',
    lastName: '最新 code',
    lastSchedule: '58 13,20 * * *',
  })
})

test('skips an occupied minute in the current hour group', () => {
  const result = getNextCronSlot([
    {
      id: 1,
      name: '占用',
      command: '/scripts/code/occupied.py',
      schedule: '52 10 * * *',
      earliest_minute: 652,
    },
    {
      id: 2,
      name: '最新',
      command: '/scripts/code/latest.py',
      schedule: '50 10 * * *',
      earliest_minute: 650,
    },
  ], { intervalMinutes: 2 })

  assert.equal(result.schedule, '54 10 * * *')
})

test('handles intervals larger than one hour without producing an invalid minute', () => {
  const result = getNextCronSlot([
    {
      id: 1,
      name: '最新',
      command: '/scripts/code/latest.py',
      schedule: '58 13,20 * * *',
      earliest_minute: 838,
    },
  ], { intervalMinutes: 120 })

  assert.equal(result.schedule, '58 15,22 * * *')
  assert.equal(result.time, '15:58')
})

test('honors disabled and excluded tasks without losing the type fallback', () => {
  const result = getNextCronSlot([
    {
      id: 99,
      name: '被排除 code',
      command: '/scripts/code/excluded.py',
      schedule: '10 9 * * *',
      earliest_minute: 550,
    },
    {
      id: 2,
      name: '其他脚本',
      command: '/scripts/other.sh',
      schedule: '20 9 * * *',
      earliest_minute: 560,
    },
    {
      id: 3,
      name: '禁用脚本',
      command: '/scripts/code/disabled.py',
      schedule: '30 9 * * *',
      earliest_minute: 570,
      is_disabled: 1,
    },
  ], {
    intervalMinutes: 2,
    isExcluded: (cron) => cron.name === '被排除 code',
  })

  assert.equal(result.lastName, '其他脚本')
  assert.equal(result.schedule, '22 9 * * *')
})
