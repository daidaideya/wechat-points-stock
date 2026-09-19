/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import QinglongCronOverview from './QinglongCronOverview.vue'

const ElementButtonStub = defineComponent({
  props: {
    disabled: Boolean,
    loading: Boolean,
  },
  emits: ['click'],
  setup(props, { emit, slots }) {
    return () =>
      h(
        'button',
        {
          class: 'button-stub',
          disabled: props.disabled,
          'aria-busy': props.loading ? 'true' : 'false',
          onClick: (event) => emit('click', event),
        },
        slots.default?.(),
      )
  },
})

const ElementIconStub = defineComponent({
  setup(_, { slots }) {
    return () => h('span', { class: 'icon-stub' }, slots.default?.())
  },
})

const defaultProps = {
  loading: false,
  scriptCount: 10,
  enabledCount: 8,
  disabledCount: 2,
  nextSlotTime: '07:12',
  nextSlotSchedule: '12 7,14 * * *',
  nextSlotLastName: 'code版示例',
  nextSlotLastSchedule: '07:10',
  intervalMinutes: 2,
  keyword: '',
  crowdedCount: 3,
  excludedCount: 1,
  commandTypeFilter: 'code',
  codeCount: 7,
  otherCount: 3,
}

function mountOverview(props = {}) {
  return mount(QinglongCronOverview, {
    props: { ...defaultProps, ...props },
    global: {
      stubs: {
        ElButton: ElementButtonStub,
        ElIcon: ElementIconStub,
      },
    },
  })
}

describe('QinglongCronOverview', () => {
  it('renders metric, next-slot and filter summaries', () => {
    const wrapper = mountOverview()

    expect(wrapper.text()).toContain('脚本任务10')
    expect(wrapper.text()).toContain('启用8')
    expect(wrapper.text()).toContain('已禁用2')
    expect(wrapper.text()).toContain('07:12')
    expect(wrapper.text()).toContain('12 7,14 * * *')
    expect(wrapper.text()).toContain('基于最新脚本「code版示例」07:10 +2 分钟')
    expect(wrapper.text()).toContain('黑名单 1 个脚本')
    expect(wrapper.get('.ql-filter-chip.active').text()).toContain('code 版 7')
  })

  it('forwards refresh, copy, clear and filter interactions', async () => {
    const wrapper = mountOverview()

    await wrapper.get('.ql-hero-actions .button-stub').trigger('click')
    await wrapper.get('.ql-next-slot-foot .button-stub').trigger('click')
    await wrapper.get('.ql-clear-excluded-btn').trigger('click')
    await wrapper.get('.ql-filter-chip').trigger('click')

    expect(wrapper.emitted('refresh')).toHaveLength(1)
    expect(wrapper.emitted('copy-next-slot')).toHaveLength(1)
    expect(wrapper.emitted('clear-excluded')).toHaveLength(1)
    expect(wrapper.emitted('update:command-type-filter')).toEqual([['all']])
  })

  it('forwards keyword changes and disables copy when no suggestion exists', async () => {
    const wrapper = mountOverview({ nextSlotSchedule: '' })

    await wrapper.get('.ql-meta-search').setValue('会员')

    expect(wrapper.emitted('update:keyword')).toEqual([['会员']])
    expect(wrapper.get('.ql-next-slot-foot .button-stub').attributes('disabled')).toBeDefined()
  })
})
