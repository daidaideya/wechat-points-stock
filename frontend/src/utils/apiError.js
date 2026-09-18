export function isRequestCanceled(error) {
  return error?.code === 'ERR_CANCELED' || error?.name === 'CanceledError'
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
  const data = error?.response?.data
  return readErrorText(data?.message) || readErrorText(data?.detail) || readErrorText(data) || fallback
}
