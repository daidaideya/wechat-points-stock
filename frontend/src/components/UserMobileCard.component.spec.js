/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UserMobileCard from './UserMobileCard.vue'

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
          class: 'button-stub',
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
    return () => h('span', attrs, slots.default?.())
  },
})

const user = {
  wechat_id: 'wx-alice',
  nickname: 'Alice',
  phone: '13800138000',
  device: 'iPhone',
  active_program_count: 2,
  active_app_count: 1,
}

function mountCard(props = {}) {
  return mount(UserMobileCard, {
    props: { item: user, index: 3, ...props },
    global: {
      stubs: {
        ElButton: ElementButtonStub,
        ElIcon: passthroughStub,
      },
    },
  })
}

describe('UserMobileCard', () => {
  it('renders identity, counts, contact metadata and sort position', () => {
    const wrapper = mountCard()

    expect(wrapper.get('.users-mobile-card').attributes('data-wechat-id')).toBe('wx-alice')
    expect(wrapper.get('.users-sort-index-inline').text()).toBe('4.')
    expect(wrapper.get('.users-mobile-title').text()).toContain('Alice')
    expect(wrapper.get('.users-mobile-subtitle').text()).toBe('手机 13800138000')
    expect(wrapper.text()).toContain('小程序 2')
    expect(wrapper.text()).toContain('APP 1')
    expect(wrapper.text()).toContain('iPhone')
    expect(wrapper.text()).toContain('13800138000')
    expect(wrapper.text()).toContain('wx-alice')
  })

  it('falls back to a phone identity and hides phone-shaped WeChat ids', () => {
    const wrapper = mountCard({
      item: {
        wechat_id: '13900139000',
        nickname: '',
        phone: '',
        device: '',
      },
      index: 0,
    })

    expect(wrapper.get('.users-mobile-title').text()).toContain('13900139000')
    expect(wrapper.get('.users-mobile-subtitle').text()).toBe('手机 13900139000')
    expect(wrapper.text()).toContain('设备未填写')
    expect(wrapper.text()).toContain('手机号13900139000')
    expect(wrapper.text()).toContain('小程序 0')
    expect(wrapper.text()).toContain('APP 0')
    expect(wrapper.get('.users-mobile-meta-grid').text()).not.toContain('微信号')
  })

  it('forwards edit, points and remove actions and marks the deleting row busy', async () => {
    const wrapper = mountCard({ deletingWechatId: user.wechat_id })
    const buttons = wrapper.findAll('.button-stub')

    expect(buttons).toHaveLength(3)
    expect(buttons[2].attributes('aria-busy')).toBe('true')

    await buttons[0].trigger('click')
    await buttons[1].trigger('click')
    await buttons[2].trigger('click')

    expect(wrapper.emitted('edit')?.[0]?.[0]).toEqual(user)
    expect(wrapper.emitted('view-points')?.[0]?.[0]).toEqual(user)
    expect(wrapper.emitted('remove')).toEqual([[user]])
  })
})
