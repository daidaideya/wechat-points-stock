/* eslint-disable vue/one-component-per-file -- the test needs small isolated Element Plus stubs. */

import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ProgramFilterBar from './ProgramFilterBar.vue'

const ElementButtonStub = defineComponent({
  props: { disabled: Boolean },
  emits: ['click'],
  setup(props, { emit, slots, attrs }) {
    return () =>
      h(
        'button',
        {
          ...attrs,
          disabled: props.disabled,
          onClick: (event) => emit('click', event),
        },
        slots.default?.(),
      )
  },
})

const ElementInputStub = defineComponent({
  props: { modelValue: { type: String, default: '' } },
  emits: ['update:modelValue', 'clear', 'keyup'],
  setup(props, { emit, slots, attrs }) {
    return () =>
      h('label', { class: 'element-input-stub' }, [
        h('input', {
          ...attrs,
          value: props.modelValue,
          onInput: (event) => emit('update:modelValue', event.target.value),
          onKeyup: (event) => emit('keyup', event),
        }),
        slots.prefix?.(),
        slots.append?.(),
      ])
  },
})

const ElementIconStub = defineComponent({
  setup(_, { slots }) {
    return () => h('span', { class: 'element-icon-stub' }, slots.default?.())
  },
})

function mountFilterBar(props = {}) {
  return mount(ProgramFilterBar, {
    props: {
      availableTags: ['积分', '热门'],
      activeFilterChips: [{ key: 'status', label: '活跃' }],
      hasActiveFilters: true,
      loadedCount: 12,
      ...props,
    },
    global: {
      stubs: {
        ElButton: ElementButtonStub,
        ElIcon: ElementIconStub,
        ElInput: ElementInputStub,
      },
    },
  })
}

describe('ProgramFilterBar', () => {
  it('exposes grouped pressed state for the current filters', () => {
    const wrapper = mountFilterBar({ statusFilter: 'archived', currentTag: '热门' })

    expect(wrapper.get('[aria-label="状态筛选"] .segmented-item:nth-child(2)').attributes('aria-pressed')).toBe('true')
    expect(wrapper.get('[aria-label="状态筛选"] .segmented-item:nth-child(1)').attributes('aria-pressed')).toBe('false')
    expect(wrapper.get('[aria-label="标签筛选"] .filter-chip:nth-child(3)').attributes('aria-pressed')).toBe('true')
    expect(wrapper.get('.filter-count-chip').text()).toContain('12')
  })

  it('maps search, filter, tag, chip and reset actions to explicit events', async () => {
    const wrapper = mountFilterBar()

    await wrapper.get('input').setValue('coffee')
    await wrapper.get('.filter-search-btn').trigger('click')
    await wrapper.get('[aria-label="状态筛选"] .segmented-item:nth-child(2)').trigger('click')
    await wrapper.get('[aria-label="收藏筛选"] .segmented-item:nth-child(2)').trigger('click')
    await wrapper.get('[aria-label="青龙状态筛选"] .segmented-item:nth-child(3)').trigger('click')
    await wrapper.get('[aria-label="排序筛选"] .segmented-item:nth-child(2)').trigger('click')
    await wrapper.get('[aria-label="标签筛选"] .filter-chip:nth-child(2)').trigger('click')
    await wrapper.get('.active-filter-chip').trigger('click')
    await wrapper.get('.filter-reset-btn').trigger('click')

    expect(wrapper.emitted('update:searchKeyword')).toEqual([['coffee']])
    expect(wrapper.emitted('search')).toHaveLength(1)
    expect(wrapper.emitted('status')).toEqual([['archived']])
    expect(wrapper.emitted('favorite')).toEqual([['favorite']])
    expect(wrapper.emitted('ql-status')).toEqual([['disabled']])
    expect(wrapper.emitted('sort')).toEqual([['cron']])
    expect(wrapper.emitted('tag')).toEqual([['积分']])
    expect(wrapper.emitted('clear-chip')).toEqual([['status']])
    expect(wrapper.emitted('reset')).toHaveLength(1)
  })
})
