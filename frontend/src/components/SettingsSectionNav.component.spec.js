import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import SettingsSectionNav from './SettingsSectionNav.vue'

const items = [
  { key: 'general', label: '基础设置', desc: '日志清理 / 访问保护', icon: '⚙️' },
  { key: 'bark', label: 'Bark 推送', desc: '未报小程序提醒', icon: '🔔' },
]

function mountNav(props = {}) {
  return mount(SettingsSectionNav, {
    props: { items, modelValue: 'general', ...props },
  })
}

describe('SettingsSectionNav', () => {
  it('exposes the active section through navigation semantics', () => {
    const wrapper = mountNav()

    expect(wrapper.get('nav').attributes('aria-label')).toBe('设置导航')
    expect(wrapper.get('button[aria-current="page"]').text()).toContain('基础设置')
    expect(wrapper.findAll('button')[1].attributes('aria-current')).toBeUndefined()
  })

  it('emits the selected section and respects the disabled boundary', async () => {
    const wrapper = mountNav()

    await wrapper.findAll('button')[1].trigger('click')
    expect(wrapper.emitted('update:modelValue')).toEqual([['bark']])

    const disabledWrapper = mountNav({ disabled: true })
    await disabledWrapper.findAll('button')[1].trigger('click')
    expect(disabledWrapper.emitted('update:modelValue')).toBeUndefined()
  })
})
