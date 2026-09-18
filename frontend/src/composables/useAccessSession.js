const ACCESS_SESSION_KEY = 'site_access_key'

function resolveStorage(storage) {
  if (storage) return storage
  try {
    return typeof localStorage !== 'undefined' ? localStorage : null
  } catch {
    return null
  }
}

export function useAccessSession(storage) {
  const sessionStorage = resolveStorage(storage)

  function getAccessSession() {
    return sessionStorage?.getItem(ACCESS_SESSION_KEY) || ''
  }

  function clearAccessSession() {
    sessionStorage?.removeItem(ACCESS_SESSION_KEY)
  }

  return {
    getAccessSession,
    clearAccessSession,
  }
}

const defaultAccessSession = useAccessSession()

export const getAccessSession = defaultAccessSession.getAccessSession
export const clearAccessSession = defaultAccessSession.clearAccessSession
