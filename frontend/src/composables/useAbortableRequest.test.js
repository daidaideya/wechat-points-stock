import test from 'node:test'
import assert from 'node:assert/strict'

import { createAbortableRequestController } from './useAbortableRequest.js'

test('starting a request aborts and invalidates the previous request', () => {
  const controller = createAbortableRequestController()
  const first = controller.start()
  const second = controller.start()

  assert.equal(first.signal.aborted, true)
  assert.equal(first.isCurrent(), false)
  assert.equal(second.isCurrent(), true)

  second.finish()
  assert.equal(second.isCurrent(), false)
})

test('cancel aborts the active request and makes it stale', () => {
  const controller = createAbortableRequestController()
  const request = controller.start()

  controller.cancel()

  assert.equal(request.signal.aborted, true)
  assert.equal(request.isCurrent(), false)
})
