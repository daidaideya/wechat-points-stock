/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ProgramStockDialog from './ProgramStockDialog.vue'

const ElementDialogStub = defineComponent({
  name: 'ElDialog',
  props: { modelValue: Boolean, title: { type: String, default: '' } },
  emits: ['update:modelValue'],
  setup(props, { emit, slots }) {
    return () =>
      h('section', { class: 'dialog-stub', 'aria-label': props.title }, [
        h('h2', { class: 'dialog-stub-title' }, props.title),
        h('div', { class: 'dialog-stub-body' }, slots.default?.()),
        h('button', { class: 'dialog-stub-update', onClick: () => emit('update:modelValue', false) }, '模拟关闭'),
      ])
  },
})

const passthroughStub = defineComponent({
  inheritAttrs: false,
  setup(_, { attrs, slots }) {
    return () => h('span', attrs, slots.default?.())
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

const stockData = {
  program_name: '示例小程序',
  product_count: 2,
  max_user_points: 1000,
  max_user_cash: 12.5,
  stock_change: { added_count: 1, removed_count: 1 },
  changed_products: [
    { change_type: 'added', product_id: 'new-product', product_name: '新增商品', points: 100, stock: 3 },
    { change_type: 'removed', product_id: 'old-product', product_name: '下架商品', points: 200, stock: 0 },
  ],
}

const sortedStockProducts = [
  { product_id: 'new-product', product_name: '新增商品', points: 100, stock: 3 },
  { product_id: 'old-product', product_name: '下架商品', points: 200, stock: 0 },
]

function mountDialog(props = {}) {
  return mount(ProgramStockDialog, {
    props: {
      modelValue: true,
      stockData,
      redeemableProductCount: 1,
      stockMaxUserPoints: 1000,
      stockMaxUserCash: 12.5,
      sortedStockProducts,
      formatMoney: (value) => `金额:${value}`,
      formatProductPrice: (product) => `价格:${product.product_name}`,
      isProductRedeemable: (product) => product.product_id === 'new-product',
      getRedeemBlockedLabel: () => '积分不足',
      formatPointsGap: (product) => `差额:${product.points}`,
      stockRowClassName: () => 'stock-row-test',
      ...props,
    },
    global: {
      stubs: {
        ElDialog: ElementDialogStub,
        ElEmpty: passthroughStub,
        ElImage: passthroughStub,
        ElSkeleton: ElementSkeletonStub,
        ElTable: passthroughStub,
        ElTableColumn: ElementTableColumnStub,
        ElTag: passthroughStub,
      },
    },
  })
}

describe('ProgramStockDialog', () => {
  it('renders stock summaries, snapshot badges and changed products', () => {
    const wrapper = mountDialog()

    expect(wrapper.get('.dialog-stub-title').text()).toBe('示例小程序 - 库存详情')
    expect(wrapper.text()).toContain('商品 2')
    expect(wrapper.text()).toContain('最高积分 1000')
    expect(wrapper.text()).toContain('最高现金 ¥金额:12.5')
    expect(wrapper.text()).toContain('可兑换 1')
    expect(wrapper.text()).toContain('+1')
    expect(wrapper.text()).toContain('-1')
    expect(wrapper.get('.stock-summary-grid').text()).toContain('当前最高用户现金')
    expect(wrapper.get('.stock-summary-grid').text()).toContain('¥金额:12.5')
    expect(wrapper.get('.stock-change-list').text()).toContain('新增商品')
    expect(wrapper.get('.stock-change-list').text()).toContain('下架商品')
  })

  it('maps the change disclosure and dialog model events', async () => {
    const wrapper = mountDialog()

    expect(wrapper.get('.stock-change-toggle').attributes('aria-expanded')).toBe('false')
    expect(wrapper.get('.stock-change-list').attributes('aria-hidden')).toBe('true')

    await wrapper.get('.stock-change-toggle').trigger('click')
    expect(wrapper.emitted('update:change-expanded')).toEqual([[true]])

    await wrapper.setProps({ changeExpanded: true })
    expect(wrapper.get('.stock-change-toggle').attributes('aria-expanded')).toBe('true')
    expect(wrapper.get('.stock-change-list').attributes('aria-hidden')).toBe('false')
    expect(wrapper.get('.stock-change-list').exists()).toBe(true)

    await wrapper.get('.dialog-stub-update').trigger('click')
    expect(wrapper.emitted('update:modelValue')).toEqual([[false]])
  })

  it('exposes loading status without rendering stale stock content', () => {
    const wrapper = mountDialog({ loading: true })

    const loading = wrapper.get('.stock-loading')
    expect(loading.attributes('role')).toBe('status')
    expect(loading.attributes('aria-live')).toBe('polite')
    expect(loading.attributes('aria-busy')).toBe('true')
    expect(wrapper.find('.stock-summary-grid').exists()).toBe(false)
    expect(wrapper.find('.stock-change-panel').exists()).toBe(false)
  })
})
