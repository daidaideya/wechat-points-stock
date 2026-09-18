import test from 'node:test'
import assert from 'node:assert/strict'

import { getApiErrorKind, getApiErrorMessage, isRequestCanceled } from './apiError.js'

test('normalizes string, message, and validation error payloads', () => {
  assert.equal(getApiErrorMessage({ response: { data: { detail: '密钥错误' } } }, '失败'), '密钥错误')
  assert.equal(getApiErrorMessage({ response: { data: { message: '同步失败' } } }, '失败'), '同步失败')
  assert.equal(
    getApiErrorMessage({ response: { data: { detail: [{ msg: '字段缺失' }, { message: '格式错误' }] } } }, '失败'),
    '字段缺失；格式错误',
  )
})

test('uses a fallback for unknown errors and hides cancellation messages', () => {
  assert.equal(getApiErrorMessage(new Error('network'), '网络异常'), '网络异常')
  assert.equal(getApiErrorMessage({ code: 'ERR_CANCELED' }, '网络异常'), '')
  assert.equal(isRequestCanceled({ name: 'CanceledError' }), true)
  assert.equal(isRequestCanceled({ code: 'ERR_NETWORK' }), false)
})

test('classifies transport failures and includes the backend request id', () => {
  assert.equal(getApiErrorKind({ code: 'ECONNABORTED' }), 'timeout')
  assert.equal(getApiErrorMessage({ code: 'ECONNABORTED' }, '加载失败'), '加载失败（请求超时）')
  assert.equal(getApiErrorKind({ code: 'ERR_NETWORK' }), 'network')
  assert.equal(getApiErrorMessage({ code: 'ERR_NETWORK' }, '加载失败'), '加载失败（网络不可用）')
  assert.equal(
    getApiErrorMessage(
      {
        response: {
          data: { detail: '服务异常', request_id: 'req-123' },
          headers: {},
        },
      },
      '加载失败',
    ),
    '服务异常（请求 ID: req-123）',
  )
  assert.equal(
    getApiErrorMessage(
      {
        response: {
          data: { detail: '服务异常' },
          headers: { 'X-Request-ID': 'req-header' },
        },
      },
      '加载失败',
    ),
    '服务异常（请求 ID: req-header）',
  )
})

test('treats native AbortError as a silent cancellation', () => {
  const error = new DOMException('The operation was aborted.', 'AbortError')

  assert.equal(isRequestCanceled(error), true)
  assert.equal(getApiErrorKind(error), 'canceled')
  assert.equal(getApiErrorMessage(error, '不应显示'), '')
})
