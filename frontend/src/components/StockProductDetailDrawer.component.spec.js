/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import StockProductDetailDrawer from './StockProductDetailDrawer.vue'

const ElementDrawerStub = defineComponent({
  props: {
    modelValue: Boolean,
    title: { type: String, default: '' },
  },
  emits: ['update:modelValue'],
  setup(props, { attrs, emit, slots }) {
    return () =>
      h('section', { class: ['drawer-stub', attrs.class], 'data-title': props.title }, [
        props.modelValue ? h('div', { class: 'drawer-stub-body' }, slots.default?.()) : null,
        props.modelValue
          ? h('button', { class: 'drawer-stub-close', onClick: () => emit('update:modelValue', false) }, '关闭')
          : null,
      ])
  },
})

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
  props: { type: { type: String, default: '' } },
  setup(props, { slots }) {
    return () => h('span', { class: 'tag-stub', 'data-type': props.type }, slots.default?.())
  },
})

const product = {
  product_id: 'gift-7',
  product_name: '咖啡券',
  program_id: 'demo-program',
  program_name: '示例小程序',
  image_url: 'https://example.test/coffee.png',
  statusTagType: 'success',
  statusLabel: '有库存',
  redeemable: true,
  stock: 8,
  maxUserPoints: 999,
  maxUserCash: 3.5,
}

function mountDrawer(props = {}) {
  return mount(StockProductDetailDrawer, {
    props: {
      modelValue: true,
      product,
      formatProductPrice: () => '120 积分 + ¥3.5',
      formatCashAmount: (value) => `¥${value}`,
      ...props,
    },
    global: {
      stubs: {
        ElDrawer: ElementDrawerStub,
        ElImage: ElementImageStub,
        ElTag: ElementTagStub,
      },
    },
  })
}

describe('StockProductDetailDrawer', () => {
  it('renders product identity, statuses, image and stock metrics', () => {
    const wrapper = mountDrawer()

    expect(wrapper.get('.drawer-stub').attributes('data-title')).toBe('咖啡券')
    expect(wrapper.get('.image-stub').attributes('src')).toBe('https://example.test/coffee.png')
    expect(wrapper.get('.image-stub').attributes('data-preview')).toBe('https://example.test/coffee.png')
    expect(wrapper.text()).toContain('咖啡券')
    expect(wrapper.text()).toContain('示例小程序')
    expect(wrapper.text()).toContain('可兑换')
    expect(wrapper.text()).toContain('120 积分 + ¥3.5')
    expect(wrapper.text()).toContain('当前库存8')
    expect(wrapper.text()).toContain('最高积分999')
    expect(wrapper.text()).toContain('最高现金¥3.5')
  })

  it('renders an empty-image state and forwards drawer visibility updates', async () => {
    const wrapper = mountDrawer({
      product: {
        product_id: 'fallback-product',
        program_id: 'fallback-program',
        statusLabel: '无库存',
        statusTagType: 'danger',
        redeemable: false,
        stock: 0,
        maxUserPoints: 0,
        maxUserCash: null,
      },
    })

    expect(wrapper.get('.stock-detail-image-empty').text()).toBe('暂无图片')
    expect(wrapper.text()).toContain('fallback-product')
    expect(wrapper.text()).toContain('不可兑换')

    await wrapper.get('.drawer-stub-close').trigger('click')
    expect(wrapper.emitted('update:modelValue')).toEqual([[false]])
  })

  it('does not render product details while closed', () => {
    const wrapper = mountDrawer({ modelValue: false })

    expect(wrapper.find('.stock-detail-stack').exists()).toBe(false)
  })
})
