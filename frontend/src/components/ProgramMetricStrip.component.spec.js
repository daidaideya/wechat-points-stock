import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ProgramMetricStrip from './ProgramMetricStrip.vue'

const iconStub = {
  template: '<span><slot /></span>',
}

function mountMetrics(program) {
  return mount(ProgramMetricStrip, {
    props: { program },
    global: {
      stubs: {
        ElIcon: iconStub,
      },
    },
  })
}

describe('ProgramMetricStrip', () => {
  it('does not render a metric row when the program has no metrics', () => {
    const wrapper = mountMetrics({})

    expect(wrapper.find('.showcase-card-stock-row').exists()).toBe(false)
  })

  it('formats metrics and emits stock navigation from the shared component', async () => {
    const wrapper = mountMetrics({
      has_stock: true,
      product_count: 2,
      max_user_points: 12345,
      max_user_cash: 1234.5,
      stock_change: { added_count: 3, removed_count: 1 },
    })

    expect(wrapper.get('.stock-count-value').text()).toBe('2')
    expect(wrapper.text()).toContain('1.2w')
    expect(wrapper.text()).toContain('¥1,234.5')
    expect(wrapper.text()).toContain('+3')
    expect(wrapper.text()).toContain('-1')

    await wrapper.get('.stock-count-button').trigger('click')

    expect(wrapper.emitted('open-stock')).toHaveLength(1)
  })

  it('hides invalid cash values while keeping valid point metrics', () => {
    const wrapper = mountMetrics({ max_user_points: 1250, max_user_cash: 'not-a-number' })

    expect(wrapper.text()).toContain('1.3k')
    expect(wrapper.find('.cash-count-display').exists()).toBe(false)
  })

  it('shows a review status for incomplete stock snapshots', () => {
    const wrapper = mountMetrics({
      stock_snapshot: {
        is_complete: false,
        status: 'count_mismatch',
        reported_product_count: 2,
        expected_product_count: 3,
      },
    })

    const warning = wrapper.get('.stock-snapshot-warning')
    expect(warning.text()).toBe('库存快照需复核')
    expect(warning.attributes('title')).toContain('2/3')
    expect(warning.attributes('aria-label')).toBe('库存快照需复核')
  })
})
