const DEFAULT_TTL_MS = 15 * 60 * 1000
const SCHEMA_VERSION_KEY = '__schemaVersion'
const SAVED_AT_KEY = '__savedAt'

function resolveStorage(storage) {
  if (storage) return storage
  try {
    return typeof sessionStorage !== 'undefined' ? sessionStorage : null
  } catch {
    return null
  }
}

export function usePageStateCache({ version = 1, ttlMs = DEFAULT_TTL_MS, storage, now = () => Date.now() } = {}) {
  const pageStateStorage = resolveStorage(storage)

  function remove(key) {
    pageStateStorage?.removeItem(key)
  }

  function save(key, state) {
    if (!pageStateStorage) return false
    try {
      pageStateStorage.setItem(key, JSON.stringify({
        ...state,
        [SCHEMA_VERSION_KEY]: version,
        [SAVED_AT_KEY]: now(),
      }))
      return true
    } catch {
      return false
    }
  }

  function read(key) {
    if (!pageStateStorage) return null
    try {
      const raw = pageStateStorage.getItem(key)
      if (!raw) return null
      const parsed = JSON.parse(raw)
      const savedAt = Number(parsed?.[SAVED_AT_KEY])
      const age = now() - savedAt
      if (
        parsed?.[SCHEMA_VERSION_KEY] !== version
        || !Number.isFinite(savedAt)
        || age < 0
        || age > ttlMs
      ) {
        remove(key)
        return null
      }

      const { [SCHEMA_VERSION_KEY]: _schemaVersion, [SAVED_AT_KEY]: _savedAt, ...state } = parsed
      return state
    } catch {
      remove(key)
      return null
    }
  }

  return { save, read, remove }
}
