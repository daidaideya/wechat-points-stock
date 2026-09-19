/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ProgramDetailDataSections from './ProgramDetailDataSections.vue'

const ElementTableStub = defineComponent({
  props: {
    data: {
      type: Array,
      default: () => [],
    },
  },
  setup(props) {
    return () => h('div', { class: 'table-stub', 'data-row-count': String(props.data.length) })
  },
})

const passthroughStub = defineComponent({
  inheritAttrs: false,
  setup(_, { attrs, slots }) {
    return () => h('span', attrs, slots.default?.())
  },
})

function mountSections() {
  return mount(ProgramDetailDataSections, {
    props: {
      detail: {
        ranking: [{ nickname: '用户一', report_time: '2026-09-19T10:20:00+08:00' }],
      },
      stock: {
        max_user_points: 999,
        max_user_cash: 12.5,
        products: [{ product_name: '礼品', points: 300, cash: 9.9, stock: 2 }],
      },
      formatDate: (value) => `格式化:${value}`,
    },
    global: {
      stubs: {
        ElTable: ElementTableStub,
        ElTableColumn: passthroughStub,
        ElTag: passthroughStub,
      },
    },
  })
}

describe('ProgramDetailDataSections', () => {
  it('renders ranking and stock sections with their current data', () => {
    const wrapper = mountSections()

    expect(wrapper.findAll('.detail-section-card')).toHaveLength(2)
    expect(wrapper.text()).toContain('积分排行榜')
    expect(wrapper.text()).toContain('库存详情')
    expect(wrapper.text()).toContain('999')
    expect(wrapper.text()).toContain('¥12.5')
    expect(wrapper.findAll('.table-stub')[0].attributes('data-row-count')).toBe('1')
    expect(wrapper.findAll('.table-stub')[1].attributes('data-row-count')).toBe('1')
  })

  it('keeps empty ranking and stock data renderable', () => {
    const wrapper = mount(ProgramDetailDataSections, {
      props: {
        detail: null,
        stock: null,
        formatDate: () => '暂无',
      },
      global: {
        stubs: {
          ElTable: ElementTableStub,
          ElTableColumn: passthroughStub,
          ElTag: passthroughStub,
        },
      },
    })

    expect(wrapper.findAll('.detail-section-card')).toHaveLength(2)
    expect(wrapper.findAll('.table-stub')[0].attributes('data-row-count')).toBe('0')
    expect(wrapper.findAll('.table-stub')[1].attributes('data-row-count')).toBe('0')
    expect(wrapper.findAll('.stock-highlight-card')).toHaveLength(1)
  })
})
