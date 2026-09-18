export function isRequestCanceled(error) {
  return error?.code === 'ERR_CANCELED' || error?.name === 'CanceledError' || error?.name === 'AbortError'
}

export function getApiErrorKind(error) {
  if (isRequestCanceled(error)) return 'canceled'
  if (error?.code === 'ECONNABORTED' || error?.code === 'ETIMEDOUT') return 'timeout'
  if (error?.code === 'ERR_NETWORK' || (!error?.response && error?.message === 'Network Error')) {
    return 'network'
  }
  if (error?.response) return 'http'
  return 'unknown'
}

function readResponseHeader(error, name) {
  const headers = error?.response?.headers
  if (!headers) return ''
  if (typeof headers.get === 'function') return String(headers.get(name) || '').trim()
  return String(headers[name] || headers[name.toLowerCase()] || '').trim()
}

function readRequestId(error) {
  return String(error?.response?.data?.request_id || readResponseHeader(error, 'X-Request-ID') || '').trim()
}

function readErrorText(value) {
  if (typeof value === 'string') return value.trim()
  if (Array.isArray(value)) {
    return value
      .map((item) => readErrorText(item?.msg || item?.message || item))
      .filter(Boolean)
      .join('；')
  }
  if (value && typeof value === 'object') {
    return readErrorText(value.message || value.msg || value.detail)
  }
  return ''
}

export function getApiErrorMessage(error, fallback = '请求失败') {
  if (isRequestCanceled(error)) return ''
  const kind = getApiErrorKind(error)
  const data = error?.response?.data
  const detail = readErrorText(data?.message) || readErrorText(data?.detail) || readErrorText(data)
  const message =
    detail ||
    (kind === 'timeout' ? `${fallback}（请求超时）` : kind === 'network' ? `${fallback}（网络不可用）` : fallback)
  const requestId = readRequestId(error)
  return requestId ? `${message}（请求 ID: ${requestId}）` : message
}
