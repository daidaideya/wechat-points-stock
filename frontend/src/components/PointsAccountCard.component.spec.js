/* eslint-disable vue/one-component-per-file -- test-only stubs stay co-located with the component suite. */

import { h, defineComponent } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import PointsAccountCard from './PointsAccountCard.vue'

const ElButtonStub = defineComponent({
  name: 'ElButton',
  props: { disabled: Boolean },
  emits: ['click'],
  setup(props, { slots, emit }) {
    return () =>
      h('button', { type: 'button', disabled: props.disabled, onClick: () => emit('click') }, slots.default?.())
  },
})

const ElIconStub = defineComponent({
  name: 'ElIcon',
  setup(_props, { slots }) {
    return () => h('span', slots.default?.())
  },
})

const ElTagStub = defineComponent({
  name: 'ElTag',
  setup(_props, { slots }) {
    return () => h('span', slots.default?.())
  },
})

const ElTooltipStub = defineComponent({
  name: 'ElTooltip',
  setup(_props, { slots }) {
    return () => h('span', slots.default?.())
  },
})

const ElEmptyStub = defineComponent({
  name: 'ElEmpty',
  props: { description: String },
  setup(props) {
    return () => h('div', { class: 'empty-stub' }, props.description)
  },
})

const format = {
  formatDate: (value) => value || '暂无',
  formatNumber: (value) => String(value),
  formatCash: (value) => `¥${value}`,
  formatSigned: (value) => `${value > 0 ? '+' : ''}${value}`,
  formatSignedCash: (value) => `${value > 0 ? '+' : ''}¥${value}`,
  formatPointsValue: (value) => String(value),
  diffClass: (value) => (value > 0 ? 'is-positive' : value < 0 ? 'is-negative' : 'is-neutral'),
}

const item = {
  account: { nickname: '小明', wechat_id: 'wx-1', phone: '13800000000', device: 'iPhone' },
  totalDiff: 12,
  totalCashDiff: -1.5,
  totalPoints: 1234,
  totalCash: 9.5,
  activeProgramCount: 2,
  registeredProgramCount: 3,
  unregisteredProgramCount: 1,
  stale: true,
  latestReportTime: '2026-09-19 10:00:00',
  topPrograms: [
    {
      program_id: 'app-1',
      program_name: '积分小程序',
      report_time: '10:00',
      points: 100,
      cash: 2,
      diff: 4,
      cash_diff: -0.5,
    },
  ],
  unregisteredPrograms: [{ program_id: 'app-2' }],
}

function mountCard(props = {}) {
  return mount(PointsAccountCard, {
    props: { item, format, ...props },
    global: {
      stubs: {
        ElButton: ElButtonStub,
        ElIcon: ElIconStub,
        ElTag: ElTagStub,
        ElTooltip: ElTooltipStub,
        ElEmpty: ElEmptyStub,
      },
    },
  })
}

describe('PointsAccountCard', () => {
  it('renders identity, status, metrics, top programs and action availability', () => {
    const wrapper = mountCard()

    expect(wrapper.get('.points-account-title').text()).toBe('小明')
    expect(wrapper.text()).toContain('今日上涨')
    expect(wrapper.text()).toContain('未更新')
    expect(wrapper.text()).toContain('13800000000')
    expect(wrapper.text()).toContain('¥9.5')
    expect(wrapper.text()).toContain('积分小程序')
    expect(wrapper.text()).toContain('+4')
    expect(wrapper.findAll('button')[0].attributes('disabled')).toBeUndefined()
  })

  it('emits detail and unregistered actions with the account item', async () => {
    const wrapper = mountCard()
    const buttons = wrapper.findAll('button')

    await buttons[0].trigger('click')
    await buttons[1].trigger('click')

    expect(wrapper.emitted('open-unregistered')).toEqual([[item]])
    expect(wrapper.emitted('open-details')).toEqual([[item]])
  })

  it('disables the unregistered action and renders the empty state when appropriate', () => {
    const wrapper = mountCard({ item: { ...item, unregisteredProgramCount: 0, topPrograms: [] } })

    expect(wrapper.findAll('button')[0].attributes('disabled')).toBeDefined()
    expect(wrapper.get('.empty-stub').text()).toBe('暂无积分明细')
  })
})
