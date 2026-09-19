/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import QinglongCronRow from './QinglongCronRow.vue'

const ElementTagStub = defineComponent({
  props: {
    type: { type: String, default: '' },
  },
  setup(props, { slots }) {
    return () => h('span', { class: 'tag-stub', 'data-type': props.type }, slots.default?.())
  },
})

const ElementButtonStub = defineComponent({
  emits: ['click'],
  setup(_, { attrs, emit, slots }) {
    return () =>
      h('button', { ...attrs, class: 'button-stub', onClick: (event) => emit('click', event) }, slots.default?.())
  },
})

const cron = {
  name: '积分同步任务',
  command: 'python sync_points.py --all',
  is_disabled: 1,
  displayTimes: ['08:00', '12:30', '18:45'],
  hasMoreTimes: true,
  moreTimesCount: 2,
  schedule: '0 8,12,18 * * *',
}

function mountRow(props = {}) {
  return mount(QinglongCronRow, {
    props: { cron, excluded: true, crowded: true, sparse: false, minuteGap: 3, ...props },
    global: {
      stubs: {
        ElButton: ElementButtonStub,
        ElTag: ElementTagStub,
      },
    },
  })
}

describe('QinglongCronRow', () => {
  it('renders disabled, excluded and crowded schedule states', () => {
    const wrapper = mountRow()

    expect(wrapper.get('.ql-cron-row').classes()).toEqual(expect.arrayContaining(['disabled', 'excluded', 'crowded']))
    expect(wrapper.get('.ql-cron-name').text()).toBe('积分同步任务')
    expect(wrapper.get('.ql-cron-command').text()).toBe('python sync_points.py --all')
    expect(wrapper.get('.ql-cron-raw').text()).toBe('0 8,12,18 * * *')
    expect(wrapper.findAll('.ql-cron-times .tag-stub').map((tag) => tag.text())).toEqual([
      '08:00',
      '12:30',
      '18:45',
      '+2',
    ])
    expect(wrapper.text()).toContain('已禁用')
    expect(wrapper.text()).toContain('已排除')
    expect(wrapper.text()).toContain('间隔 3 分钟')
  })

  it('uses sparse status only when the row is not crowded and falls back for missing names', () => {
    const wrapper = mountRow({
      cron: { ...cron, name: '', displayTimes: [], hasMoreTimes: false },
      crowded: false,
      sparse: true,
    })

    expect(wrapper.get('.ql-cron-name').text()).toBe('(未命名)')
    expect(wrapper.get('.ql-cron-row').classes()).toContain('sparse')
    expect(wrapper.get('.ql-cron-row').classes()).not.toContain('crowded')
    expect(wrapper.text()).toContain('间隔 3 分钟')
    expect(wrapper.find('.ql-cron-times').text()).toBe('')
  })

  it('forwards edit and exclusion toggle events with the cron payload', async () => {
    const wrapper = mountRow({ excluded: false })
    const buttons = wrapper.findAll('.button-stub')

    expect(buttons).toHaveLength(2)
    expect(buttons[0].text()).toBe('修改时间')
    expect(buttons[1].text()).toBe('排除')

    await buttons[0].trigger('click')
    await buttons[1].trigger('click')

    expect(wrapper.emitted('edit')).toEqual([[cron]])
    expect(wrapper.emitted('toggle-exclude')).toEqual([[cron]])
  })
})
