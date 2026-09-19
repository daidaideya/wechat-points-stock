/* eslint-disable vue/one-component-per-file -- the test uses isolated Element Plus stubs. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import StockManagementDrawers from './StockManagementDrawers.vue'

const ElementDrawerStub = defineComponent({
  props: {
    modelValue: Boolean,
    title: { type: String, default: '' },
  },
  emits: ['update:modelValue'],
  setup(props, { emit, slots }) {
    return () =>
      h('section', { class: 'drawer-stub', 'data-title': props.title, 'data-open': String(props.modelValue) }, [
        props.modelValue ? h('div', { class: 'drawer-stub-body' }, slots.default?.()) : null,
        props.modelValue
          ? h('button', { class: 'drawer-stub-close', onClick: () => emit('update:modelValue', false) }, '关闭')
          : null,
      ])
  },
})

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

const ElementEmptyStub = defineComponent({
  props: { description: { type: String, default: '' } },
  setup(props, { slots }) {
    return () => h('div', { class: 'empty-stub' }, [props.description, slots.description?.()])
  },
})

const ElementImageStub = defineComponent({
  props: { src: { type: String, default: '' } },
  setup(props) {
    return () => h('img', { class: 'image-stub', src: props.src })
  },
})

const product = {
  id: 7,
  product_id: 'gift-7',
  product_name: '咖啡券',
  program_id: 'demo-program',
  program_name: '示例小程序',
  image_url: 'https://example.test/coffee.png',
  points: 120,
  cash: 3.5,
  stock: 8,
  hidden_at: '2026-09-19T10:20:00+08:00',
}

const group = {
  program_id: 'demo-program',
  program_name: '示例小程序',
  count: 1,
  total_count: 1,
  products: [{ ...product, unlisted_at: product.hidden_at }],
}

function mountDrawers(props = {}) {
  return mount(StockManagementDrawers, {
    props: {
      hiddenVisible: false,
      hiddenLoading: false,
      hiddenProducts: [],
      hiddenTotal: 0,
      hiddenKeywordInput: '',
      offShelfVisible: false,
      offShelfLoading: false,
      offShelfLoadingMore: false,
      offShelfPrograms: [],
      offShelfTotal: 0,
      offShelfHasMore: false,
      offShelfKeywordInput: '',
      restoringProductId: null,
      relistingId: null,
      ...props,
    },
    global: {
      stubs: {
        ElButton: ElementButtonStub,
        ElDrawer: ElementDrawerStub,
        ElEmpty: ElementEmptyStub,
        ElImage: ElementImageStub,
        ElInput: ElementInputStub,
        ElSkeleton: passthroughStub,
        ElTag: passthroughStub,
      },
    },
  })
}

describe('StockManagementDrawers', () => {
  it('renders hidden products and forwards search, restore and close actions', async () => {
    const wrapper = mountDrawers({ hiddenVisible: true, hiddenProducts: [product], hiddenTotal: 2 })
    const drawer = wrapper.get('[data-title="已隐藏商品"]')

    expect(drawer.text()).toContain('咖啡券')
    expect(drawer.text()).toContain('隐藏数 2')
    await drawer.find('.hidden-products-toolbar button').trigger('click')
    await drawer.get('.hidden-product-card button').trigger('click')
    await drawer.get('.drawer-stub-close').trigger('click')

    expect(wrapper.emitted('fetch-hidden')).toHaveLength(1)
    expect(wrapper.emitted('restore')).toEqual([[product]])
    expect(wrapper.emitted('update:hidden-visible')).toEqual([[false]])
  })

  it('renders grouped off-shelf products and forwards pagination and relist actions', async () => {
    const wrapper = mountDrawers({
      offShelfVisible: true,
      offShelfPrograms: [group],
      offShelfTotal: 2,
      offShelfHasMore: true,
    })
    const drawer = wrapper.get('[data-title="已下架商品"]')

    expect(drawer.text()).toContain('示例小程序')
    expect(drawer.text()).toContain('下架 1')
    await drawer.find('.hidden-products-toolbar button').trigger('click')
    await drawer.get('.hidden-products-load-more button').trigger('click')
    await drawer.get('.off-shelf-product-item button').trigger('click')

    expect(wrapper.emitted('fetch-off-shelf')).toEqual([[], [{ append: true }]])
    expect(wrapper.emitted('relist')).toEqual([[group.products[0], group]])
  })

  it('keeps loading and empty states explicit', () => {
    const loadingWrapper = mountDrawers({ hiddenVisible: true, hiddenLoading: true })
    expect(loadingWrapper.get('[data-title="已隐藏商品"] .hidden-products-loading').exists()).toBe(true)

    const emptyWrapper = mountDrawers({ offShelfVisible: true })
    expect(emptyWrapper.get('[data-title="已下架商品"] .empty-stub').text()).toContain('暂无已下架商品')
  })
})
