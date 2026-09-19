/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ProgramStockTable from './ProgramStockTable.vue'

const ElementTableStub = defineComponent({
  name: 'ElTable',
  props: {
    data: { type: Array, default: () => [] },
    rowClassName: { type: Function, default: undefined },
  },
  setup(props, { slots }) {
    return () =>
      h('div', { class: 'table-stub' }, [
        h('span', { class: 'table-row-count' }, String(props.data.length)),
        slots.default?.(),
      ])
  },
})

const passthroughStub = defineComponent({
  inheritAttrs: false,
  setup(_, { attrs, slots }) {
    return () => h('span', attrs, slots.default?.())
  },
})

const ElementTableColumnStub = defineComponent({
  setup() {
    return () => null
  },
})

const products = [{ product_id: 'product-1', product_name: '示例商品', points: 100, stock: 2 }]

function mountTable(props = {}) {
  return mount(ProgramStockTable, {
    props: {
      sortedStockProducts: products,
      stockMaxUserPoints: 1000,
      stockMaxUserCash: 12.5,
      formatMoney: (value) => `金额:${value}`,
      formatProductPrice: (product) => `价格:${product.product_name}`,
      isProductRedeemable: () => true,
      getRedeemBlockedLabel: () => '积分不足',
      formatPointsGap: (product) => `差额:${product.points}`,
      stockRowClassName: () => 'stock-row-test',
      ...props,
    },
    global: {
      stubs: {
        ElImage: passthroughStub,
        ElTable: ElementTableStub,
        ElTableColumn: ElementTableColumnStub,
        ElTag: passthroughStub,
      },
    },
  })
}

describe('ProgramStockTable', () => {
  it('passes the sorted products and row-class callback to the table', () => {
    const wrapper = mountTable()
    const table = wrapper.findComponent(ElementTableStub)

    expect(wrapper.get('.stock-section-hint').text()).toContain('最高积分 1000 / 现金 ¥金额:12.5')
    expect(table.props('data')).toEqual(products)
    expect(table.props('rowClassName')).toEqual(expect.any(Function))
    expect(wrapper.get('.table-row-count').text()).toBe('1')
  })

  it('keeps the table shell available when there are no products', () => {
    const wrapper = mountTable({ sortedStockProducts: [] })

    expect(wrapper.get('.stock-table-panel').exists()).toBe(true)
    expect(wrapper.findComponent(ElementTableStub).props('data')).toEqual([])
  })
})
