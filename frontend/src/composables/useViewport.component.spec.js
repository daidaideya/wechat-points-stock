import { h, nextTick, defineComponent } from 'vue'
import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { useViewport } from './useViewport'

const ViewportHarness = defineComponent({
  name: 'ViewportHarness',
  setup() {
    const { width, isMobile } = useViewport({ mobileMax: 900 })
    return { width, isMobile }
  },
  render() {
    return h(
      'output',
      {
        'data-width': String(this.width),
        'data-mobile': String(this.isMobile),
      },
      `${this.width}/${this.isMobile}`,
    )
  },
})

function setViewportWidth(width) {
  Object.defineProperty(window, 'innerWidth', {
    configurable: true,
    value: width,
  })
}

function readViewport(wrapper) {
  const output = wrapper.get('output')
  return {
    width: Number(output.attributes('data-width')),
    isMobile: output.attributes('data-mobile') === 'true',
  }
}

describe('useViewport', () => {
  beforeEach(() => {
    setViewportWidth(1200)
  })

  afterEach(() => {
    setViewportWidth(1200)
  })

  it('tracks the initial width and updates the mobile boundary on resize', async () => {
    const wrapper = mount(ViewportHarness)
    expect(readViewport(wrapper)).toEqual({ width: 1200, isMobile: false })

    setViewportWidth(900)
    window.dispatchEvent(new Event('resize'))
    await nextTick()
    expect(readViewport(wrapper)).toEqual({ width: 900, isMobile: true })

    setViewportWidth(901)
    window.dispatchEvent(new Event('resize'))
    await nextTick()
    expect(readViewport(wrapper)).toEqual({ width: 901, isMobile: false })

    wrapper.unmount()
  })

  it('removes its resize listener when the owner component unmounts', () => {
    const originalRemoveEventListener = window.removeEventListener
    const removedListeners = []
    window.removeEventListener = function (...args) {
      removedListeners.push(args)
      return originalRemoveEventListener.apply(this, args)
    }

    try {
      const wrapper = mount(ViewportHarness)
      wrapper.unmount()
      expect(removedListeners.some(([type]) => type === 'resize')).toBe(true)
    } finally {
      window.removeEventListener = originalRemoveEventListener
    }
  })
})
