/* eslint-disable vue/one-component-per-file -- test-only stubs stay co-located with the component suite. */

import { h, defineComponent } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import DashboardMetricCard from './DashboardMetricCard.vue'

const ElCardStub = defineComponent({
  name: 'ElCard',
  inheritAttrs: false,
  emits: ['click'],
  setup(_props, { attrs, slots, emit }) {
    return () => h('article', { ...attrs, onClick: () => emit('click') }, slots.default?.())
  },
})

const ElIconStub = defineComponent({
  name: 'ElIcon',
  setup(_props, { slots }) {
    return () => h('span', slots.default?.())
  },
})

const iconStub = defineComponent({
  name: 'MetricIcon',
  setup() {
    return () => h('span', { class: 'metric-icon-stub' }, 'icon')
  },
})

function mountCard(card) {
  return mount(DashboardMetricCard, {
    props: { card },
    global: {
      stubs: {
        ElCard: ElCardStub,
        ElIcon: ElIconStub,
      },
    },
  })
}

describe('DashboardMetricCard', () => {
  it('renders the metric content, tone and optional emphasis', () => {
    const wrapper = mountCard({
      label: '微信号',
      value: 3,
      description: '系统内已管理账号总数',
      emphasis: '今日活跃 2',
      icon: iconStub,
      tone: 'tone-wheat',
      clickable: true,
    })

    expect(wrapper.get('article').classes()).toEqual(
      expect.arrayContaining(['dashboard-metric-card', 'tone-wheat', 'clickable']),
    )
    expect(wrapper.get('.dashboard-metric-label').text()).toBe('微信号')
    expect(wrapper.get('.dashboard-metric-value').text()).toBe('3')
    expect(wrapper.text()).toContain('系统内已管理账号总数')
    expect(wrapper.text()).toContain('今日活跃 2')
    expect(wrapper.get('.metric-icon-stub').text()).toBe('icon')
  })

  it('only emits the activation payload for clickable cards', async () => {
    const card = {
      label: '小程序',
      value: 1,
      description: '当前已接入监控的小程序数量',
      icon: iconStub,
      tone: 'tone-sand',
      clickable: true,
    }
    const wrapper = mountCard(card)

    await wrapper.get('article').trigger('click')
    expect(wrapper.emitted('activate')).toEqual([[card]])

    const staticWrapper = mountCard({ ...card, clickable: false })
    await staticWrapper.get('article').trigger('click')
    expect(staticWrapper.emitted('activate')).toBeUndefined()
  })
})
