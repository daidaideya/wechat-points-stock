/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h, nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ProgramCardActions from './ProgramCardActions.vue'

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
  tags: ['积分'],
  last_update_time: '2026-09-19T10:20:00+08:00',
}

function mountActions(program = {}, extraProps = {}) {
  return mount(ProgramCardActions, {
    props: {
      program: { ...baseProgram, ...program },
      formatDate: () => '2026/9/19 10:20:00',
      ...extraProps,
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

describe('ProgramCardActions', () => {
  it('renders footer actions and forwards program-scoped interactions', async () => {
    const program = { ...baseProgram }
    const wrapper = mountActions(program)

    await wrapper.get('button[title="编辑备注"]').trigger('click')
    await wrapper.get('button[title="查看详情"]').trigger('click')
    await wrapper.get('.favorite-toggle').trigger('click')
    await wrapper.get('button[title="编辑标签"]').trigger('click')
    await wrapper.get('.stock-action').trigger('click')

    expect(wrapper.emitted('open-note')).toEqual([[program]])
    expect(wrapper.emitted('open-detail')).toEqual([[program]])
    expect(wrapper.emitted('toggle-favorite')).toEqual([[program]])
    expect(wrapper.emitted('open-tags')).toEqual([[program]])
    expect(wrapper.emitted('open-stock')).toEqual([[program]])

    const dropdown = wrapper.findComponent(dropdownStub)
    dropdown.vm.$emit('command', 'archive')
    await nextTick()
    expect(wrapper.emitted('command')).toEqual([['archive', program]])
  })

  it('blocks stock navigation without stock and disables busy menu actions', async () => {
    const wrapper = mountActions({ has_stock: false }, { archivingProgramId: 'demo-program' })

    await wrapper.get('.stock-action').trigger('click')

    expect(wrapper.emitted('open-stock')).toBeUndefined()
    expect(wrapper.get('button[title="更多操作"]').attributes('disabled')).toBeDefined()
    expect(wrapper.get('.showcase-button-loading').exists()).toBe(true)
  })
})
