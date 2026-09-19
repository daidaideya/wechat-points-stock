/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus and row stubs. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import QinglongCronTimeline from './QinglongCronTimeline.vue'

const ElementCardStub = defineComponent({
  inheritAttrs: false,
  setup(_, { attrs, slots }) {
    return () =>
      h('section', { class: ['card-stub', attrs.class] }, [
        h('header', { class: 'card-stub-header' }, slots.header?.()),
        h('div', { class: 'card-stub-body' }, slots.default?.()),
      ])
  },
})

const ElementSwitchStub = defineComponent({
  props: { modelValue: Boolean },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () =>
      h(
        'button',
        {
          class: 'switch-stub',
          'aria-pressed': String(props.modelValue),
          onClick: () => emit('update:modelValue', !props.modelValue),
        },
        '显示已禁用',
      )
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

const CronRowStub = defineComponent({
  props: {
    cron: { type: Object, required: true },
    excluded: Boolean,
    crowded: Boolean,
    sparse: Boolean,
    minuteGap: { type: [Number, String], default: '-' },
  },
  emits: ['edit', 'toggle-exclude'],
  setup(props, { emit }) {
    return () =>
      h('article', { class: 'timeline-row', 'data-name': props.cron.name }, [
        h('span', { class: 'timeline-row-gap' }, String(props.minuteGap)),
        h('button', { class: 'timeline-row-edit', onClick: () => emit('edit', props.cron) }, '修改时间'),
        h('button', { class: 'timeline-row-exclude', onClick: () => emit('toggle-exclude', props.cron) }, '排除'),
      ])
  },
})

const groups = [
  {
    hour: 7,
    crons: [{ id: 'cron-1', name: '早间脚本' }],
  },
  {
    hour: -1,
    crons: [{ id: 'cron-2', name: '无法解析脚本' }],
  },
]

function mountTimeline(props = {}) {
  return mount(QinglongCronTimeline, {
    props: {
      loading: false,
      filteredGroups: groups,
      intervalMinutes: 5,
      showDisabled: false,
      cronKey: (cron) => cron.id,
      isExcluded: () => false,
      isCrowded: (cron) => cron.id === 'cron-1',
      isSparse: () => false,
      minuteGap: (cron) => (cron.id === 'cron-1' ? 2 : '-'),
      ...props,
    },
    global: {
      stubs: {
        ElCard: ElementCardStub,
        ElEmpty: ElementEmptyStub,
        ElSkeleton: ElementSkeletonStub,
        ElSwitch: ElementSwitchStub,
        QinglongCronRow: CronRowStub,
      },
    },
  })
}

describe('QinglongCronTimeline', () => {
  it('renders grouped hours, interval guidance and row state inputs', () => {
    const wrapper = mountTimeline()

    expect(wrapper.get('.ql-card-title').text()).toBe('当前时间线')
    expect(wrapper.get('.ql-card-subtitle').text()).toContain('5 分钟')
    expect(wrapper.findAll('.ql-hour-group')).toHaveLength(2)
    expect(wrapper.find('.ql-hour-label').text()).toBe('07:00')
    expect(wrapper.findAll('.timeline-row')).toHaveLength(2)
    expect(wrapper.get('[data-name="早间脚本"] .timeline-row-gap').text()).toBe('2')
  })

  it('forwards switch and row actions without taking over page behavior', async () => {
    const wrapper = mountTimeline()

    await wrapper.get('.switch-stub').trigger('click')
    await wrapper.get('[data-name="早间脚本"] .timeline-row-edit').trigger('click')
    await wrapper.get('[data-name="早间脚本"] .timeline-row-exclude').trigger('click')

    expect(wrapper.emitted('update:showDisabled')).toEqual([[true]])
    expect(wrapper.emitted('edit')).toEqual([[groups[0].crons[0]]])
    expect(wrapper.emitted('toggle-exclude')).toEqual([[groups[0].crons[0]]])
  })

  it('keeps loading and empty states mutually exclusive with rows', () => {
    const loadingWrapper = mountTimeline({ loading: true })
    expect(loadingWrapper.find('.skeleton-stub').exists()).toBe(true)
    expect(loadingWrapper.find('.timeline-row').exists()).toBe(false)

    const emptyWrapper = mountTimeline({ filteredGroups: [] })
    expect(emptyWrapper.get('.empty-stub').text()).toBe('没有匹配的任务')
    expect(emptyWrapper.find('.timeline-row').exists()).toBe(false)
  })
})
