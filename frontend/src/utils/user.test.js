import assert from 'node:assert/strict'
import test from 'node:test'

import {
  avatarChar,
  avatarColor,
  displayName,
  displayPhone,
  displayPrimaryId,
  displayWechatId,
  isPhoneLike,
} from './user.js'

test('normalizes phone and legacy WeChat identity fields', () => {
  assert.equal(isPhoneLike('13800138000'), true)
  assert.equal(isPhoneLike('wx_13800138000'), false)
  assert.equal(displayPhone({ wechat_id: '13800138000' }), '13800138000')
  assert.equal(displayWechatId({ wechat_id: '13800138000' }), '')
  assert.equal(displayPhone({ phone: ' 13900139000 ', wechat_id: 'wx_demo' }), '13900139000')
  assert.equal(displayWechatId({ phone: '13900139000', wechat_id: 'wx_demo' }), 'wx_demo')
})

test('chooses a stable display name and primary identity', () => {
  assert.equal(displayName({ nickname: '小明', wechat_id: 'wx_demo' }), '小明')
  assert.equal(displayName({ phone: '13800138000', wechat_id: 'wx_demo' }), '13800138000')
  assert.equal(displayName({}), '未命名用户')
  assert.equal(displayPrimaryId({ phone: '13800138000', wechat_id: 'wx_demo' }), '手机 13800138000')
  assert.equal(displayPrimaryId({ wechat_id: 'wx_demo' }), '微信 wx_demo')
  assert.equal(displayPrimaryId({}), '未设置账号标识')
})

test('derives deterministic avatar presentation from the identity', () => {
  const item = { nickname: '小明', wechat_id: 'wx_demo' }
  assert.equal(avatarChar(item), '小')
  assert.equal(avatarColor(item), avatarColor(item))
  assert.match(avatarColor(item), /^linear-gradient\(135deg, hsl\(/)
})
