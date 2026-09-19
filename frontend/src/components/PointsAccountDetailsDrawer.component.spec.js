/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import PointsAccountDetailsDrawer from './PointsAccountDetailsDrawer.vue'

const ElementDrawerStub = defineComponent({
  name: 'ElDrawer',
  props: { modelValue: Boolean },
  emits: ['update:modelValue'],
  setup(props, { attrs, emit, slots }) {
    return () =>
      h(
        'section',
        { class: ['drawer-stub', attrs.class], 'data-open': props.modelValue ? 'true' : 'false' },
        props.modelValue
          ? [
              h('div', { class: 'drawer-stub-body' }, slots.default?.()),
              h('button', { class: 'drawer-stub-close', onClick: () => emit('update:modelValue', false) }, '模拟关闭'),
            ]
          : [],
      )
  },
})

const ElementInputStub = defineComponent({
  props: { modelValue: { type: String, default: '' } },
  emits: ['update:modelValue'],
  setup(props, { attrs, emit }) {
    return () =>
      h('input', {
        ...attrs,
        class: 'input-stub',
        value: props.modelValue,
        onInput: (event) => emit('update:modelValue', event.target.value),
      })
  },
})

const passthroughStub = defineComponent({
  inheritAttrs: false,
  setup(_, { attrs, slots }) {
    return () => h('div', attrs, slots.default?.())
  },
})

const ElementButtonStub = defineComponent({
  inheritAttrs: false,
  setup(_, { attrs, slots }) {
    return () => h('button', attrs, slots.default?.())
  },
})

const ElementEmptyStub = defineComponent({
  props: { description: { type: String, default: '' } },
  setup(props) {
    return () => h('div', { class: 'empty-stub' }, props.description)
  },
})

const account = {
  account: { nickname: '张三', wechat_id: 'wx-1', phone: '13800000000', device: 'iPhone' },
  stale: false,
  totalPoints: 1200,
  totalCash: 12.5,
  totalDiff: 80,
  totalCashDiff: 1.5,
  activeProgramCount: 2,
  latestReportTime: '2026-09-19T10:20:00+08:00',
  unregisteredProgramCount: 1,
  unregisteredPrograms: [{ program_id: 'unregistered', program_name: '', report_time: '2026-09-19T10:00:00+08:00' }],
  points: [
    {
      program_id: 'low',
      program_name: '低积分小程序',
      points: 100,
      cash: 1.5,
      diff: -2,
      cash_diff: 0,
      report_time: '2026-09-19T09:00:00+08:00',
    },
    {
      program_id: 'high',
      program_name: '高积分小程序',
      points: 900,
      cash: 11,
      diff: 80,
      cash_diff: 1.5,
      report_time: '2026-09-19T10:00:00+08:00',
    },
    { program_id: 'empty', program_name: '未注册小程序', points: '未注册', cash: '未注册', diff: 0, cash_diff: 0 },
  ],
}

const formatters = {
  formatDate: (value) => `日期:${value || '—'}`,
  formatNumber: (value) => `数字:${value}`,
  formatCash: (value) => `现金:${value}`,
  formatSigned: (value) => `变化:${value}`,
  formatSignedCash: (value) => `现金变化:${value}`,
  formatPointsValue: (value) => `积分:${value}`,
  diffClass: (value) => (value > 0 ? 'is-positive' : value < 0 ? 'is-negative' : 'is-neutral'),
}

function mountDrawer(props = {}) {
  return mount(PointsAccountDetailsDrawer, {
    props: {
      account,
      detailVisible: true,
      unregisteredVisible: false,
      drawerSize: '720px',
      formatters,
      ...props,
    },
    global: {
      stubs: {
        ElDrawer: ElementDrawerStub,
        ElButton: ElementButtonStub,
        ElInput: ElementInputStub,
        ElEmpty: ElementEmptyStub,
        ElIcon: passthroughStub,
        ElOption: passthroughStub,
        ElSelect: passthroughStub,
        ElSwitch: passthroughStub,
        ElTag: passthroughStub,
        Search: passthroughStub,
      },
    },
  })
}

describe('PointsAccountDetailsDrawer', () => {
  it('renders sorted account details and forwards the detail close boundary', async () => {
    const wrapper = mountDrawer()

    expect(wrapper.get('.points-detail-title').text()).toBe('张三')
    expect(wrapper.get('.points-detail-summary').text()).toContain('数字:1200')
    expect(wrapper.findAll('.points-detail-program-card')).toHaveLength(3)
    expect(wrapper.find('.points-detail-program-name').text()).toBe('高积分小程序')

    await wrapper.get('.points-detail-drawer .drawer-stub-close').trigger('click')

    expect(wrapper.emitted('update:detailVisible')).toEqual([[false]])
  })

  it('filters changed programs and renders unregistered programs in the second drawer', async () => {
    const wrapper = mountDrawer()
    const input = wrapper.get('.points-detail-drawer .input-stub')

    await input.setValue('未注册')
    expect(wrapper.findAll('.points-detail-program-card')).toHaveLength(1)
    expect(wrapper.get('.points-detail-program-name').text()).toBe('未注册小程序')

    await wrapper.setProps({ detailVisible: false, unregisteredVisible: true })
    expect(wrapper.get('.points-unregistered-drawer').text()).toContain('未命名小程序')
    expect(wrapper.get('.points-unregistered-drawer').text()).toContain('wx-1')

    await wrapper.get('.points-unregistered-drawer .drawer-stub-close').trigger('click')
    expect(wrapper.emitted('update:unregisteredVisible')).toEqual([[false]])
  })
})
