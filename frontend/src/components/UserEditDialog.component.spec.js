/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UserEditDialog from './UserEditDialog.vue'

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
        h('footer', { class: 'dialog-stub-footer' }, slots.footer?.()),
        h('button', { class: 'dialog-stub-closed', onClick: () => emit('closed') }, '模拟关闭完成'),
      ])
  },
})

const ElementInputStub = defineComponent({
  props: {
    modelValue: { type: String, default: '' },
    disabled: Boolean,
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () =>
      h('input', {
        class: 'input-stub',
        value: props.modelValue,
        disabled: props.disabled,
        onInput: (event) => emit('update:modelValue', event.target.value),
      })
  },
})

const ElementButtonStub = defineComponent({
  props: {
    loading: Boolean,
  },
  emits: ['click'],
  setup(props, { attrs, emit, slots }) {
    return () =>
      h(
        'button',
        {
          ...attrs,
          class: ['button-stub', attrs.class],
          'aria-busy': props.loading ? 'true' : 'false',
          onClick: (event) => emit('click', event),
        },
        slots.default?.(),
      )
  },
})

const passthroughStub = defineComponent({
  inheritAttrs: false,
  setup(_, { attrs, slots }) {
    return () => h('div', attrs, slots.default?.())
  },
})

const form = {
  wechat_id: 'wx-alice',
  nickname: 'Alice',
  device: 'iPhone',
  phone: '13800138000',
}

function mountDialog(props = {}) {
  return mount(UserEditDialog, {
    props: {
      modelValue: true,
      editing: true,
      form,
      ...props,
    },
    global: {
      stubs: {
        ElButton: ElementButtonStub,
        ElDialog: ElementDialogStub,
        ElForm: passthroughStub,
        ElFormItem: passthroughStub,
        ElInput: ElementInputStub,
      },
    },
  })
}

describe('UserEditDialog', () => {
  it('renders the editing title and locks the WeChat id field', () => {
    const wrapper = mountDialog()
    const inputs = wrapper.findAll('.input-stub')

    expect(wrapper.get('.dialog-stub-title').text()).toBe('编辑用户')
    expect(inputs).toHaveLength(4)
    expect(inputs[0].element.value).toBe('wx-alice')
    expect(inputs[0].attributes('disabled')).toBeDefined()
    expect(inputs[1].element.value).toBe('Alice')
    expect(inputs[2].element.value).toBe('iPhone')
    expect(inputs[3].element.value).toBe('13800138000')
  })

  it('forwards field updates with their whitelist key and supports add mode', async () => {
    const editingWrapper = mountDialog()
    const editingInputs = editingWrapper.findAll('.input-stub')

    await editingInputs[1].setValue('新昵称')
    await editingInputs[3].setValue('13900139000')

    expect(editingWrapper.emitted('update-field')).toEqual([
      ['nickname', '新昵称'],
      ['phone', '13900139000'],
    ])

    const addWrapper = mountDialog({ editing: false, form: { wechat_id: '', nickname: '', device: '', phone: '' } })
    const addInput = addWrapper.get('.input-stub')

    expect(addWrapper.get('.dialog-stub-title').text()).toBe('新增用户')
    expect(addInput.attributes('disabled')).toBeUndefined()
    await addInput.setValue('wx-new')
    expect(addWrapper.emitted('update-field')).toEqual([['wechat_id', 'wx-new']])
  })

  it('keeps save, cancel and closed events separate and exposes saving state', async () => {
    const wrapper = mountDialog({ saving: true })
    const buttons = wrapper.findAll('.button-stub')

    expect(buttons).toHaveLength(2)
    expect(buttons[1].attributes('aria-busy')).toBe('true')

    await buttons[1].trigger('click')
    await buttons[0].trigger('click')
    await wrapper.get('.dialog-stub-closed').trigger('click')

    expect(wrapper.emitted('save')).toEqual([[]])
    expect(wrapper.emitted('update:modelValue')).toEqual([[false]])
    expect(wrapper.emitted('closed')).toEqual([[]])
  })
})
