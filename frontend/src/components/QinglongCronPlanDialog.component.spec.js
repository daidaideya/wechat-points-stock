/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import QinglongCronPlanDialog from './QinglongCronPlanDialog.vue'

const DialogStub = defineComponent({
  props: { modelValue: Boolean },
  emits: ['update:modelValue'],
  setup(_, { slots, attrs }) {
    return () => h('section', { ...attrs }, [slots.default?.(), slots.footer?.()])
  },
})

const TableStub = defineComponent({
  setup(_, { slots }) {
    return () => h('div', { class: 'table-stub' }, slots.default?.())
  },
})

const TableColumnStub = defineComponent({
  setup(_, { slots }) {
    return () =>
      h(
        'div',
        slots.default?.({
          row: {
            name: '演示脚本',
            newTime: '07:00 / 14:00',
            changed: true,
            applied: false,
            applying: false,
          },
        }),
      )
  },
})

const ButtonStub = defineComponent({
  emits: ['click'],
  setup(_, { emit, slots, attrs }) {
    return () => h('button', { ...attrs, onClick: (event) => emit('click', event) }, slots.default?.())
  },
})

const TagStub = defineComponent({
  setup(_, { slots }) {
    return () => h('span', { class: 'tag-stub' }, slots.default?.())
  },
})

function mountPlanDialog(props = {}) {
  return mount(QinglongCronPlanDialog, {
    props: {
      modelValue: true,
      planForm: {
        startTime: '07:00',
        afternoonStartTime: '14:00',
        intervalMinutes: 2,
        codeOnly: true,
      },
      planItems: [
        {
          name: '签到脚本',
          command: 'node sign.js',
          oldTime: '08:00',
          oldSchedule: '0 8 * * *',
          newTime: '07:00 / 14:00',
          newSchedule: '0 7,14 * * *',
          changed: true,
          applied: false,
          applying: false,
        },
      ],
      ...props,
    },
    global: {
      stubs: {
        ElDialog: DialogStub,
        ElTable: TableStub,
        ElTableColumn: TableColumnStub,
        ElButton: ButtonStub,
        ElTag: TagStub,
      },
    },
  })
}

describe('QinglongCronPlanDialog', () => {
  it('renders the plan summary and per-script application action', () => {
    const wrapper = mountPlanDialog()

    expect(wrapper.text()).toContain('上午 07:00 / 下午 14:00')
    expect(wrapper.text()).toContain('时间窗 07:00 ~ 07:00')
    expect(wrapper.get('[aria-label="应用 演示脚本"]').exists()).toBe(true)
  })

  it('emits parent actions and supports dialog close through v-model', async () => {
    const wrapper = mountPlanDialog()

    await wrapper.get('[aria-label="应用 演示脚本"]').trigger('click')
    const applyAllButton = wrapper.findAll('button').find((button) => button.text() === '应用到青龙')
    await applyAllButton.trigger('click')
    await wrapper.findAll('button')[1].trigger('click')

    expect(wrapper.emitted('apply-item')).toHaveLength(1)
    expect(wrapper.emitted('apply')).toHaveLength(1)
    expect(wrapper.emitted('update:modelValue')).toEqual([[false]])
  })
})
