/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import StockProductCard from './StockProductCard.vue'

const ElementImageStub = defineComponent({
  props: {
    src: { type: String, default: '' },
    previewSrcList: { type: Array, default: () => [] },
  },
  setup(props) {
    return () => h('img', { class: 'image-stub', src: props.src, 'data-preview': props.previewSrcList.join('|') })
  },
})

const ElementTagStub = defineComponent({
  props: {
    type: { type: String, default: '' },
  },
  setup(props, { slots }) {
    return () => h('span', { class: 'tag-stub', 'data-type': props.type }, slots.default?.())
  },
})

const ElementButtonStub = defineComponent({
  props: {
    loading: Boolean,
  },
  emits: ['click'],
  setup(props, { emit, slots }) {
    return () =>
      h(
        'button',
        {
          class: 'button-stub',
          'aria-busy': props.loading ? 'true' : 'false',
          onClick: (event) => emit('click', event),
        },
        slots.default?.(),
      )
  },
})

const product = {
  id: 7,
  product_id: 'gift-7',
  product_name: '咖啡券',
  program_id: 'demo-program',
  program_name: '示例小程序',
  image_url: 'https://example.test/coffee.png',
  image_local_path: '/uploads/coffee.png',
  statusTagType: 'success',
  statusLabel: '有库存',
  redeemable: true,
  points: 120,
  cash: 3.5,
  stock: 8,
  maxUserPoints: 999,
}

function mountCard(props = {}) {
  return mount(StockProductCard, {
    props: { item: product, ...props },
    global: {
      stubs: {
        ElButton: ElementButtonStub,
        ElImage: ElementImageStub,
        ElTag: ElementTagStub,
      },
    },
  })
}

describe('StockProductCard', () => {
  it('renders image, status, redeemability and stock metrics', () => {
    const wrapper = mountCard()

    const image = wrapper.get('.image-stub')
    expect(image.attributes('src')).toBe('https://example.test/coffee.png')
    expect(image.attributes('data-preview')).toBe('https://example.test/coffee.png')
    expect(wrapper.get('.tag-stub').attributes('data-type')).toBe('success')
    expect(wrapper.text()).toContain('有库存')
    expect(wrapper.text()).toContain('咖啡券')
    expect(wrapper.text()).toContain('示例小程序')
    expect(wrapper.text()).toContain('可兑换')
    expect(wrapper.text()).toContain('120 积分 + ¥3.5')
    expect(wrapper.text()).toContain('8')
    expect(wrapper.text()).toContain('999')
  })

  it('uses fallback labels and renders the empty-image state', () => {
    const wrapper = mountCard({
      item: {
        product_id: 'fallback-product',
        program_id: 'fallback-program',
        points: 0,
        cash: 5,
        stock: 0,
        redeemable: false,
        statusTagType: 'danger',
        statusLabel: '无库存',
        maxUserPoints: 0,
      },
    })

    expect(wrapper.find('.image-stub').exists()).toBe(false)
    expect(wrapper.get('.stock-gallery-image-empty').text()).toBe('暂无图片')
    expect(wrapper.text()).toContain('fallback-product')
    expect(wrapper.text()).toContain('fallback-program')
    expect(wrapper.text()).toContain('不可兑换')
    expect(wrapper.text()).toContain('¥5')
    expect(wrapper.get('.tag-stub').attributes('data-type')).toBe('danger')
  })

  it('forwards the product when hiding and exposes the loading boundary', async () => {
    const wrapper = mountCard({ hiding: true })

    expect(wrapper.get('.button-stub').attributes('aria-busy')).toBe('true')
    await wrapper.get('.button-stub').trigger('click')

    expect(wrapper.emitted('hide')).toEqual([[product]])
  })
})
