import test from 'node:test'
import assert from 'node:assert/strict'

import { usePageStateCache } from './usePageStateCache.js'

function createStorage() {
  const values = new Map()
  return {
    values,
    getItem(key) {
      return values.get(key) || null
    },
    setItem(key, value) {
      values.set(key, value)
    },
    removeItem(key) {
      values.delete(key)
    },
  }
}

test('saves versioned page state and returns the payload without metadata', () => {
  const storage = createStorage()
  let currentTime = 1000
  const cache = usePageStateCache({ version: 2, ttlMs: 500, storage, now: () => currentTime })

  assert.equal(cache.save('programs', { searchKeyword: 'coffee', scrollY: 120 }), true)
  assert.deepEqual(cache.read('programs'), { searchKeyword: 'coffee', scrollY: 120 })

  currentTime += 501
  assert.equal(cache.read('programs'), null)
  assert.equal(storage.values.has('programs'), false)
})

test('invalidates a state saved by another schema version', () => {
  const storage = createStorage()
  const oldCache = usePageStateCache({ version: 1, storage, now: () => 1000 })
  const newCache = usePageStateCache({ version: 2, storage, now: () => 1000 })

  oldCache.save('programs', { page: 3 })
  assert.equal(newCache.read('programs'), null)
  assert.equal(storage.values.has('programs'), false)
})
