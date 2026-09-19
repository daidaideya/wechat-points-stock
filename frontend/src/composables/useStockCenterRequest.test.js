import test from 'node:test'
import assert from 'node:assert/strict'

import { createStockCenterRequestController } from './useStockCenterRequest.js'

function createFakeClient() {
  const calls = []
  return {
    calls,
    get(_path, config) {
      return new Promise((resolve, reject) => {
        calls.push({ config, resolve, reject })
      })
    },
  }
}

const noCacheReader = () => null
const noCacheWriter = () => {}

test('deduplicates the same page and cancels a different stock-center request', async () => {
  const client = createFakeClient()
  const controller = createStockCenterRequestController({
    apiClient: client,
    cacheReader: noCacheReader,
    cacheWriter: noCacheWriter,
  })

  const first = controller.fetch({ page: 1, size: 20 })
  const duplicate = controller.fetch({ page: 1, size: 20 })
  assert.equal(client.calls.length, 1)

  const next = controller.fetch({ page: 1, size: 20, q: '帽子' }, true)
  assert.equal(client.calls.length, 2)
  assert.equal(client.calls[0].config.signal.aborted, true)

  client.calls[1].resolve({ data: { items: ['new'] } })
  const result = await next
  assert.deepEqual(result, { data: { items: ['new'] }, fromCache: false })

  // The superseded request can settle later without clearing the new request.
  client.calls[0].resolve({ data: { items: ['old'] } })
  assert.deepEqual(await first, { data: { items: ['old'] }, fromCache: false })
  assert.deepEqual(await duplicate, { data: { items: ['old'] }, fromCache: false })
})

test('serves a fresh first-page cache without starting a request', async () => {
  const client = createFakeClient()
  const cached = { items: ['cached'] }
  const controller = createStockCenterRequestController({
    apiClient: client,
    cacheReader: () => cached,
  })

  const result = await controller.fetch({ page: 1, size: 20 })
  assert.deepEqual(result, { data: cached, fromCache: true })
  assert.equal(client.calls.length, 0)
})

test('cancel aborts the active request and allows a later request', () => {
  const client = createFakeClient()
  const controller = createStockCenterRequestController({
    apiClient: client,
    cacheReader: noCacheReader,
    cacheWriter: noCacheWriter,
  })

  controller.fetch({ page: 1, size: 20 })
  controller.cancel()
  assert.equal(client.calls[0].config.signal.aborted, true)
})
