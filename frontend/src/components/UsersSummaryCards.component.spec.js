import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UsersSummaryCards from './UsersSummaryCards.vue'

function mountSummary(props = {}) {
  return mount(UsersSummaryCards, {
    props: {
      userCount: 27,
      totalActivePrograms: 1985,
      totalActiveApps: 61,
      usersWithPhone: 27,
      ...props,
    },
  })
}

describe('UsersSummaryCards', () => {
  it('renders the four user metrics from the parent-provided values', () => {
    const wrapper = mountSummary()

    expect(wrapper.findAll('.users-summary-card')).toHaveLength(4)
    expect(wrapper.get('.users-summary-grid').text()).toContain('用户数量27')
    expect(wrapper.get('.users-summary-grid').text()).toContain('活跃小程序总计1985')
    expect(wrapper.get('.users-summary-grid').text()).toContain('活跃 APP 总计61')
    expect(wrapper.get('.users-summary-grid').text()).toContain('已留手机号27')
  })

  it('updates the presentation when aggregate values change', async () => {
    const wrapper = mountSummary()

    await wrapper.setProps({ userCount: 0, totalActivePrograms: 0, totalActiveApps: 0, usersWithPhone: 0 })

    expect(wrapper.findAll('.users-summary-value').map((node) => node.text())).toEqual(['0', '0', '0', '0'])
  })
})
