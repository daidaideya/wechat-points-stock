/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ProgramDetailDialog from './ProgramDetailDialog.vue'

const ElementDialogStub = defineComponent({
  name: 'ElDialog',
  props: {
    modelValue: Boolean,
    title: { type: String, default: '' },
  },
  emits: ['update:modelValue'],
  setup(props, { emit, slots }) {
    return () =>
      h('section', { class: 'dialog-stub', 'aria-label': props.title }, [
        h('h2', { class: 'dialog-stub-title' }, props.title),
        h('div', { class: 'dialog-stub-body' }, slots.default?.()),
        h('footer', { class: 'dialog-stub-footer' }, slots.footer?.()),
        h('button', { class: 'dialog-stub-update', onClick: () => emit('update:modelValue', false) }, '模拟关闭'),
      ])
  },
})

const ElementButtonStub = defineComponent({
  props: { disabled: Boolean },
  emits: ['click'],
  setup(props, { attrs, emit, slots }) {
    return () =>
      h('button', { ...attrs, disabled: props.disabled, onClick: (event) => emit('click', event) }, slots.default?.())
  },
})

const ElementEmptyStub = defineComponent({
  props: { description: { type: String, default: '' } },
  setup(props) {
    return () => h('div', { class: 'empty-stub' }, props.description)
  },
})

const ElementSkeletonStub = defineComponent({
  setup() {
    return () => h('div', { class: 'skeleton-stub' }, '加载中')
  },
})

const ElementTableColumnStub = defineComponent({
  setup() {
    return () => null
  },
})

const passthroughStub = defineComponent({
  inheritAttrs: false,
  setup(_, { attrs, slots }) {
    return () => h('div', attrs, slots.default?.())
  },
})

const detailData = {
  program_id: 'demo-program',
  program_name: '示例小程序',
  is_favorite: true,
  max_user_points: 999,
  tags: ['积分', '热门'],
  note: '详情备注',
  has_stock: true,
  last_update_time: '2026-09-19T10:20:00+08:00',
  ranking: [
    { nickname: '低分用户', wechat_id: 'wx-low', points: 10, cash: 1 },
    { nickname: '高分用户', wechat_id: 'wx-high', points: 100, cash: 2 },
  ],
}

function mountDialog(props = {}) {
  return mount(ProgramDetailDialog, {
    props: {
      modelValue: true,
      detailData,
      formatDate: (value) => `格式化:${value}`,
      ...props,
    },
    global: {
      stubs: {
        ElButton: ElementButtonStub,
        ElDialog: ElementDialogStub,
        ElEmpty: ElementEmptyStub,
        ElSkeleton: ElementSkeletonStub,
        ElTable: passthroughStub,
        ElTableColumn: ElementTableColumnStub,
      },
    },
  })
}

describe('ProgramDetailDialog', () => {
  it('renders the detail summary, tags, note and ranking count', () => {
    const wrapper = mountDialog()

    expect(wrapper.get('.dialog-stub-title').text()).toBe('示例小程序 - 详情')
    expect(wrapper.text()).toContain('已收藏')
    expect(wrapper.text()).toContain('最高积分 999')
    expect(wrapper.text()).toContain('排行 2')
    expect(wrapper.get('.detail-id-value').text()).toBe('demo-program')
    expect(wrapper.get('.detail-update-value').text()).toContain('格式化:2026-09-19T10:20:00+08:00')
    expect(wrapper.get('.detail-tag-row').text()).toContain('积分')
    expect(wrapper.get('.detail-note-text').text()).toBe('详情备注')
  })

  it('shows loading semantics and handles close/model update events', async () => {
    const wrapper = mountDialog({ loading: true })

    const loading = wrapper.get('.stock-loading')
    expect(loading.attributes('role')).toBe('status')
    expect(loading.attributes('aria-live')).toBe('polite')
    expect(loading.attributes('aria-busy')).toBe('true')
    expect(wrapper.find('.stock-summary-grid').exists()).toBe(false)

    await wrapper.get('.dialog-stub-update').trigger('click')
    expect(wrapper.emitted('update:modelValue')).toEqual([[false]])
  })

  it('closes before forwarding stock navigation and hides it when stock is unavailable', async () => {
    const wrapper = mountDialog()

    await wrapper.get('button[type="primary"]').trigger('click')
    expect(wrapper.emitted('update:modelValue')).toEqual([[false]])
    expect(wrapper.emitted('open-stock')).toEqual([[detailData]])

    const noStockWrapper = mountDialog({ detailData: { ...detailData, has_stock: false, ranking: [] } })
    expect(noStockWrapper.find('button[type="primary"]').exists()).toBe(false)
    expect(noStockWrapper.get('.empty-stub').text()).toBe('暂无积分排行数据')
  })
})
