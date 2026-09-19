/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ProgramMaintenanceDialogs from './ProgramMaintenanceDialogs.vue'

const ElementDialogStub = defineComponent({
  props: {
    modelValue: Boolean,
    title: { type: String, default: '' },
    width: { type: String, default: '' },
  },
  emits: ['update:modelValue'],
  setup(props, { attrs, slots }) {
    return () =>
      props.modelValue
        ? h('section', { class: ['dialog-stub', attrs.class], 'data-title': props.title, 'data-width': props.width }, [
            h('h2', props.title),
            h('div', { class: 'dialog-stub-body' }, slots.default?.()),
            h('footer', { class: 'dialog-stub-footer' }, slots.footer?.()),
          ])
        : null
  },
})

const ElementInputStub = defineComponent({
  props: {
    modelValue: { type: String, default: '' },
    type: { type: String, default: 'text' },
  },
  emits: ['update:modelValue', 'keyup'],
  setup(props, { attrs, emit, slots }) {
    return () =>
      h('div', { class: 'input-stub' }, [
        h(props.type === 'textarea' ? 'textarea' : 'input', {
          ...attrs,
          value: props.modelValue,
          onInput: (event) => emit('update:modelValue', event.target.value),
          onKeyup: (event) => emit('keyup', event),
        }),
        slots.append?.(),
      ])
  },
})

const ElementButtonStub = defineComponent({
  inheritAttrs: false,
  setup(_, { attrs, slots }) {
    return () => h('button', attrs, slots.default?.())
  },
})

const ElementTagStub = defineComponent({
  emits: ['close'],
  setup(_, { attrs, emit, slots }) {
    return () =>
      h('span', { ...attrs, class: ['tag-stub', attrs.class] }, [
        slots.default?.(),
        h('button', { onClick: () => emit('close') }, '×'),
      ])
  },
})

const baseProps = {
  noteVisible: false,
  tagsVisible: true,
  viewportWidth: 800,
  currentProgram: { program_id: 'demo', program_name: '示例小程序', note: '旧备注', tags: ['热门'] },
  availableTags: ['热门', '食品'],
  savingNote: false,
  savingTags: false,
  normalizeTags: (input) => [...new Set(input.map((item) => String(item).trim()).filter(Boolean))].slice(0, 20),
}

function mountDialogs(props = {}) {
  return mount(ProgramMaintenanceDialogs, {
    props: { ...baseProps, ...props },
    global: {
      stubs: {
        ElButton: ElementButtonStub,
        ElDialog: ElementDialogStub,
        ElInput: ElementInputStub,
        ElTag: ElementTagStub,
      },
    },
  })
}

describe('ProgramMaintenanceDialogs', () => {
  it('initializes note and tag editors from the selected program', () => {
    const wrapper = mountDialogs({ noteVisible: true })

    expect(wrapper.get('textarea').element.value).toBe('旧备注')
    expect(wrapper.findAll('.dialog-tag-chip').map((item) => item.text())).toEqual(['热门', '食品', '+ 自定义'])
    expect(wrapper.findAll('.tag-stub').map((item) => item.text())).toContain('热门×')
    expect(wrapper.get('[data-title="编辑标签"]').attributes('data-width')).toBe('620px')
  })

  it('keeps edits local and emits note/tags payloads at the page boundary', async () => {
    const wrapper = mountDialogs({ noteVisible: true })

    await wrapper.get('textarea').setValue('新备注')
    await wrapper.get('[data-title="编辑备注"] .dialog-stub-footer button:last-child').trigger('click')
    expect(wrapper.emitted('save-note')).toEqual([['新备注']])

    const tagsDialog = wrapper.get('[data-title="编辑标签"]')
    await tagsDialog.findAll('.dialog-tag-chip')[1].trigger('click')
    await tagsDialog.get('.tags-custom-input input').setValue('自定义')
    await tagsDialog.get('.tags-custom-input button').trigger('click')
    await tagsDialog.find('.tag-stub button').trigger('click')
    await tagsDialog.get('.dialog-stub-footer button:last-child').trigger('click')

    expect(wrapper.emitted('save-tags')).toEqual([[['食品', '自定义']]])
  })

  it('forwards close actions and reflects loading state on save buttons', async () => {
    const wrapper = mountDialogs({ noteVisible: true, savingNote: true, savingTags: true })

    await wrapper.get('[data-title="编辑备注"] .dialog-stub-footer button:first-child').trigger('click')
    await wrapper.get('[data-title="编辑标签"] .dialog-stub-footer button:first-child').trigger('click')

    expect(wrapper.emitted('update:note-visible')).toEqual([[false]])
    expect(wrapper.emitted('update:tags-visible')).toEqual([[false]])
    expect(wrapper.get('[data-title="编辑备注"] .dialog-stub-footer button:last-child').attributes('loading')).toBe(
      'true',
    )
    expect(wrapper.get('[data-title="编辑标签"] .dialog-stub-footer button:last-child').attributes('loading')).toBe(
      'true',
    )
  })
})
