/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h, inject, provide } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UserDesktopTable from './UserDesktopTable.vue'

const tableRowsKey = Symbol('tableRows')

const ElementTableStub = defineComponent({
  props: {
    data: { type: Array, default: () => [] },
  },
  setup(props, { slots }) {
    provide(tableRowsKey, props.data)
    return () => h('div', { class: 'table-stub' }, slots.default?.())
  },
})

const ElementTableColumnStub = defineComponent({
  props: {
    label: { type: String, default: '' },
    prop: { type: String, default: '' },
  },
  setup(props, { slots }) {
    const rows = inject(tableRowsKey, [])
    return () =>
      h(
        'div',
        { class: 'column-stub', 'data-label': props.label },
        rows.map((row, index) =>
          h(
            'span',
            { class: 'cell-stub' },
            slots.default ? slots.default({ row, $index: index }) : (row[props.prop] ?? ''),
          ),
        ),
      )
  },
})

const ElementButtonStub = defineComponent({
  props: {
    loading: Boolean,
  },
  emits: ['click'],
  setup(props, { attrs, emit, slots }) {
    return () =>
      h(
        'button',
        {
          ...attrs,
          class: ['button-stub', attrs.class],
          'aria-busy': props.loading ? 'true' : 'false',
          onClick: (event) => emit('click', event),
        },
        slots.default?.(),
      )
  },
})

const passthroughStub = defineComponent({
  inheritAttrs: false,
  setup(_, { attrs, slots }) {
    return () => h('span', attrs, slots.default?.())
  },
})

const firstUser = {
  wechat_id: 'wx-alice',
  nickname: 'Alice',
  phone: '13800138000',
  device: 'iPhone',
  active_program_count: 2,
  active_app_count: 1,
}

const secondUser = {
  wechat_id: '13900139000',
  nickname: '',
  phone: '',
  device: '',
  active_program_count: 0,
  active_app_count: 3,
}

function mountTable(props = {}) {
  return mount(UserDesktopTable, {
    props: { items: [firstUser, secondUser], ...props },
    global: {
      stubs: {
        ElButton: ElementButtonStub,
        ElIcon: passthroughStub,
        ElTable: ElementTableStub,
        ElTableColumn: ElementTableColumnStub,
      },
    },
  })
}

describe('UserDesktopTable', () => {
  it('renders rows with sort positions, identity fallbacks, contact data and counts', () => {
    const wrapper = mountTable()

    expect(wrapper.findAll('.users-sort-index')).toHaveLength(2)
    expect(wrapper.findAll('.users-sort-index').map((node) => node.text())).toEqual(['1', '2'])
    expect(wrapper.text()).toContain('Alice')
    expect(wrapper.text()).toContain('13800138000')
    expect(wrapper.text()).toContain('wx-alice')
    expect(wrapper.text()).toContain('iPhone')
    expect(wrapper.text()).toContain('2')
    expect(wrapper.text()).toContain('1')
    expect(wrapper.text()).toContain('13900139000')
    expect(wrapper.text()).toContain('3')
    expect(wrapper.text()).toContain('—')
  })

  it('forwards each row action and marks only the deleting row busy', async () => {
    const wrapper = mountTable({ deletingWechatId: secondUser.wechat_id })
    const buttons = wrapper.findAll('.button-stub')

    expect(buttons).toHaveLength(6)
    expect(buttons.slice(0, 3).every((button) => button.attributes('aria-busy') === 'false')).toBe(true)
    expect(buttons[5].attributes('aria-busy')).toBe('true')

    await buttons[0].trigger('click')
    await buttons[1].trigger('click')
    await buttons[2].trigger('click')
    await buttons[3].trigger('click')
    await buttons[4].trigger('click')
    await buttons[5].trigger('click')

    expect(wrapper.emitted('edit')?.map(([item]) => item)).toEqual([firstUser, secondUser])
    expect(wrapper.emitted('view-points')?.map(([item]) => item)).toEqual([firstUser, secondUser])
    expect(wrapper.emitted('remove')).toEqual([[firstUser], [secondUser]])
  })

  it('renders an empty table boundary without inventing rows', () => {
    const wrapper = mountTable({ items: [] })

    expect(wrapper.findAll('.users-sort-index')).toHaveLength(0)
    expect(wrapper.findAll('.button-stub')).toHaveLength(0)
    expect(wrapper.get('.table-stub').exists()).toBe(true)
  })
})
