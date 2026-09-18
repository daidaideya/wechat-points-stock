import test from 'node:test'
import assert from 'node:assert/strict'

import { createInfiniteScrollController } from './useInfiniteScroll.js'

test('observes the target, loads on intersection, and disconnects cleanly', () => {
  const originalObserver = globalThis.IntersectionObserver
  const instances = []

  class FakeIntersectionObserver {
    constructor(callback, options) {
      this.callback = callback
      this.options = options
      this.target = null
      this.disconnected = false
      instances.push(this)
    }

    observe(target) {
      this.target = target
    }

    disconnect() {
      this.disconnected = true
    }

    trigger(entries) {
      this.callback(entries)
    }
  }

  globalThis.IntersectionObserver = FakeIntersectionObserver
  try {
    const target = { id: 'sentinel' }
    let loadCount = 0
    const controller = createInfiniteScrollController({
      target,
      rootMargin: '180px 0px',
      canLoadMore: () => true,
      onLoadMore: () => {
        loadCount += 1
      },
    })

    controller.observe()
    assert.equal(instances.length, 1)
    assert.equal(instances[0].target, target)
    assert.equal(instances[0].options.rootMargin, '180px 0px')
    instances[0].trigger([{ isIntersecting: false }])
    assert.equal(loadCount, 0)
    instances[0].trigger([{ isIntersecting: true }])
    assert.equal(loadCount, 1)

    controller.disconnect()
    assert.equal(instances[0].disconnected, true)
  } finally {
    if (originalObserver === undefined) delete globalThis.IntersectionObserver
    else globalThis.IntersectionObserver = originalObserver
  }
})

test('does not create an observer when loading more is not allowed', () => {
  const originalObserver = globalThis.IntersectionObserver
  let created = false
  globalThis.IntersectionObserver = class FakeIntersectionObserver {
    constructor() {
      created = true
    }
  }

  try {
    const controller = createInfiniteScrollController({
      target: { id: 'sentinel' },
      canLoadMore: () => false,
      onLoadMore: () => {},
    })
    controller.observe()
    assert.equal(created, false)
  } finally {
    if (originalObserver === undefined) delete globalThis.IntersectionObserver
    else globalThis.IntersectionObserver = originalObserver
  }
})
