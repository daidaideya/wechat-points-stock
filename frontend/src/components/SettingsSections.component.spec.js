/* eslint-disable vue/one-component-per-file -- test-only stubs stay co-located with the section suite. */

import { h, defineComponent } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import SettingsBarkSection from './SettingsBarkSection.vue'
import SettingsDatabaseSection from './SettingsDatabaseSection.vue'
import SettingsGeneralSection from './SettingsGeneralSection.vue'
import SettingsQinglongSection from './SettingsQinglongSection.vue'

const ElFormStub = defineComponent({
  name: 'ElForm',
  props: { disabled: Boolean },
  setup(props, { slots }) {
    return () => h('form', { 'data-disabled': String(props.disabled) }, slots.default?.())
  },
})

const ElFormItemStub = defineComponent({
  name: 'ElFormItem',
  props: { label: String },
  setup(props, { slots }) {
    return () =>
      h('div', { 'data-label': props.label }, [h('span', { class: 'form-item-label' }, props.label), slots.default?.()])
  },
})

const ElButtonStub = defineComponent({
  name: 'ElButton',
  props: { disabled: Boolean, loading: Boolean, type: String },
  emits: ['click'],
  setup(props, { slots, emit }) {
    return () =>
      h(
        'button',
        {
          type: 'button',
          disabled: props.disabled,
          'data-loading': String(props.loading),
          onClick: () => emit('click'),
        },
        slots.default?.(),
      )
  },
})

const ElInputStub = defineComponent({
  name: 'ElInput',
  props: { modelValue: [String, Number], disabled: Boolean, type: String },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () =>
      h('input', {
        value: props.modelValue ?? '',
        type: props.type || 'text',
        disabled: props.disabled,
        onInput: (event) => emit('update:modelValue', event.target.value),
      })
  },
})

const ElInputNumberStub = defineComponent({
  name: 'ElInputNumber',
  props: { modelValue: [String, Number], disabled: Boolean },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () =>
      h('input', {
        value: props.modelValue ?? '',
        type: 'number',
        disabled: props.disabled,
        onInput: (event) => emit('update:modelValue', Number(event.target.value)),
      })
  },
})

const ElSwitchStub = defineComponent({
  name: 'ElSwitch',
  props: { modelValue: Boolean, disabled: Boolean },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () =>
      h('input', {
        type: 'checkbox',
        checked: props.modelValue,
        disabled: props.disabled,
        onChange: (event) => emit('update:modelValue', event.target.checked),
      })
  },
})

const ElRadioGroupStub = defineComponent({
  name: 'ElRadioGroup',
  props: { modelValue: String, disabled: Boolean },
  emits: ['update:modelValue'],
  setup(props, { slots }) {
    return () =>
      h('div', { 'data-value': props.modelValue, 'data-disabled': String(props.disabled) }, slots.default?.())
  },
})

const ElRadioButtonStub = defineComponent({
  name: 'ElRadioButton',
  props: { value: String },
  setup(_props, { slots }) {
    return () => h('span', slots.default?.())
  },
})

const ElTimeSelectStub = defineComponent({
  name: 'ElTimeSelect',
  props: { modelValue: String, disabled: Boolean },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () =>
      h('input', {
        value: props.modelValue ?? '',
        type: 'time',
        disabled: props.disabled,
        onInput: (event) => emit('update:modelValue', event.target.value),
      })
  },
})

const ElTagStub = defineComponent({
  name: 'ElTag',
  props: { type: String },
  setup(_props, { slots }) {
    return () => h('span', slots.default?.())
  },
})

const globalStubs = {
  ElForm: ElFormStub,
  ElFormItem: ElFormItemStub,
  ElButton: ElButtonStub,
  ElInput: ElInputStub,
  ElInputNumber: ElInputNumberStub,
  ElSwitch: ElSwitchStub,
  ElRadioGroup: ElRadioGroupStub,
  ElRadioButton: ElRadioButtonStub,
  ElTimeSelect: ElTimeSelectStub,
  ElTag: ElTagStub,
}

function mountSection(component, props) {
  return mount(component, { props, global: { stubs: globalStubs } })
}

describe('SettingsDatabaseSection', () => {
  it('emits export and forwards the selected file after resetting the input', async () => {
    const wrapper = mountSection(SettingsDatabaseSection, { exporting: true })
    const buttons = wrapper.findAllComponents(ElButtonStub)

    await buttons[0].trigger('click')
    expect(wrapper.emitted('export')).toHaveLength(1)
    expect(buttons[0].attributes('data-loading')).toBe('true')

    let clicked = false
    const fileInput = wrapper.get('input[type="file"]')
    fileInput.element.click = () => {
      clicked = true
    }
    await buttons[1].trigger('click')
    expect(clicked).toBe(true)

    const file = new File(['sqlite'], 'backup.db', { type: 'application/octet-stream' })
    Object.defineProperty(fileInput.element, 'files', { configurable: true, value: [file] })
    await fileInput.trigger('change')
    expect(wrapper.emitted('import-file')).toEqual([[file]])
    expect(fileInput.element.value).toBe('')
  })
})

describe('SettingsGeneralSection', () => {
  it('renders protection status and emits field updates and save', async () => {
    const wrapper = mountSection(SettingsGeneralSection, {
      form: {
        max_log_entries: 1000,
        max_retention_days: 30,
        access_protection_enabled: true,
        access_key: '',
      },
      accessKeyConfigured: true,
      updatedAt: '2026-09-19 20:00',
      saving: true,
    })

    expect(wrapper.text()).toContain('已启用保护')
    expect(wrapper.text()).toContain('已设置访问密钥')
    expect(wrapper.text()).toContain('2026-09-19 20:00')

    const numbers = wrapper.findAllComponents(ElInputNumberStub)
    await numbers[0].vm.$emit('update:modelValue', 1200)
    await numbers[1].vm.$emit('update:modelValue', 45)
    await wrapper.findComponent(ElSwitchStub).vm.$emit('update:modelValue', false)
    await wrapper.findComponent(ElInputStub).vm.$emit('update:modelValue', 'new-secret')
    expect(wrapper.emitted('update-field')).toEqual([
      ['max_log_entries', 1200],
      ['max_retention_days', 45],
      ['access_protection_enabled', false],
      ['access_key', 'new-secret'],
    ])

    const saveButton = wrapper.findAllComponents(ElButtonStub)[0]
    expect(saveButton.attributes('data-loading')).toBe('true')
    await saveButton.trigger('click')
    expect(wrapper.emitted('save')).toHaveLength(1)
  })
})

describe('SettingsQinglongSection', () => {
  it('renders auto-sync details and emits configuration and action events', async () => {
    const wrapper = mountSection(SettingsQinglongSection, {
      form: {
        ql_base_url: 'http://qinglong:5700',
        ql_client_id: 'client-id',
        ql_client_secret: '',
        ql_sync_mode: 'auto',
        ql_auto_sync_minutes: 5,
      },
      secretConfigured: true,
      lastSyncAt: '2026-09-19 19:55',
      lastSyncStatus: '同步成功',
      syncing: true,
    })

    expect(wrapper.text()).toContain('已配置')
    expect(wrapper.text()).toContain('后台按间隔刷新')
    expect(wrapper.text()).toContain('同步间隔')
    expect(wrapper.text()).toContain('2026-09-19 19:55')
    expect(wrapper.text()).toContain('同步成功')

    const inputs = wrapper.findAllComponents(ElInputStub)
    await inputs[0].vm.$emit('update:modelValue', 'http://new:5700')
    await inputs[1].vm.$emit('update:modelValue', 'new-client')
    await inputs[2].vm.$emit('update:modelValue', 'new-secret')
    await wrapper.findComponent(ElRadioGroupStub).vm.$emit('update:modelValue', 'blocking')
    await wrapper.findComponent(ElInputNumberStub).vm.$emit('update:modelValue', 10)
    expect(wrapper.emitted('update-field')).toEqual([
      ['ql_base_url', 'http://new:5700'],
      ['ql_client_id', 'new-client'],
      ['ql_client_secret', 'new-secret'],
      ['ql_sync_mode', 'blocking'],
      ['ql_auto_sync_minutes', 10],
    ])

    const buttons = wrapper.findAllComponents(ElButtonStub)
    await buttons[0].trigger('click')
    await buttons[1].trigger('click')
    expect(wrapper.emitted('save')).toHaveLength(1)
    expect(wrapper.emitted('sync')).toHaveLength(1)
    expect(buttons[1].attributes('data-loading')).toBe('true')
  })

  it('hides the interval control and explains manual mode', () => {
    const wrapper = mountSection(SettingsQinglongSection, {
      form: { ql_sync_mode: 'manual' },
    })

    expect(wrapper.text()).toContain('不自动刷新')
    expect(wrapper.text()).not.toContain('同步间隔')
    expect(wrapper.findComponent(ElInputNumberStub).exists()).toBe(false)
  })
})

describe('SettingsBarkSection', () => {
  it('renders push status and emits fields, save and test actions', async () => {
    const wrapper = mountSection(SettingsBarkSection, {
      form: {
        bark_enabled: true,
        bark_server: 'https://api.day.app',
        bark_device_key: '',
        bark_push_time: '09:00',
      },
      keyConfigured: false,
      lastPushAt: '2026-09-19 09:00',
      lastPushStatus: '测试成功',
      testing: true,
    })

    expect(wrapper.text()).toContain('未配置')
    expect(wrapper.text()).toContain('2026-09-19 09:00')
    expect(wrapper.text()).toContain('测试成功')

    await wrapper.findComponent(ElSwitchStub).vm.$emit('update:modelValue', false)
    const inputs = wrapper.findAllComponents(ElInputStub)
    await inputs[0].vm.$emit('update:modelValue', 'https://bark.example')
    await inputs[1].vm.$emit('update:modelValue', 'device-key')
    await wrapper.findComponent(ElTimeSelectStub).vm.$emit('update:modelValue', '10:05')
    expect(wrapper.emitted('update-field')).toEqual([
      ['bark_enabled', false],
      ['bark_server', 'https://bark.example'],
      ['bark_device_key', 'device-key'],
      ['bark_push_time', '10:05'],
    ])

    const buttons = wrapper.findAllComponents(ElButtonStub)
    await buttons[0].trigger('click')
    await buttons[1].trigger('click')
    expect(wrapper.emitted('save')).toHaveLength(1)
    expect(wrapper.emitted('test')).toHaveLength(1)
    expect(buttons[1].attributes('data-loading')).toBe('true')
  })
})
