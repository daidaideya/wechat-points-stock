/* eslint-disable vue/one-component-per-file -- test-only Element Plus stubs stay co-located. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import DashboardActivityPanels from './DashboardActivityPanels.vue'

const ElCardStub = defineComponent({
  name: 'ElCard',
  inheritAttrs: false,
  setup(_props, { attrs, slots }) {
    return () => h('section', attrs, [slots.header?.(), slots.default?.()])
  },
})

const ElButtonStub = defineComponent({
  name: 'ElButton',
  emits: ['click'],
  setup(_props, { attrs, emit, slots }) {
    return () => h('button', { ...attrs, onClick: (event) => emit('click', event) }, slots.default?.())
  },
})

const ElIconStub = defineComponent({
  name: 'ElIcon',
  setup(_props, { slots }) {
    return () => h('span', { class: 'icon-stub' }, slots.default?.())
  },
})

const ElTagStub = defineComponent({
  name: 'ElTag',
  setup(_props, { slots }) {
    return () => h('span', { class: 'tag-stub' }, slots.default?.())
  },
})

const ElSkeletonStub = defineComponent({
  name: 'ElSkeleton',
  setup(_props, { attrs }) {
    return () => h('div', { ...attrs, class: 'skeleton-stub' })
  },
})

const ElEmptyStub = defineComponent({
  name: 'ElEmpty',
  props: { description: String },
  setup(props) {
    return () => h('div', { class: 'empty-stub' }, props.description)
  },
})

const ElementDialogStub = defineComponent({
  name: 'ElDialog',
  props: { modelValue: Boolean },
  emits: ['update:model-value'],
  setup(props, { emit, slots }) {
    return () =>
      h(
        'dialog',
        { open: props.modelValue, class: 'dialog-stub', onClick: () => emit('update:model-value', false) },
        slots.default?.(),
      )
  },
})

const stubs = {
  ElCard: ElCardStub,
  ElButton: ElButtonStub,
  ElIcon: ElIconStub,
  ElTag: ElTagStub,
  ElSkeleton: ElSkeletonStub,
  ElEmpty: ElEmptyStub,
  ElDialog: ElementDialogStub,
}

const defaultProps = {
  loading: false,
  recentUpdates: [
    {
      program_id: 'mini-1',
      program_name: '示例小程序',
      wechat_id: 'wx-1',
      report_time: '2026-09-19T08:00:00Z',
      points: 88,
    },
  ],
  unreportedPrograms: [{ program_id: 'mini-2', program_name: '待上报小程序', tags: ['重点'], is_favorite: true }],
  allUnreportedPrograms: [
    { program_id: 'mini-2', program_name: '待上报小程序', tags: ['重点'], note: '稍后检查', is_favorite: true },
  ],
  unreportedDialogVisible: true,
  unreportedDialogLoading: false,
  formatDate: (value) => `formatted:${value}`,
}

function mountPanels(props = {}) {
  return mount(DashboardActivityPanels, {
    props: { ...defaultProps, ...props },
    global: { stubs },
  })
}

describe('DashboardActivityPanels', () => {
  it('renders recent updates, unreported summaries and the full dialog list', () => {
    const wrapper = mountPanels()

    expect(wrapper.text()).toContain('示例小程序')
    expect(wrapper.text()).toContain('88 积分')
    expect(wrapper.text()).toContain('formatted:2026-09-19T08:00:00Z')
    expect(wrapper.text()).toContain('今天没报的小程序')
    expect(wrapper.text()).toContain('重点关注')
    expect(wrapper.text()).toContain('备注：稍后检查')
  })

  it('forwards refresh and dialog visibility changes', async () => {
    const wrapper = mountPanels()

    await wrapper.get('button').trigger('click')
    await wrapper.get('.dialog-stub').trigger('click')

    expect(wrapper.emitted('refresh')).toHaveLength(1)
    expect(wrapper.emitted('update:unreported-dialog-visible')).toEqual([[false]])
  })

  it('shows loading and empty states for the dialog', () => {
    const loadingWrapper = mountPanels({ unreportedDialogLoading: true, allUnreportedPrograms: [] })
    expect(loadingWrapper.get('[aria-label="正在加载未上报小程序"]')).toBeTruthy()

    const emptyWrapper = mountPanels({ unreportedDialogVisible: true, allUnreportedPrograms: [] })
    expect(emptyWrapper.text()).toContain('今天全部已上报')
  })
})
