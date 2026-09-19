const API_TIME_ZONE = 'Asia/Shanghai'
const LEGACY_NAIVE_DATETIME = /^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?$/

function normalizeApiDate(value) {
  if (!value) return null
  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value
  }

  let raw = String(value).trim()
  if (LEGACY_NAIVE_DATETIME.test(raw)) {
    // Historical database rows were written with datetime.utcnow() and have no offset.
    raw = `${raw.replace(' ', 'T')}Z`
  }

  const date = new Date(raw)
  return Number.isNaN(date.getTime()) ? null : date
}

export function parseApiDate(value) {
  return normalizeApiDate(value)
}

export function formatApiDate(value, fallback = '暂无') {
  if (!value) return fallback
  const date = normalizeApiDate(value)
  if (!date) return String(value)

  return date.toLocaleString('zh-CN', {
    hour12: false,
    timeZone: API_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export function getApiDateKey(value) {
  const date = normalizeApiDate(value)
  if (!date) return null

  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: API_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(date)
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]))
  return `${values.year}-${values.month}-${values.day}`
}
