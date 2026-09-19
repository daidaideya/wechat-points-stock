import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ProgramDetailOverview from './ProgramDetailOverview.vue'

const ElementButtonStub = defineComponent({
  emits: ['click'],
  setup(_, { attrs, emit, slots }) {
    return () => h('button', { ...attrs, onClick: (event) => emit('click', event) }, slots.default?.())
  },
})

const detail = {
  program_id: 'demo-program',
  program_name: '示例小程序',
  is_favorite: true,
  tags: ['积分', '热门'],
  note: '详情备注',
  last_update_time: '2026-09-19T10:20:00+08:00',
}

function mountOverview(props = {}) {
  return mount(ProgramDetailOverview, {
    props: {
      programId: 'demo-program',
      detail,
      stock: { max_user_points: 999 },
      formatDate: (value) => `格式化:${value}`,
      ...props,
    },
    global: {
      stubs: {
        ElButton: ElementButtonStub,
      },
    },
  })
}

describe('ProgramDetailOverview', () => {
  it('renders the identity, summary, tags and note', () => {
    const wrapper = mountOverview()

    expect(wrapper.get('.detail-title').text()).toBe('示例小程序')
    expect(wrapper.get('.id-chip').text()).toBe('demo-program')
    expect(wrapper.get('.favorite-chip').text()).toBe('已收藏')
    expect(wrapper.get('.update-chip').text()).toContain('格式化:2026-09-19T10:20:00+08:00')
    expect(wrapper.get('.emphasis-value').text()).toBe('999')
    expect(wrapper.get('.info-tag-row').text()).toContain('积分')
    expect(wrapper.get('.info-note').text()).toBe('详情备注')
  })

  it('forwards refresh and back actions and renders empty fallbacks', async () => {
    const wrapper = mountOverview({ detail: null, stock: null })

    expect(wrapper.get('.detail-title').text()).toBe('demo-program')
    expect(wrapper.get('.info-tag.empty').text()).toBe('未设置标签')
    expect(wrapper.get('.info-note').text()).toBe('暂无备注信息')

    await wrapper.get('.hero-action-button').trigger('click')
    await wrapper.get('.hero-primary-button').trigger('click')

    expect(wrapper.emitted('refresh')).toHaveLength(1)
    expect(wrapper.emitted('back')).toHaveLength(1)
  })
})
