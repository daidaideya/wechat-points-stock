/* eslint-disable vue/one-component-per-file -- test-only child stubs stay co-located. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UsersListSection from './UsersListSection.vue'

const UserMobileCardStub = defineComponent({
  name: 'UserMobileCard',
  props: { item: Object, index: Number },
  emits: ['edit', 'view-points', 'remove'],
  setup(props, { emit }) {
    return () =>
      h('article', { class: 'mobile-card-stub' }, [
        h('span', props.item?.nickname || `user-${props.index}`),
        h('button', { class: 'mobile-edit', onClick: () => emit('edit', props.item) }, '编辑'),
        h('button', { class: 'mobile-points', onClick: () => emit('view-points', props.item) }, '积分'),
        h('button', { class: 'mobile-remove', onClick: () => emit('remove', props.item) }, '删除'),
      ])
  },
})

const UserDesktopTableStub = defineComponent({
  name: 'UserDesktopTable',
  props: { items: Array },
  emits: ['edit', 'view-points', 'remove'],
  setup(props, { emit, expose }) {
    const tableElement = document.createElement('div')
    expose({ $el: tableElement })
    return () =>
      h('div', { class: 'desktop-table-stub' }, [
        h('span', props.items?.[0]?.nickname || '桌面用户'),
        h('button', { class: 'desktop-edit', onClick: () => emit('edit', props.items?.[0]) }, '编辑'),
        h('button', { class: 'desktop-points', onClick: () => emit('view-points', props.items?.[0]) }, '积分'),
        h('button', { class: 'desktop-remove', onClick: () => emit('remove', props.items?.[0]) }, '删除'),
      ])
  },
})

const ElSkeletonStub = defineComponent({
  name: 'ElSkeleton',
  setup() {
    return () => h('div', { class: 'skeleton-stub' }, 'loading')
  },
})

const ElEmptyStub = defineComponent({
  name: 'ElEmpty',
  props: { description: String },
  setup(props) {
    return () => h('div', { class: 'empty-stub' }, props.description)
  },
})

const user = { wechat_id: 'wx-1', nickname: '示例用户' }

function mountSection(props = {}) {
  return mount(UsersListSection, {
    props: { items: [user], ...props },
    global: {
      stubs: {
        UserMobileCard: UserMobileCardStub,
        UserDesktopTable: UserDesktopTableStub,
        ElSkeleton: ElSkeletonStub,
        ElEmpty: ElEmptyStub,
      },
    },
  })
}

describe('UsersListSection', () => {
  it('renders list guidance, mobile cards and desktop table', () => {
    const wrapper = mountSection({ sorting: true })

    expect(wrapper.text()).toContain('用户列表')
    expect(wrapper.text()).toContain('正在保存顺序')
    expect(wrapper.get('.users-mobile-list')).toBeTruthy()
    expect(wrapper.get('.users-desktop-table-wrap')).toBeTruthy()
    expect(wrapper.text()).toContain('示例用户')
  })

  it('forwards user actions from both presentation modes', async () => {
    const wrapper = mountSection()

    await wrapper.get('.mobile-edit').trigger('click')
    await wrapper.get('.mobile-points').trigger('click')
    await wrapper.get('.mobile-remove').trigger('click')
    await wrapper.get('.desktop-edit').trigger('click')

    expect(wrapper.emitted('edit')).toHaveLength(2)
    expect(wrapper.emitted('view-points')).toHaveLength(1)
    expect(wrapper.emitted('remove')).toHaveLength(1)
    expect(wrapper.emitted('edit')[0]).toEqual([user])
  })

  it('keeps loading and empty states explicit', () => {
    const loadingWrapper = mountSection({ loading: true })
    expect(loadingWrapper.get('.skeleton-stub').text()).toBe('loading')

    const emptyWrapper = mountSection({ items: [] })
    expect(emptyWrapper.get('.empty-stub').text()).toBe('暂无用户数据')
  })
})
