/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UserPointsDialog from './UserPointsDialog.vue'

const ElementDialogStub = defineComponent({
  name: 'ElDialog',
  props: {
    modelValue: Boolean,
    title: { type: String, default: '' },
  },
  emits: ['update:modelValue', 'closed'],
  setup(props, { emit, slots }) {
    return () =>
      h('section', { class: 'dialog-stub', 'aria-label': props.title }, [
        h('h2', { class: 'dialog-stub-title' }, props.title),
        h('div', { class: 'dialog-stub-body' }, slots.default?.()),
        h('button', { class: 'dialog-stub-update', onClick: () => emit('update:modelValue', false) }, '模拟关闭'),
        h('button', { class: 'dialog-stub-closed', onClick: () => emit('closed') }, '模拟关闭完成'),
      ])
  },
})

const ElementEmptyStub = defineComponent({
  props: { description: { type: String, default: '' } },
  setup(props) {
    return () => h('div', { class: 'empty-stub' }, props.description)
  },
})

const ElementSkeletonStub = defineComponent({
  setup() {
    return () => h('div', { class: 'skeleton-stub' }, '加载中')
  },
})

const ElementTableColumnStub = defineComponent({
  setup() {
    return () => null
  },
})

const passthroughStub = defineComponent({
  inheritAttrs: false,
  setup(_, { attrs, slots }) {
    return () => h('div', attrs, slots.default?.())
  },
})

const pointItems = [
  {
    program_name: '积分小程序',
    points: 1280,
    cash: 12.5,
    diff: 80,
    cash_diff: 1.5,
    report_time: '2026-09-19T10:20:00+08:00',
  },
  {
    program_name: '',
    points: '未注册',
    cash: '未注册',
    diff: null,
    cash_diff: undefined,
    report_time: '',
  },
]

function mountDialog(props = {}) {
  return mount(UserPointsDialog, {
    props: {
      modelValue: true,
      title: '张三的积分详情',
      items: pointItems,
      ...props,
    },
    global: {
      stubs: {
        ElDialog: ElementDialogStub,
        ElEmpty: ElementEmptyStub,
        ElSkeleton: ElementSkeletonStub,
        ElTable: passthroughStub,
        ElTableColumn: ElementTableColumnStub,
      },
    },
  })
}

describe('UserPointsDialog', () => {
  it('renders point summaries, cash values, change values and fallback labels', () => {
    const wrapper = mountDialog()

    expect(wrapper.get('.dialog-stub-title').text()).toBe('张三的积分详情')
    expect(wrapper.findAll('.users-points-mobile-card')).toHaveLength(2)
    expect(wrapper.text()).toContain('积分小程序')
    expect(wrapper.text()).toContain('1280 积分')
    expect(wrapper.text()).toContain('¥12.5')
    expect(wrapper.text()).toContain('积分变化：80')
    expect(wrapper.text()).toContain('现金变化：1.5')
    expect(wrapper.text()).toContain('未知小程序')
    expect(wrapper.text()).toContain('未注册 积分')
    expect(wrapper.text()).toContain('积分变化：0')
    expect(wrapper.text()).toContain('现金变化：0')
    expect(wrapper.text()).toContain('暂无')
  })

  it('shows loading and empty semantics without stale point rows', () => {
    const loadingWrapper = mountDialog({ loading: true })
    const loading = loadingWrapper.get('[role="status"]')

    expect(loading.attributes('aria-live')).toBe('polite')
    expect(loading.attributes('aria-busy')).toBe('true')
    expect(loading.attributes('aria-label')).toBe('正在加载积分详情')
    expect(loadingWrapper.find('.users-points-mobile-card').exists()).toBe(false)

    const emptyWrapper = mountDialog({ items: [] })
    expect(emptyWrapper.get('.empty-stub').text()).toBe('暂无积分详情')
    expect(emptyWrapper.find('.users-points-mobile-card').exists()).toBe(false)
  })

  it('forwards model updates and the closed event from the dialog boundary', async () => {
    const wrapper = mountDialog()

    await wrapper.get('.dialog-stub-update').trigger('click')
    await wrapper.get('.dialog-stub-closed').trigger('click')

    expect(wrapper.emitted('update:modelValue')).toEqual([[false]])
    expect(wrapper.emitted('closed')).toEqual([[]])
  })
})
