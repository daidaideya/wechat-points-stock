/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import QinglongCronEditDialog from './QinglongCronEditDialog.vue'

const ElementDialogStub = defineComponent({
  props: {
    modelValue: Boolean,
    title: { type: String, default: '' },
    width: { type: String, default: '' },
    top: { type: String, default: '' },
  },
  emits: ['update:modelValue'],
  setup(props, { emit, slots }) {
    return () =>
      h(
        'section',
        {
          class: 'dialog-stub',
          'data-title': props.title,
          'data-width': props.width,
          'data-top': props.top,
        },
        props.modelValue
          ? [
              h('div', { class: 'dialog-stub-body' }, slots.default?.()),
              h('footer', { class: 'dialog-stub-footer' }, slots.footer?.()),
              h('button', { class: 'dialog-stub-close', onClick: () => emit('update:modelValue', false) }, '关闭'),
            ]
          : null,
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

const ElementButtonStub = defineComponent({
  inheritAttrs: false,
  setup(_, { attrs, slots }) {
    return () => h('button', attrs, slots.default?.())
  },
})

const baseProps = {
  modelValue: true,
  isMobile: false,
  cron: { name: '积分脚本', command: 'python /scripts/points.py' },
  schedule: '0 9 * * *',
  previewTimes: ['09:00'],
  applying: false,
}

function mountDialog(props = {}) {
  return mount(QinglongCronEditDialog, {
    props: { ...baseProps, ...props },
    global: {
      stubs: {
        ElButton: ElementButtonStub,
        ElDialog: ElementDialogStub,
        ElInput: ElementInputStub,
      },
    },
  })
}

describe('QinglongCronEditDialog', () => {
  it('renders cron identity, schedule preview and responsive dialog sizing', () => {
    const wrapper = mountDialog({ isMobile: true })
    const dialog = wrapper.get('[data-title="修改执行时间"]')

    expect(dialog.text()).toContain('积分脚本')
    expect(dialog.text()).toContain('python /scripts/points.py')
    expect(dialog.text()).toContain('每日执行：09:00')
    expect(dialog.attributes('data-width')).toBe('92%')
    expect(dialog.attributes('data-top')).toBe('5vh')
    expect(wrapper.get('#ql-edit-schedule').element.value).toBe('0 9 * * *')
  })

  it('keeps schedule editing at the page boundary and forwards save/close actions', async () => {
    const wrapper = mountDialog()

    await wrapper.get('#ql-edit-schedule').setValue('30 10 * * *')
    await wrapper.get('.dialog-stub-footer button:last-child').trigger('click')
    await wrapper.get('.dialog-stub-close').trigger('click')

    expect(wrapper.emitted('update:schedule')).toEqual([['30 10 * * *']])
    expect(wrapper.emitted('save')).toEqual([[]])
    expect(wrapper.emitted('update:modelValue')).toEqual([[false]])
  })

  it('shows invalid expressions and disables saving while applying', () => {
    const wrapper = mountDialog({ previewTimes: [], applying: true })

    expect(wrapper.text()).toContain('无法解析该表达式')
    expect(wrapper.get('.dialog-stub-footer button:last-child').attributes('disabled')).toBeDefined()
    expect(wrapper.get('.dialog-stub-footer button:last-child').attributes('loading')).toBe('true')
  })
})
