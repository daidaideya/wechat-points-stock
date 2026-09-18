import test from 'node:test'
import assert from 'node:assert/strict'

import { useAccessSession } from './useAccessSession.js'

function createStorage(initialValue = '') {
  let value = initialValue
  return {
    getItem(key) {
      return key === 'site_access_key' ? value : null
    },
    removeItem(key) {
      if (key === 'site_access_key') value = ''
    },
  }
}

test('reads and clears the legacy access session through one boundary', () => {
  const session = useAccessSession(createStorage('legacy-key'))

  assert.equal(session.getAccessSession(), 'legacy-key')
  session.clearAccessSession()
  assert.equal(session.getAccessSession(), '')
})

test('does not require browser storage when running without a window', () => {
  const session = useAccessSession(null)

  assert.equal(session.getAccessSession(), '')
  assert.doesNotThrow(() => session.clearAccessSession())
})
