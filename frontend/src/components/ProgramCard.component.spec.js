/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h, nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ProgramCard from './ProgramCard.vue'

const passthroughStub = defineComponent({
  inheritAttrs: false,
  setup(_, { attrs, slots }) {
    return () => h('span', attrs, slots.default?.())
  },
})

const dropdownStub = defineComponent({
  name: 'ElDropdown',
  inheritAttrs: false,
  emits: ['command'],
  setup(_, { attrs, emit, slots }) {
    return () => h('div', { ...attrs, class: 'dropdown-stub' }, [slots.default?.(), slots.dropdown?.()])
  },
})

const baseProgram = {
  program_id: 'demo-program',
  program_name: '示例小程序',
  is_favorite: false,
  is_archived: false,
  has_stock: true,
  tags: ['积分', '热门'],
  note: '这是备注',
  last_update_time: '2026-09-19T10:20:00+08:00',
  ql_status: 'enabled',
  ql_cron_name: 'demo-cron',
  ql_schedule: '0 10 * * *',
  product_count: 2,
  max_user_points: 1234,
}

function mountCard(program = {}) {
  return mount(ProgramCard, {
    props: {
      program: { ...baseProgram, ...program },
      index: 1,
      titleSizeClass: () => 'is-title-md',
      isUpdatedToday: () => true,
      formatDate: () => '2026/9/19 10:20:00',
      formatQlScheduleTooltip: () => '青龙定时（已启用）demo-cron：0 10 * * *',
    },
    global: {
      stubs: {
        ElDropdown: dropdownStub,
        ElDropdownItem: passthroughStub,
        ElDropdownMenu: passthroughStub,
        ElIcon: passthroughStub,
        ElTooltip: passthroughStub,
      },
    },
  })
}

describe('ProgramCard', () => {
  it('renders the program identity, Qinglong status, tags, note and stock metrics', () => {
    const wrapper = mountCard()

    expect(wrapper.get('.showcase-card-title').text()).toBe('示例小程序')
    expect(wrapper.get('.showcase-card-id').text()).toBe('demo-program')
    expect(wrapper.get('[aria-label="青龙已启用"]').exists()).toBe(true)
    expect(wrapper.get('.inline-tag-chip').text()).toContain('积分 / 热门')
    expect(wrapper.get('.showcase-card-note').text()).toBe('这是备注')
    expect(wrapper.get('.stock-count-value').text()).toBe('2')
    expect(wrapper.get('.ql-schedule-code').text()).toBe('0 10 * * *')
  })

  it('maps card actions to explicit events and guards stock actions without stock', async () => {
    const program = { ...baseProgram }
    const wrapper = mountCard(program)

    await wrapper.get('.showcase-card-title').trigger('click')
    await wrapper.get('.showcase-card-id').trigger('click')
    await wrapper.get('.showcase-card-tag-row').trigger('click')
    await wrapper.get('.showcase-card-note').trigger('click')
    await wrapper.get('button[title="编辑备注"]').trigger('click')
    await wrapper.get('button[title="查看详情"]').trigger('click')
    await wrapper.get('.favorite-toggle').trigger('click')
    await wrapper.get('.stock-count-button').trigger('click')

    expect(wrapper.emitted('copy-name')).toEqual([[program]])
    expect(wrapper.emitted('copy-id')).toEqual([[program]])
    expect(wrapper.emitted('open-tags')).toEqual([[program]])
    expect(wrapper.emitted('open-note')).toEqual([[program]])
    expect(wrapper.emitted('open-detail')).toEqual([[program]])
    expect(wrapper.emitted('toggle-favorite')).toEqual([[program]])
    expect(wrapper.emitted('open-stock')).toEqual([[program]])

    const dropdown = wrapper.findComponent(dropdownStub)
    dropdown.vm.$emit('command', 'archive')
    await nextTick()
    expect(wrapper.emitted('command')).toEqual([['archive', program]])

    const noStockWrapper = mountCard({ has_stock: false, product_count: 0 })
    await noStockWrapper.get('.stock-action').trigger('click')

    expect(noStockWrapper.emitted('open-stock')).toBeUndefined()
  })
})
