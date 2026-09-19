import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import SettingsSectionCard from './SettingsSectionCard.vue'

describe('SettingsSectionCard', () => {
  it('renders the shared heading structure and projected section content', () => {
    const wrapper = mount(SettingsSectionCard, {
      props: {
        title: '基础设置',
        description: '日志清理策略与访问保护。',
      },
      slots: {
        default: '<p data-test="content">设置表单</p>',
      },
    })

    expect(wrapper.get('section').classes()).toContain('settings-section-card')
    expect(wrapper.get('h3').text()).toBe('基础设置')
    expect(wrapper.get('.settings-section-desc').text()).toBe('日志清理策略与访问保护。')
    expect(wrapper.get('[data-test="content"]').text()).toBe('设置表单')
  })
})
