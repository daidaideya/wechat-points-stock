const EMPTY_NEXT_SLOT = {
  schedule: '',
  time: '',
  lastName: '',
  lastSchedule: '',
}

export const pad2 = (value) => String(value).padStart(2, '0')

export function cronKey(cron) {
  return `${cron?.id ?? 'noid'}-${cron?.name || ''}-${cron?.schedule || ''}`
}

// 判断是否为 code 版脚本：任务名以 code版_ 开头，或命令包含 code/、code_ 前缀。
export function isCodeCron(cron) {
  const name = (cron?.name || '').trim()
  if (name.startsWith('code版_')) return true
  const command = (cron?.command || '').toLowerCase()
  return /(^|[\s/\\])code[\\/]/.test(command) || /(^|[\s/\\])code_/.test(command)
}

// Expand cron fields such as "*/15", "1,5,10" and "9-11/2".
export function expandField(field, minimum, maximum) {
  const values = new Set()
  for (const chunk of String(field ?? '').split(',')) {
    const token = chunk.trim()
    if (!token) continue

    let step = 1
    let base = token
    if (token.includes('/')) {
      const parts = token.split('/')
      base = parts[0]
      step = Math.max(1, parseInt(parts[1], 10) || 1)
    }

    let start
    let end
    if (base === '*' || base === '') {
      start = minimum
      end = maximum
    } else if (base.includes('-')) {
      const parts = base.split('-')
      start = parseInt(parts[0], 10)
      end = parseInt(parts[1], 10)
    } else {
      start = parseInt(base, 10)
      end = start
    }

    if (Number.isNaN(start) || Number.isNaN(end)) continue
    start = Math.max(minimum, Math.min(maximum, start))
    end = Math.max(minimum, Math.min(maximum, end))
    if (end < start) continue
    for (let value = start; value <= end; value += step) {
      values.add(value)
    }
  }
  return [...values].sort((a, b) => a - b)
}

export function parseDailyMinutes(schedule) {
  const parts = String(schedule || '')
    .trim()
    .split(/\s+/)
  if (parts.length < 2) return []

  const minutes = expandField(parts[0], 0, 59)
  const hours = expandField(parts[1], 0, 23)
  const result = []
  for (const hour of hours) {
    for (const minute of minutes) {
      result.push(hour * 60 + minute)
    }
  }
  return result.sort((a, b) => a - b)
}

export function formatMinute(minuteOfDay) {
  return `${pad2(Math.floor(minuteOfDay / 60))}:${pad2(minuteOfDay % 60)}`
}

export function parseTimeToMinute(timeStr) {
  const match = /^(\d{2}):(\d{2})$/.exec(timeStr || '')
  if (!match) return null

  const hour = parseInt(match[1], 10)
  const minute = parseInt(match[2], 10)
  if (hour > 23 || minute > 59) return null
  return hour * 60 + minute
}

function emptyNextSlot(lastName = '', lastSchedule = '') {
  return { ...EMPTY_NEXT_SLOT, lastName, lastSchedule }
}

function bumpHourField(hourField) {
  const parts = String(hourField).split(',')
  const bumped = parts.map((part) => {
    const value = parseInt(part.trim(), 10)
    if (Number.isNaN(value)) return null
    return String((value + 1) % 24)
  })
  if (bumped.some((part) => part === null)) return null
  return bumped.join(',')
}

function firstNumericHour(hourField) {
  for (const part of String(hourField).split(',')) {
    const value = parseInt(part.trim(), 10)
    if (!Number.isNaN(value)) return value
  }
  return null
}

/**
 * Suggest the next cron slot from the newest task in the active command pool.
 * The helper is deliberately independent from Vue state so it can be tested
 * with fixtures and reused when the page is split into smaller components.
 */
export function getNextCronSlot(crons, { commandType = 'code', intervalMinutes = 2, isExcluded = () => false } = {}) {
  let pool = (Array.isArray(crons) ? crons : []).filter((cron) => {
    const earliestMinute = Number(cron?.earliest_minute)
    return cron?.is_disabled !== 1 && !isExcluded(cron) && Number.isFinite(earliestMinute) && earliestMinute < 24 * 60
  })

  if (commandType === 'code') {
    const filtered = pool.filter(isCodeCron)
    if (filtered.length) pool = filtered
  } else if (commandType === 'other') {
    const filtered = pool.filter((cron) => !isCodeCron(cron))
    if (filtered.length) pool = filtered
  }

  if (!pool.length) return { ...EMPTY_NEXT_SLOT }

  const numericId = (cron) => {
    const value = Number(cron?.id)
    return Number.isFinite(value) ? value : -1
  }
  const anyNumericId = pool.some((cron) => numericId(cron) >= 0)
  const base = pool.reduce((best, cron) => {
    if (anyNumericId) return numericId(cron) > numericId(best) ? cron : best
    return Number(cron.earliest_minute) > Number(best.earliest_minute) ? cron : best
  })

  const fields = String(base.schedule || '')
    .trim()
    .split(/\s+/)
  if (fields.length < 5) {
    return emptyNextSlot(base.name || '', base.schedule || '')
  }

  const rest = fields.slice(2).join(' ')
  const interval = Math.max(1, Number(intervalMinutes) || 2)
  const occupiedMinutesFor = (hourField) =>
    new Set(
      pool
        .filter((cron) => {
          const parts = String(cron.schedule || '')
            .trim()
            .split(/\s+/)
          return parts.length >= 5 && parts[1] === hourField
        })
        .map((cron) => parseInt(String(cron.schedule).trim().split(/\s+/)[0], 10))
        .filter((value) => Number.isFinite(value)),
    )

  let minute = parseInt(fields[0], 10)
  if (Number.isNaN(minute)) minute = Number(base.earliest_minute) % 60
  let hourField = fields[1]

  for (let attempts = 0; attempts < 200; attempts += 1) {
    const candidateTotalMinutes = minute + interval
    const hourSteps = Math.floor(candidateTotalMinutes / 60)
    minute = candidateTotalMinutes % 60

    let candidateHourField = hourField
    for (let step = 0; step < hourSteps; step += 1) {
      candidateHourField = bumpHourField(candidateHourField)
      if (candidateHourField === null) break
    }
    if (candidateHourField === null) {
      return emptyNextSlot(base.name || '', base.schedule || '')
    }
    hourField = candidateHourField

    if (!occupiedMinutesFor(hourField).has(minute)) {
      const hour = firstNumericHour(hourField)
      return {
        schedule: `${minute} ${hourField} ${rest}`,
        time: hour !== null ? `${pad2(hour)}:${pad2(minute)}` : '',
        lastName: base.name || '',
        lastSchedule: base.schedule || '',
      }
    }
  }

  return emptyNextSlot(base.name || '', base.schedule || '')
}
