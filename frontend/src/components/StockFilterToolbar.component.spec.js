/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import StockFilterToolbar from './StockFilterToolbar.vue'

const ElementInputStub = defineComponent({
  props: { modelValue: { type: String, default: '' } },
  emits: ['update:modelValue', 'clear', 'keyup'],
  setup(props, { attrs, emit, slots }) {
    return () =>
      h('div', { class: 'input-stub' }, [
        h('input', {
          ...attrs,
          value: props.modelValue,
          onInput: (event) => emit('update:modelValue', event.target.value),
          onKeyup: (event) => emit('keyup', event),
        }),
        slots.append?.(),
      ])
  },
})

const ElementButtonStub = defineComponent({
  inheritAttrs: false,
  setup(_, { attrs, slots }) {
    return () => h('button', attrs, slots.default?.())
  },
})

const passthroughStub = defineComponent({
  inheritAttrs: false,
  setup(_, { attrs, slots }) {
    return () => h('span', attrs, slots.default?.())
  },
})

const summary = {
  totalProducts: 120,
  inStockProducts: 90,
  outOfStockProducts: 30,
  redeemableProducts: 48,
  pointsOnlyProducts: 80,
  mixedProducts: 40,
}

function mountToolbar(props = {}) {
  return mount(StockFilterToolbar, {
    props: {
      keywordInput: '',
      cashCapInput: '',
      cashCapValue: null,
      hiddenTotal: 4,
      offShelfTotal: 6,
      availableTags: ['热门', '食品'],
      currentTag: '热门',
      priceMode: 'points_plus_cash',
      priceModeLabel: '积分加钱购',
      activeStatus: 'all',
      searchKeyword: '帽子',
      loadedFromCache: true,
      totalResults: 120,
      visibleCount: 20,
      pageSize: 20,
      cashCapPresets: [1, 9.9],
      summary,
      isCashCapPresetActive: (value) => value === 1,
      ...props,
    },
    global: {
      stubs: {
        ElButton: ElementButtonStub,
        ElInput: ElementInputStub,
        ElTag: passthroughStub,
      },
    },
  })
}

describe('StockFilterToolbar', () => {
  it('renders search, tag, price, status and result summary boundaries', () => {
    const wrapper = mountToolbar()

    expect(wrapper.text()).toContain('已隐藏 4')
    expect(wrapper.text()).toContain('已下架 6')
    expect(wrapper.text()).toContain('全部商品 120')
    expect(wrapper.text()).toContain('积分加钱购 40')
    expect(wrapper.text()).toContain('当前结果 120')
    expect(wrapper.text()).toContain('关键词：帽子')
    expect(wrapper.text()).toContain('缓存命中')
    expect(wrapper.find('.stock-cash-cap-chip.active').text()).toContain('¥1')
  })

  it('forwards actions and controlled input updates to the page boundary', async () => {
    const wrapper = mountToolbar()

    await wrapper.find('.input-stub input').setValue('背包')
    expect(wrapper.emitted('update:keywordInput')).toEqual([['背包']])

    const tag = wrapper.findAll('.stock-tag-chip').find((item) => item.text() === '食品')
    await tag.trigger('click')
    await wrapper.find('.stock-price-mode-list .stock-tag-chip').trigger('click')
    await wrapper.find('.stock-cash-cap-chip').trigger('click')
    await wrapper.find('.stock-summary-item.success').trigger('click')
    await wrapper.find('.stock-search-bar button').trigger('click')

    expect(wrapper.emitted('select-tag')).toEqual([['食品']])
    expect(wrapper.emitted('select-price-mode')).toEqual([['all']])
    expect(wrapper.emitted('apply-cash-cap-preset')).toEqual([[1]])
    expect(wrapper.emitted('apply-metric-filter')).toEqual([['in_stock']])
    expect(wrapper.emitted('apply-search')).toEqual([[]])
  })

  it('clears the cash cap and exposes drawer, refresh and custom-cap actions', async () => {
    const wrapper = mountToolbar()

    await wrapper.find('.stock-cash-cap-chip:last-of-type').trigger('click')
    await wrapper.find('.stock-cash-cap-input input').setValue('3.5')
    await wrapper.find('.stock-cash-cap-custom button').trigger('click')
    const searchBarButtons = wrapper.findAll('.stock-search-bar button')
    await searchBarButtons.find((button) => button.text().includes('已隐藏')).trigger('click')
    await searchBarButtons.find((button) => button.text().includes('已下架')).trigger('click')
    await searchBarButtons.find((button) => button.text().includes('刷新数据')).trigger('click')

    expect(wrapper.emitted('clear-cash-cap')).toEqual([[]])
    expect(wrapper.emitted('update:cashCapInput')).toEqual([['3.5']])
    expect(wrapper.emitted('apply-cash-cap')).toEqual([[]])
    expect(wrapper.emitted('open-hidden')).toEqual([[]])
    expect(wrapper.emitted('open-off-shelf')).toEqual([[]])
    expect(wrapper.emitted('refresh')).toEqual([[]])
  })
})
